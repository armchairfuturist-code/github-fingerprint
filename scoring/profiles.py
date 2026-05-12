"""
Role-Adaptive Scoring Profiles
Defines role-specific signal weight distributions and confidence thresholds
for the scoring engine.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

ALL_SIGNALS = [
    "commit_consistency",
    "pr_patterns",
    "commit_semantics",
    "cicd_maturity",
    "language_diversity",
    "response_time",
    "review_patterns",
    "issue_engagement",
    "readme_quality",
    "project_ownership",
    "contribution_consistency",
    "ai_usage_patterns",
]

# Signal categorization for threshold assignment
TECH_SIGNALS = {
    "commit_consistency",
    "pr_patterns",
    "commit_semantics",
    "cicd_maturity",
    "language_diversity",
    "review_patterns",
    "ai_usage_patterns",
}
PROCESS_SIGNALS = {
    "response_time",
    "issue_engagement",
    "readme_quality",
    "project_ownership",
    "contribution_consistency",
}
COMMS_SIGNALS = {
    "readme_quality",
    "project_ownership",
    "issue_engagement",
    "response_time",
    "review_patterns",
    "contribution_consistency",
}
CODE_SIGNALS = {
    "commit_semantics",
    "pr_patterns",
    "language_diversity",
    "commit_consistency",
    "cicd_maturity",
    "ai_usage_patterns",
}
PROJECT_SIGNALS = {
    "project_ownership",
    "issue_engagement",
    "review_patterns",
    "readme_quality",
    "response_time",
    "contribution_consistency",
}


@dataclass
class RoleProfile:
    """A role-specific scoring profile with signal weights and confidence thresholds.

    Attributes:
        name: Machine key identifying the profile (e.g. 'engineering').
        display_name: Human-readable label (e.g. 'Engineering').
        description: Short description of when to use this profile.
        weights: Signal name -> weight mapping. Must sum to 1.0 (within 0.001).
        confidence_thresholds: Signal name -> minimum confidence [0.0-1.0].
    """
    name: str
    display_name: str
    description: str
    weights: Dict[str, float] = field(default_factory=dict)
    confidence_thresholds: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate profile constraints after initialization."""
        self._validate_signal_keys()
        self._validate_weights_sum()
        self._validate_thresholds()

    def _validate_signal_keys(self) -> None:
        """Ensure all 12 signal names are present in both weights and thresholds."""
        missing_weights = [s for s in ALL_SIGNALS if s not in self.weights]
        if missing_weights:
            raise ValueError(
                f"Profile '{self.name}' missing weights for: {missing_weights}"
            )
        missing_thresholds = [
            s for s in ALL_SIGNALS if s not in self.confidence_thresholds
        ]
        if missing_thresholds:
            raise ValueError(
                f"Profile '{self.name}' missing thresholds for: {missing_thresholds}"
            )

    def _validate_weights_sum(self) -> None:
        """Validate that weights sum to approximately 1.0."""
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"Profile '{self.name}' weights sum to {total:.4f}, "
                f"expected ~1.0"
            )

    def _validate_thresholds(self) -> None:
        """Validate confidence thresholds are in [0.0, 1.0]."""
        for signal, threshold in self.confidence_thresholds.items():
            if not 0.0 <= threshold <= 1.0:
                raise ValueError(
                    f"Profile '{self.name}' threshold for '{signal}' "
                    f"is {threshold}, expected [0.0, 1.0]"
                )


def _build_profile(
    name: str,
    display_name: str,
    description: str,
    weights: Dict[str, float],
    thresholds: Dict[str, float],
) -> RoleProfile:
    """Build a validated RoleProfile.

    Ensures all 12 signals are present in both weights and thresholds,
    filling any missing entries with sensible defaults during construction.
    """
    full_weights: Dict[str, float] = {}
    full_thresholds: Dict[str, float] = {}
    for signal in ALL_SIGNALS:
        full_weights[signal] = weights.get(signal, 0.0)
        full_thresholds[signal] = thresholds.get(signal, 0.3)
    return RoleProfile(
        name=name,
        display_name=display_name,
        description=description,
        weights=full_weights,
        confidence_thresholds=full_thresholds,
    )


# ---------------------------------------------------------------------------
# Built-in profiles
# ---------------------------------------------------------------------------

