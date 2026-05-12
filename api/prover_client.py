"""
Python subprocess wrapper for the SP1 prover CLI.

Triggers proof generation via scoring-prover-cli (Rust binary) and
returns proof metadata. Designed to be called from the FastAPI score
flow after a scoring response has been computed.

Usage::

    metadata = run_proof("octocat", activity_data)
    print(metadata["proof_id"])
    print(metadata["proving_time_ms"])
"""
import hashlib
import json
import logging
import os
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Path to the scoring-prover-cli binary (also tried via PATH lookup)
PROVER_CLI = os.environ.get(
    "SCORING_PROVER_CLI",
    "scoring-prover-cli",
)

_TEMP_DIR_PREFIX = "gh-fingerprint-proof-"


# ---------------------------------------------------------------------------
# ScoreInput builder: convert crawl activity data → ScoreInput JSON dict
# ---------------------------------------------------------------------------


def _dt_to_str(dt) -> str:
    """Convert a datetime-like object to an ISO-8601 string."""
    if hasattr(dt, "isoformat"):
        return dt.isoformat()
    return str(dt)


def _serialize_repo(repo) -> Dict[str, Any]:
    return {
        "name": repo.name,
        "full_name": repo.full_name,
        "description": repo.description,
        "language": repo.language,
        "stars": repo.stars,
        "forks": repo.forks,
        "is_fork": repo.is_fork,
        "is_private": repo.is_private,
        "pushed_at": _dt_to_str(repo.pushed_at),
    }


def _serialize_commit(commit) -> Dict[str, Any]:
    return {
        "sha": commit.sha,
        "message": commit.message,
        "author": commit.author,
        "date": _dt_to_str(commit.date),
        "additions": commit.additions,
        "deletions": commit.deletions,
    }


def _serialize_issue(issue) -> Dict[str, Any]:
    return {
        "number": issue.number,
        "title": issue.title,
        "state": issue.state,
        "created_at": _dt_to_str(issue.created_at),
        "closed_at": _dt_to_str(issue.closed_at) if issue.closed_at else None,
        "comments": issue.comments,
        "author": issue.author,
    }


def _serialize_pr(pr) -> Dict[str, Any]:
    return {
        "number": pr.number,
        "title": pr.title,
        "state": pr.state,
        "created_at": _dt_to_str(pr.created_at),
        "closed_at": _dt_to_str(pr.closed_at) if pr.closed_at else None,
        "merged_at": _dt_to_str(pr.merged_at) if pr.merged_at else None,
        "additions": pr.additions,
        "deletions": pr.deletions,
        "changed_files": pr.changed_files,
        "comments": pr.comments,
        "review_comments": pr.review_comments,
        "author": pr.author,
    }


def _serialize_readme(readme) -> Dict[str, Any]:
    return {
        "content": readme.content,
        "size_bytes": readme.size_bytes,
        "encoding": readme.encoding,
        "name": readme.name,
        "detected_sections": list(readme.detected_sections),
        "badge_count": readme.badge_count,
        "has_code_blocks": readme.has_code_blocks,
        "code_block_count": readme.code_block_count,
        "has_emoji": readme.has_emoji,
        "list_count": readme.list_count,
    }


def _serialize_cicd(cicd) -> Dict[str, Any]:
    return {
        "path": cicd.path,
        "config_type": cicd.config_type,
        "exists": cicd.exists,
        "size_bytes": cicd.size_bytes,
        "content_summary": cicd.content_summary,
    }


def _serialize_contribution(contrib) -> Optional[Dict[str, Any]]:
    if contrib is None:
        return None
    return {
        "total_contributions": contrib.total_contributions,
        "contribution_years": list(contrib.contribution_years),
        "contribution_days": [
            {
                "date": _dt_to_str(d.date),
                "contribution_count": d.contribution_count,
            }
            for d in contrib.contribution_days
        ],
        "weeks_with_contributions": contrib.weeks_with_contributions,
        "total_weeks": contrib.total_weeks,
        "first_contribution_date": (
            _dt_to_str(contrib.first_contribution_date)
            if contrib.first_contribution_date
            else None
        ),
        "longest_streak": contrib.longest_streak,
        "current_streak": contrib.current_streak,
    }


