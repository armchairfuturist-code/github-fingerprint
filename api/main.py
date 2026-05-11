"""
FastAPI REST endpoint for GitHub fingerprint scoring.
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

from crawler.github_api import GitHubAPIClient
from scoring.engine import ScoringEngine

load_dotenv()

app = FastAPI(title="GitHub Fingerprint API", version="0.1.0")

# Initialize components
github_token = os.getenv("GITHUB_TOKEN")
if not github_token:
    raise ValueError("GITHUB_TOKEN environment variable is required")

github_client = GitHubAPIClient(github_token)
scoring_engine = ScoringEngine()


class ScoreRequest(BaseModel):
    username: str
    weights: Optional[Dict[str, float]] = None


class ScoreResponse(BaseModel):
    username: str
    overall_score: float
    signal_scores: Dict[str, Dict[str, Any]]
    risk_flags: list[str]
    details: Dict[str, Any]


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "github-fingerprint-api"}


@app.post("/score", response_model=ScoreResponse)
async def score_user(request: ScoreRequest):
    """
    Score a GitHub user based on their activity.
    
    Args:
        request: ScoreRequest with username and optional weights
        
    Returns:
        ScoreResponse with overall score, signal scores, risk flags, and details
    """
    try:
        activity_data = github_client.get_user_activity(request.username)
        
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
        
        return ScoreResponse(
            username=request.username,
            overall_score=score_result.overall_score,
            signal_scores=signal_scores,
            risk_flags=score_result.risk_flags,
            details=score_result.details,
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scoring user: {str(e)}")


@app.get("/score/{username}")
async def score_user_get(
    username: str,
    weights: Optional[str] = Query(None, description="JSON string of weights")
):
    """
    Score a GitHub user via GET request.
    
    Args:
        username: GitHub username
        weights: Optional JSON string of weights (e.g., '{"commit_consistency": 0.2}')
        
    Returns:
        ScoreResponse with overall score, signal scores, risk flags, and details
    """
    try:
        # Parse weights if provided
        weights_dict = None
        if weights:
            import json
            weights_dict = json.loads(weights)
        
        request = ScoreRequest(username=username, weights=weights_dict)
        return await score_user(request)
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid weights JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


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


def _extract_role_keywords(role_description: str) -> dict:
    """Extract keywords from role description for simple matching."""
    # Simple keyword mapping for MVP
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
    matched_signals = {}
    
    for keyword, signals in keyword_map.items():
        if keyword in role_lower:
            for sig in signals:
                matched_signals[sig] = matched_signals.get(sig, 0) + 1
    
    return matched_signals


@app.post("/match", response_model=MatchResponse)
async def match_user(request: MatchRequest):
    """
    Match a GitHub user to a role based on their activity and role description.
    
    Args:
        request: MatchRequest with username and role description
        
    Returns:
        MatchResponse with match score and top reasons
    """
    try:
        # Get user activity
        activity_data = github_client.get_user_activity(request.username)
        
        # Score the user
        score_result = scoring_engine.score_user(activity_data)
        
        # Extract keywords from role
        role_keywords = _extract_role_keywords(request.role_description)
        
        # Calculate match score (simple MVP version)
        # Boost signals that match role keywords
        match_score = score_result.overall_score
        top_reasons = []
        
        if role_keywords:
            # Weight the score based on matched signals
            keyword_boost = 0
            for sig, weight in role_keywords.items():
                if sig in score_result.signal_scores:
                    sig_score = score_result.signal_scores[sig].score
                    keyword_boost += (sig_score * weight * 0.1)
            
            match_score = min(100, match_score + keyword_boost)
        
        # Generate top reasons
        signal_scores = score_result.signal_scores
        sorted_signals = sorted(
            signal_scores.items(), 
            key=lambda x: x[1].score, 
            reverse=True
        )
        
        for sig_name, result in sorted_signals[:3]:
            reason = f"{sig_name.replace('_', ' ').title()}: {result.score:.0f}/100"
            top_reasons.append(reason)
        
        # Add keyword match reasons
        if role_keywords:
            top_reasons.append(f"Matched {len(role_keywords)} role keywords")
        
        return MatchResponse(
            username=request.username,
            role=request.role_description[:100],  # Truncate for display
            match_score=round(match_score, 1),
            top_reasons=top_reasons,
            signal_overview={
                "overall": round(score_result.overall_score, 1),
                "details": score_result.details,
            },
        )
    
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)