ENGINEERING_PROFILE = _build_profile(
    name="engineering",
    display_name="Engineering",
    description=(
        "Default profile for software engineering roles. "
        "Emphasizes technical signals: commit patterns, code review quality, "
        "and CI/CD maturity. Backward-compatible with existing scoring defaults."
    ),
    weights={
        "commit_consistency": 0.12,
        "pr_patterns": 0.12,
        "commit_semantics": 0.10,
        "cicd_maturity": 0.10,
        "language_diversity": 0.08,
        "response_time": 0.08,
        "review_patterns": 0.08,
        "issue_engagement": 0.08,
        "readme_quality": 0.06,
        "project_ownership": 0.06,
        "contribution_consistency": 0.06,
        "ai_usage_patterns": 0.06,
    },
    thresholds={
        signal: 0.4 if signal in TECH_SIGNALS else 0.3
        for signal in ALL_SIGNALS
    },
)

MARKETING_PROFILE = _build_profile(
    name="marketing",
    display_name="Marketing",
    description=(
        "Profile for marketing and community-focused roles. "
        "Prioritizes communication-signal proxies: README quality, "
        "issue engagement, and project ownership. De-emphasizes "
        "low-level code metrics."
    ),
    weights={
        "readme_quality": 0.20,
        "project_ownership": 0.15,
        "issue_engagement": 0.15,
        "review_patterns": 0.10,
        "commit_semantics": 0.08,
        "response_time": 0.08,
        "pr_patterns": 0.06,
        "language_diversity": 0.06,
        "commit_consistency": 0.04,
        "cicd_maturity": 0.04,
        "contribution_consistency": 0.02,
        "ai_usage_patterns": 0.02,
    },
    thresholds={
        signal: 0.3 if signal in COMMS_SIGNALS else 0.2
        for signal in ALL_SIGNALS
    },
)

NON_TECHNICAL_PROFILE = _build_profile(
    name="non-technical",
    display_name="Non-Technical",
    description=(
        "Profile for non-technical roles (design, product, management). "
        "Focuses on project-level signals: ownership breadth, issue "
        "stewardship, and cross-repo presence. Code-level signals "
        "receive minimal weight."
    ),
    weights={
        "project_ownership": 0.20,
        "issue_engagement": 0.20,
        "review_patterns": 0.12,
        "readme_quality": 0.10,
        "response_time": 0.08,
        "pr_patterns": 0.08,
        "language_diversity": 0.06,
        "commit_semantics": 0.04,
        "commit_consistency": 0.04,
        "cicd_maturity": 0.03,
        "contribution_consistency": 0.03,
        "ai_usage_patterns": 0.02,
    },
    thresholds={
        signal: 0.25 if signal in PROJECT_SIGNALS else 0.1
        for signal in ALL_SIGNALS
    },
)

# Registration: first entry is the default for backward compatibility
_BUILTIN_PROFILES: List[RoleProfile] = [
    ENGINEERING_PROFILE,
    MARKETING_PROFILE,
    NON_TECHNICAL_PROFILE,
]

_PROFILES_BY_NAME: Dict[str, RoleProfile] = {
    p.name: p for p in _BUILTIN_PROFILES
}


def get_profile(name: str) -> RoleProfile:
    """Retrieve a built-in profile by its machine key.

    Args:
        name: Profile name (e.g. 'engineering', 'marketing', 'non-technical').

    Returns:
        The matching RoleProfile.

    Raises:
        ValueError: If no profile with the given name exists.
    """
    if name not in _PROFILES_BY_NAME:
        valid = ", ".join(sorted(_PROFILES_BY_NAME))
        raise ValueError(
            f"Unknown profile '{name}'. Valid profiles: {valid}"
        )
    return _PROFILES_BY_NAME[name]


def list_profiles() -> List[RoleProfile]:
    """Return all built-in role profiles.

    Returns:
        A list of available RoleProfile instances.
    """
    return list(_BUILTIN_PROFILES)


def resolve_role_profile(role: Optional[str] = None) -> RoleProfile:
    """Resolve a role string to a profile, defaulting to engineering.

    Args:
        role: Optional role name. When None, returns the engineering profile
              for backward compatibility with existing scoring calls.

    Returns:
        The resolved RoleProfile.
    """
    if role is None:
        return ENGINEERING_PROFILE
    return get_profile(role)