def _build_score_input(activity_data: dict) -> Dict[str, Any]:
    """Convert crawl activity_data (dataclass instances) to ScoreInput JSON dict.

    The Rust ``scoring_types::ScoreInput`` struct expects specific field
    names and types. This function maps the Python dataclass crawl output
    to that format.
    """
    return {
        "repos": [_serialize_repo(r) for r in activity_data.get("repos", [])],
        "commits": [
            _serialize_commit(c) for c in activity_data.get("commits", [])
        ],
        "issues": [
            _serialize_issue(i) for i in activity_data.get("issues", [])
        ],
        "prs": [_serialize_pr(p) for p in activity_data.get("prs", [])],
        "readmes": {
            name: _serialize_readme(rm)
            for name, rm in activity_data.get("readmes", {}).items()
        },
        "cicd_configs": {
            name: [_serialize_cicd(c) for c in cfgs]
            for name, cfgs in activity_data.get("cicd_configs", {}).items()
        },
        "contributions": _serialize_contribution(
            activity_data.get("contributions")
        ),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _generate_proof_id(username: str) -> str:
    """Generate a persistent proof_id from username + current timestamp.

    Uses SHA-256 of ``username + "|" + iso_timestamp``. The first 16 hex
    chars form a short human-readable identifier; the full hash is the
    canonical proof_id.
    """
    now = datetime.now(timezone.utc).isoformat()
    raw = f"{username}|{now}"
    full_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"proof_{full_hash[:16]}"


def run_proof(username: str, activity_data: dict, timeout: int = 600) -> dict:
    """Run proof generation for a user's scoring data.

    Builds a ``ScoreInput`` JSON from the crawl *activity_data*, invokes
    ``scoring-prover-cli`` as a subprocess, and returns proof metadata.

    Args:
        username: GitHub username (used for proof_id generation).
        activity_data: The crawl result dict from
            ``GitHubAPIClient.get_user_activity()``.
        timeout: Max seconds to wait for the prover CLI to finish
            (default 600 = 10 minutes).

    Returns:
        A metadata dict with keys:

        - ``proof_id``: persistent SHA-256-derived identifier
        - ``status``: outcome (``proof_generated``, ``proof_failed``)
        - ``proving_time_ms``: wall-clock proving time in milliseconds
        - ``proving_time_seconds``: wall-clock proving time in seconds
        - ``prover``: prover mode (``local`` or ``network``)
        - ``proof_path``: path to the generated proof file (or ``None``)
        - ``error``: error message if the CLI failed (only on failure)
        - ``input_summary``: summary of input data sizes

    Raises:
        FileNotFoundError: If the ``scoring-prover-cli`` binary cannot be
            found on the system PATH (or ``SCORING_PROVER_CLI`` points to
            a non-existent file).
        subprocess.TimeoutExpired: If the CLI does not finish within the
            given *timeout*.
    """
    proof_id = _generate_proof_id(username)

    # Build ScoreInput JSON
    score_input = _build_score_input(activity_data)

    # Summarise input for diagnostics
    input_summary = {
        "repos": len(score_input.get("repos", [])),
        "commits": len(score_input.get("commits", [])),
        "issues": len(score_input.get("issues", [])),
        "prs": len(score_input.get("prs", [])),
        "readmes": len(score_input.get("readmes", {})),
    }
    logger.info(
        "run_proof: proof_id=%s repos=%d commits=%d issues=%d prs=%d",
        proof_id,
        input_summary["repos"],
        input_summary["commits"],
        input_summary["issues"],
        input_summary["prs"],
    )

    # Write ScoreInput JSON to a temp file
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        prefix=_TEMP_DIR_PREFIX,
        delete=False,
    ) as f:
        json.dump(score_input, f, default=str)
        input_path = f.name

    try:
        start = time.monotonic()

        proc = subprocess.run(
            [PROVER_CLI, "--input", input_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        elapsed_ms = int((time.monotonic() - start) * 1000)

        if proc.returncode != 0:
            error_msg = proc.stderr.strip() or f"exit code {proc.returncode}"
            logger.error(
                "run_proof: proof_id=%s failed: %s", proof_id, error_msg
            )
            return {
                "proof_id": proof_id,
                "status": "proof_failed",
                "error": error_msg,
                "proving_time_ms": elapsed_ms,
                "proving_time_seconds": round(elapsed_ms / 1000, 2),
                "prover": os.environ.get("SP1_PROVER", "local"),
                "proof_path": None,
                "input_summary": input_summary,
            }

        # Parse CLI stdout metadata
        metadata = {}
        stdout_text = proc.stdout.strip()
        if stdout_text:
            try:
                metadata = json.loads(stdout_text)
            except json.JSONDecodeError:
                logger.warning(
                    "run_proof: proof_id=%s non-JSON stdout: %.200s",
                    proof_id,
                    stdout_text,
                )

        # Determine proof file path (default: ./proof.bin or SP1_PROOF_OUTPUT)
        proof_path = os.environ.get("SP1_PROOF_OUTPUT", "proof.bin")
        if not os.path.isfile(proof_path):
            proof_path = None

        result = {
            "proof_id": proof_id,
            "status": metadata.get("status", "proof_generated"),
            "proving_time_ms": metadata.get("proving_time_ms", elapsed_ms),
            "proving_time_seconds": metadata.get(
                "proving_time_seconds", round(elapsed_ms / 1000, 2)
            ),
            "prover": metadata.get(
                "prover", os.environ.get("SP1_PROVER", "local")
            ),
            "proof_path": proof_path,
            "input_summary": input_summary,
        }

        logger.info(
            "run_proof: proof_id=%s status=%s proving_time_ms=%d",
            proof_id,
            result["status"],
            result["proving_time_ms"],
        )
        return result

    except FileNotFoundError:
        logger.error(
            "run_proof: CLI binary not found '%s'. "
            "Set SCORING_PROVER_CLI env var or build the binary.",
            PROVER_CLI,
        )
        raise

    except subprocess.TimeoutExpired:
        logger.error(
            "run_proof: proof_id=%s timed out after %ds", proof_id, timeout
        )
        raise

    finally:
        # Clean up temp input file
        try:
            os.unlink(input_path)
        except OSError:
            pass
