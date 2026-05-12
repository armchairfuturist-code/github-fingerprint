"""
Scoring Module
Calculates weighted scores from extracted signals, generates risk flags,
and supports role-adaptive scoring profiles.
"""

from scoring.engine import ScoringEngine, ScoreResult
from scoring.profiles import (
    RoleProfile,
    get_profile,
    list_profiles,
    resolve_role_profile,
)

__all__ = [
    "ScoringEngine",
    "ScoreResult",
    "RoleProfile",
    "get_profile",
    "list_profiles",
    "resolve_role_profile",
]
