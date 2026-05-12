"""
FastAPI REST endpoint for GitHub fingerprint scoring.
"""
import logging
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import json
from dotenv import load_dotenv

try:
    from .prover_client import run_proof, _generate_proof_id  # package import
except ImportError:
    from prover_client import run_proof, _generate_proof_id  # direct execution
from attest import sign_score, load_or_generate_signing_key, verify_attestation
from crawler.github_api import GitHubAPIClient
from scoring.engine import ScoringEngine
from scoring.profiles import list_profiles, resolve_role_profile, get_profile

logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI(title="GitHub Fingerprint API", version="0.1.0")

# Lazy initialization for GITHUB_TOKEN-based client
_github_client_instance = None


def _get_github_client() -> GitHubAPIClient:
    """Lazily initialize and return the GitHub API client.

    Validates GITHUB_TOKEN on first use, not at module import time,
    so that tests and other dependents can import the module without
    the environment variable set.
    """
    global _github_client_instance
    if _github_client_instance is None:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        logger.info("Initializing GitHub API client")
        _github_client_instance = GitHubAPIClient(token)
    return _github_client_instance
scoring_engine = ScoringEngine()

# Attestation: load (or generate) signing key at startup.
# If the key is unavailable, attestation is omitted from responses — no crash.
try:
    _signing_key, verify_key_bytes = load_or_generate_signing_key()
except Exception:
    logger.warning("Failed to initialize attestation signing key. Attestation will be omitted.", exc_info=True)
    _signing_key = None
    verify_key_bytes = None


class ScoreRequest(BaseModel):
    username: str
    weights: Optional[Dict[str, float]] = None
    role: Optional[str] = None


class ScoreResponse(BaseModel):
    username: str
    overall_score: float
    signal_scores: Dict[str, Dict[str, Any]]
    risk_flags: list[str]
    details: Dict[str, Any]
    profile: str
    attestation: Optional[Dict[str, Any]] = None
    proof_id: Optional[str] = None


class MatchRequest(BaseModel):
    username: str
    role_description: str
    required_skills: Optional[list[str]] = None


class MatchResponse(BaseModel):
    username: str
    role: str
    match_score: float
    top_reasons: list[str]
    signal_overview: Dict[str, Any]
    attestation: Optional[Dict[str, Any]] = None


class ProfileResponse(BaseModel):
    name: str
    display_name: str
    description: str
    weights: Dict[str, float]


class ProfilesListResponse(BaseModel):
    profiles: List[ProfileResponse]


class VerifyRequest(BaseModel):
    signed_payload: str
    signature: str
    public_key: str


class VerifyResponse(BaseModel):
    valid: bool
    payload: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "github-fingerprint-api"}


@app.post("/score", response_model=ScoreResponse)
async def score_user(request: ScoreRequest, background_tasks: BackgroundTasks):
    """
    Score a GitHub user based on their activity.

    After computing the score, enqueues proof generation as a background task.
    The response includes a ``proof_id`` that identifies the proof run.

    Args:
        request: ScoreRequest with username, optional weights, and optional role
        background_tasks: FastAPI BackgroundTasks for async proof generation

    Returns:
        ScoreResponse with overall score, signal scores, risk flags, details,
        profile, attestation, and proof_id.
    """
    try:
        activity_data = _get_github_client().get_user_activity(request.username)

        # Apply role profile if specified (must happen before custom weights)
        if request.role:
            try:
                resolve_role_profile(request.role)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            scoring_engine.set_role(request.role)

        # Apply custom weights (overrides profile or default weights)
        if request.weights:
            scoring_engine.weights = request.weights

        score_result = scoring_engine.score_user(activity_data)

        signal_scores = {}
        for signal_name, signal_result in score_result.signal_scores.items():
            signal_scores[signal_name] = {
                "score": signal_result.score,
                "confidence": signal_result.confidence,
                "details": signal_result.details,
            }

        profile_name = score_result.details.get("profile_name", "legacy")

        attestation_block = _build_attestation(
            username=request.username,
            overall_score=score_result.overall_score,
            signal_scores=signal_scores,
            risk_flags=score_result.risk_flags,
            profile_name=profile_name,
        )

        # Generate proof_id and enqueue proof generation as background task
        proof_id = _generate_proof_id(request.username)

        def _fire_proof():
            """Background wrapper that logs outcome without crashing the response."""
            try:
                result = run_proof(request.username, activity_data)
                logger.info(
                    "proof_id=%s status=%s proving_time_ms=%d",
                    proof_id,
                    result.get("status"),
                    result.get("proving_time_ms", 0),
                )
            except Exception:
                logger.exception(
                    "proof_id=%s background proof generation failed",
                    proof_id,
                )

        background_tasks.add_task(_fire_proof)

        return ScoreResponse(
            username=request.username,
            overall_score=score_result.overall_score,
            signal_scores=signal_scores,
            risk_flags=score_result.risk_flags,
            details=score_result.details,
            profile=profile_name,
            attestation=attestation_block,
            proof_id=proof_id,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scoring user: {str(e)}")


@app.get("/score/{username}")
async def score_user_get(
    username: str,
    weights: Optional[str] = Query(None, description="JSON string of weights"),
    role: Optional[str] = Query(None, description="Role profile name (engineering, marketing, non-technical)"),
):
    """
    Score a GitHub user via GET request.

    Args:
        username: GitHub username
        weights: Optional JSON string of weights (e.g., '{"commit_consistency": 0.2}')
        role: Optional role profile name

    Returns:
        ScoreResponse with overall score, signal scores, risk flags, details, and profile
    """
    try:
        # Parse weights if provided
        weights_dict = None
        if weights:
            weights_dict = json.loads(weights)

        request = ScoreRequest(username=username, weights=weights_dict, role=role)
        return await score_user(request, BackgroundTasks())

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid weights JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


def _build_attestation(
    username: str,
    overall_score: float,
    signal_scores: Dict[str, Dict[str, Any]],
    risk_flags: List[str],
    profile_name: str,
) -> Optional[Dict[str, Any]]:
    """
    Build an attestation block for a score response.

    Returns None if the signing key is unavailable (attestation silently
    omitted). Logs a warning on first failure so operators can detect
    missing key configuration.
    """
    global _signing_key
    if _signing_key is None:
        logger.warning(
            "Signing key not available — attestation omitted for user=%s",
            username,
        )
        return None
    try:
        attestation = sign_score(
            username=username,
            overall_score=overall_score,
            signal_scores=signal_scores,
            risk_flags=risk_flags,
            profile_name=profile_name,
            private_key=_signing_key,
        )
        logger.info(
            "Attested score for user=%s overall=%.1f sig_prefix=%s",
            username,
            overall_score,
            attestation.get("signature", "?")[:12],
        )
        return attestation
    except Exception:
        logger.exception(
            "Failed to produce attestation for user=%s", username
        )
        return None

def _extract_role_keywords(role_description: str) -> Dict[str, int]:
    """Extract keywords from role description for simple matching.

    Used as a fallback when no profile name matches the role description.
    Maps keyword patterns to signal names with boost counts.
    """
    keyword_map = {
        "backend": ["language_diversity", "issue_engagement"],
        "frontend": ["readme_quality", "pr_patterns"],
        "fullstack": ["language_diversity", "project_ownership"],
        "devops": ["commit_consistency", "response_time"],
        "data": ["language_diversity", "issue_engagement"],
        "machine learning": ["language_diversity", "project_ownership"],
        "ml": ["language_diversity", "project_ownership"],
        "api": ["issue_engagement", "pr_patterns"],
        "database": ["language_diversity", "issue_engagement"],
        "testing": ["pr_patterns", "review_patterns"],
        "security": ["commit_consistency", "response_time"],
        "performance": ["commit_consistency", "issue_engagement"],
        "scale": ["commit_consistency", "project_ownership"],
        "debug": ["response_time", "issue_engagement"],
    }

    role_lower = role_description.lower()
    matched_signals: Dict[str, int] = {}

    for keyword, signals in keyword_map.items():
        if keyword in role_lower:
            for sig in signals:
                matched_signals[sig] = matched_signals.get(sig, 0) + 1

    return matched_signals


def _resolve_role_for_matching(role_description: str) -> tuple:
    """Resolve a free-form role description to a profile name and keyword boosts.

    First tries substring matching against profile names and display names.
    Falls back to engineering profile with keyword-based signal boosting.

    Returns:
        Tuple of (profile_name_or_None, keyword_boosts_dict).
        When a named profile matches, keyword_boosts is empty.
        When no profile matches, profile_name is None and keyword_boosts
        contains the fallback keyword map.
    """
    role_lower = role_description.lower()

    # Try direct profile name/display_name matching
    for profile in list_profiles():
        if profile.name.lower() in role_lower:
            return profile.name, {}
        if profile.display_name.lower() in role_lower:
            return profile.name, {}

    # Try description keyword matching against profile descriptions
    # Check if common engineering/marketing/non-technical terms appear
    engineering_terms = {"software", "engineer", "developer", "programmer", "code", "build", "architect", "dev"}
    marketing_terms = {"market", "growth", "community", "content", "social", "brand", "product marketing"}
    non_technical_terms = {"design", "product", "manager", "designer", "pm", "ux", "research", "analyst"}

    role_words = set(role_lower.split())

    eng_score = len(role_words & engineering_terms)
    mkt_score = len(role_words & marketing_terms)
    nt_score = len(role_words & non_technical_terms)

    if eng_score > mkt_score and eng_score > nt_score:
        return "engineering", {}
    if mkt_score > eng_score and mkt_score > nt_score:
        return "marketing", {}
    if nt_score > eng_score and nt_score > mkt_score:
        return "non-technical", {}

    # Fall back to engineering with keyword boosts
    return None, _extract_role_keywords(role_description)


@app.post("/match", response_model=MatchResponse)
async def match_user(request: MatchRequest):
    """
    Match a GitHub user to a role based on their activity and role description.

    Uses role profile matching: when the description matches a known profile
    (engineering, marketing, non-technical), that profile is used for scoring.
    Otherwise falls back to keyword-based signal boosting.

    Args:
        request: MatchRequest with username and role description

    Returns:
        MatchResponse with match score and top reasons
    """
    try:
        activity_data = _get_github_client().get_user_activity(request.username)

        # Resolve role description to a profile
        profile_name, keyword_boosts = _resolve_role_for_matching(request.role_description)

        # If a named profile was matched, use it for scoring
        if profile_name is not None:
            scoring_engine.set_role(profile_name)

        score_result = scoring_engine.score_user(activity_data)

        # Calculate match score based on profile or keyword boosts
        match_score = score_result.overall_score
        top_reasons = []
        matched_signals = set()

        if profile_name is not None:
            # Profile-based scoring: use profile-aware reasons
            profile = get_profile(profile_name)
            top_reasons.append(f"Role matched to {profile.display_name} profile")
            top_reasons.append(
                f"Overall fit: {score_result.overall_score:.0f}/100"
            )

            # Add top signal reasons for this profile
            signal_scores = score_result.signal_scores
            sorted_signals = sorted(
                signal_scores.items(),
                key=lambda x: x[1].score,
                reverse=True,
            )
            for sig_name, result in sorted_signals[:3]:
                reason = (
                    f"{sig_name.replace('_', ' ').title()}: "
                    f"{result.score:.0f}/100"
                )
                top_reasons.append(reason)
                matched_signals.add(sig_name)

            # Apply profile weight redistribution for match score refinement
            profile_weights = profile.weights
            profile_weighted_score = 0.0
            for sig_name, result in signal_scores.items():
                weight = profile_weights.get(sig_name, 0)
                profile_weighted_score += result.score * weight
            match_score = round(profile_weighted_score, 1)

        elif keyword_boosts:
            # Fallback: keyword-based signal boosting
            keyword_boost = 0
            for sig, weight in keyword_boosts.items():
                if sig in score_result.signal_scores:
                    sig_score = score_result.signal_scores[sig].score
                    keyword_boost += sig_score * weight * 0.1

            match_score = min(100, match_score + keyword_boost)

            signal_scores = score_result.signal_scores
            sorted_signals = sorted(
                signal_scores.items(),
                key=lambda x: x[1].score,
                reverse=True,
            )
            for sig_name, result in sorted_signals[:3]:
                reason = (
                    f"{sig_name.replace('_', ' ').title()}: "
                    f"{result.score:.0f}/100"
                )
                top_reasons.append(reason)
                matched_signals.add(sig_name)

            top_reasons.append(f"Matched {len(keyword_boosts)} role keywords")

        else:
            # No profile match, no keywords — generic scoring
            signal_scores = score_result.signal_scores
            sorted_signals = sorted(
                signal_scores.items(),
                key=lambda x: x[1].score,
                reverse=True,
            )
            for sig_name, result in sorted_signals[:3]:
                reason = (
                    f"{sig_name.replace('_', ' ').title()}: "
                    f"{result.score:.0f}/100"
                )
                top_reasons.append(reason)

        # Build signal_scores dict for attestation (normalize SignalResult → dict)
        raw_signal_scores = score_result.signal_scores
        signal_scores_for_attest: Dict[str, Dict[str, Any]] = {}
        for name, result in raw_signal_scores.items():
            signal_scores_for_attest[name] = {
                "score": result.score,
                "confidence": result.confidence,
                "details": result.details,
            }

        profile_name = score_result.details.get("profile_name", "legacy")
        attestation_block = _build_attestation(
            username=request.username,
            overall_score=score_result.overall_score,
            signal_scores=signal_scores_for_attest,
            risk_flags=score_result.risk_flags,
            profile_name=profile_name,
        )

        return MatchResponse(
            username=request.username,
            role=request.role_description[:100],
            match_score=round(match_score, 1),
            top_reasons=top_reasons,
            signal_overview={
                "overall": round(score_result.overall_score, 1),
                "details": score_result.details,
            },
            attestation=attestation_block,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error matching user: {str(e)}")


@app.get("/match/{username}")
async def match_user_get(
    username: str,
    role: str = Query(..., description="Role description")
):
    """
    Match a GitHub user to a role via GET request.
    """
    try:
        request = MatchRequest(username=username, role_description=role)
        return await match_user(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/profiles", response_model=ProfilesListResponse)
async def list_available_profiles():
    """
    List all available role profiles for scoring.

    Returns:
        ProfilesListResponse with name, display_name, description, and weights
        for each available profile.
    """
    profiles = list_profiles()
    profile_responses = [
        ProfileResponse(
            name=p.name,
            display_name=p.display_name,
            description=p.description,
            weights=p.weights,
        )
        for p in profiles
    ]
    return ProfilesListResponse(profiles=profile_responses)


@app.post("/verify", response_model=VerifyResponse)
async def verify_attestation_endpoint(request: VerifyRequest):
    """
    Verify an Ed25519 attestation signature.

    Accepts a signed payload, its signature, and the public key used to sign it.
    Returns whether the signature is valid and the parsed payload.

    Args:
        request: VerifyRequest with signed_payload, signature, and public_key.

    Returns:
        VerifyResponse with valid flag and optional parsed payload or error message.
    """
    try:
        result = verify_attestation(
            signed_payload=request.signed_payload,
            signature=request.signature,
            public_key=request.public_key,
        )
        # Map the signer result dict to our response model
        return VerifyResponse(
            valid=result.get("valid", False),
            payload=result.get("payload"),
            error=result.get("error"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid verification input: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)