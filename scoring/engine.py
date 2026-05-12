"""
Scoring Engine
Calculates weighted scores from extracted signals and generates risk flags.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from signals.extractor import SignalResult
from scoring.profiles import resolve_role_profile


@dataclass
class ScoreResult:
    """Result of scoring calculation."""
    overall_score: float
    signal_scores: Dict[str, SignalResult]
    risk_flags: List[str]
    details: Dict[str, Any]


class ScoringEngine:
    """Calculates overall score from signals and generates risk flags."""

    def __init__(
        self,
        weights: Dict[str, float] = None,
        profile: Optional[str] = None,
    ):
        """
        Initialize scoring engine with signal weights.

        Args:
            weights: Dictionary of signal names to weights.
                     If None, uses default weights from plan (unless profile given).
            profile: Optional role profile name (e.g. 'engineering', 'marketing').
                     When provided without explicit weights, overrides defaults.
        """
        self._profile_name: str = "legacy"
        self._last_signals_below: List[str] = []
        self._last_active_signals: List[str] = []

        if weights is not None:
            # Explicit weights: no profile, no thresholds
            self.weights = dict(weights)
            self.confidence_thresholds: Dict[str, float] = {}
        elif profile is not None:
            # Profile-based: load weights and thresholds from profile
            loaded = (
                resolve_role_profile(profile)
                if isinstance(profile, str)
                else profile
            )
            self.weights = dict(loaded.weights)
            self.confidence_thresholds = dict(loaded.confidence_thresholds)
            self._profile_name = loaded.name
        else:
            # Legacy default weights (backward compatible with pre-S02)
            self.weights = {
                "commit_consistency": 0.10,
                "language_diversity": 0.07,
                "issue_engagement": 0.10,
                "pr_patterns": 0.10,
                "project_ownership": 0.07,
                "review_patterns": 0.07,
                "response_time": 0.10,
                "readme_quality": 0.08,
                "commit_semantics": 0.08,
                "cicd_maturity": 0.07,
                "contribution_consistency": 0.08,
                "ai_usage_patterns": 0.08,
            }
            self.confidence_thresholds: Dict[str, float] = {}

    def set_role(self, profile_name: str) -> None:
        """
        Load a named role profile and update weights and confidence thresholds.

        Args:
            profile_name: The machine key of the profile to load
                          (e.g. 'engineering', 'marketing', 'non-technical').

        Raises:
            ValueError: If the profile name is not recognized.
        """
        profile = resolve_role_profile(profile_name)
        self.weights = dict(profile.weights)
        self.confidence_thresholds = dict(profile.confidence_thresholds)
        self._profile_name = profile.name

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _filter_by_confidence(
        self, signal_results: Dict[str, SignalResult]
    ) -> tuple:
        """
        Filter signals whose confidence is below their configured threshold.

        When no thresholds are set (empty dict), all signals pass through
        unchanged, preserving original behavior.

        Returns:
            Tuple of (active_signals_dict, below_threshold_names_list).
        """
        active: Dict[str, SignalResult] = {}
        below: List[str] = []

        for signal_name, result in signal_results.items():
            if signal_name not in self.weights:
                continue
            threshold = self.confidence_thresholds.get(signal_name)
            if threshold is not None and result.confidence < threshold:
                below.append(signal_name)
            else:
                active[signal_name] = result

        return active, below

    # ------------------------------------------------------------------
    # Public scoring methods
    # ------------------------------------------------------------------

    def calculate_overall_score(
        self, signal_results: Dict[str, SignalResult]
    ) -> float:
        """
        Calculate weighted overall score from signal results.

        Applies confidence threshold filtering: signals whose confidence
        is below the profile's per-signal threshold are excluded, and
        their weight is redistributed proportionally among remaining
        active signals.

        When no confidence thresholds are set (legacy mode), all signals
        contribute with their original weights, preserving pre-S02 behavior.

        Returns:
            Float score in [0, 100].
        """
        active, below = self._filter_by_confidence(signal_results)

        self._last_signals_below = below
        self._last_active_signals = list(active.keys())

        if not active:
            return 0.0

        # Sum of original weights for active (non-filtered) signals.
        # This redistributes excluded signals' weight proportionally:
        #   effective_weight = original_weight / sum_of_active_weights
        original_weight_sum = sum(
            self.weights.get(s, 0) for s in active
        )

        if original_weight_sum == 0:
            return 0.0

        weighted_sum = 0.0
        for signal_name, result in active.items():
            weight = self.weights.get(signal_name, 0)
            weighted_sum += result.score * weight

        return weighted_sum / original_weight_sum

    def generate_risk_flags(
        self,
        signal_results: Dict[str, SignalResult],
        signals_below_threshold: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Generate risk flags based on low scores, low confidence,
        and confidence threshold violations.

        Args:
            signal_results: Dict of signal names to SignalResult.
            signals_below_threshold: Optional list of signal names that
                fell below their confidence threshold. If None, uses the
                last computed list from calculate_overall_score().

        Returns:
            List of human-readable risk flag strings.
        """
        risk_flags = []
        if signals_below_threshold is None:
            signals_below_threshold = self._last_signals_below

        for signal_name, result in signal_results.items():
            if result.score < 30 and result.confidence > 0.5:
                risk_flags.append(
                    f"Low {signal_name.replace('_', ' ')} score"
                )

            if result.confidence < 0.3:
                risk_flags.append(
                    f"Low confidence in {signal_name.replace('_', ' ')}"
                )

        # Profile-specific confidence threshold violations
        for signal_name in signals_below_threshold:
            risk_flags.append(
                f"Insufficient confidence in {signal_name} "
                f"for {self._profile_name} profile"
            )

        return risk_flags

    def score_user(
        self,
        activity_data: Dict[str, Any],
        role: Optional[str] = None,
    ) -> ScoreResult:
        """
        Score a user based on their GitHub activity data.

        Args:
            activity_data: GitHub activity data dict with keys
                           'repos', 'commits', 'issues', 'prs'.
            role: Optional role profile name. When provided,
                  switches the engine to that profile before scoring.
                  When None, uses current engine configuration
                  (backward compatible with pre-S02 callers).

        Returns:
            ScoreResult with overall_score, signal_scores, risk_flags,
            and details (including profile_name, signals_below_threshold,
            signals_scored).
        """
        from signals.extractor import SignalExtractor

        if role is not None:
            self.set_role(role)

        extractor = SignalExtractor()
        signal_results = extractor.extract_all_signals(activity_data)

        overall_score = self.calculate_overall_score(signal_results)
        risk_flags = self.generate_risk_flags(
            signal_results, self._last_signals_below
        )

        details = {
            "total_repos": len(activity_data.get("repos", [])),
            "total_commits": len(activity_data.get("commits", [])),
            "total_issues": len(activity_data.get("issues", [])),
            "total_prs": len(activity_data.get("prs", [])),
            "profile_name": self._profile_name,
            "signals_below_threshold": list(self._last_signals_below),
            "signals_scored": len(self._last_active_signals),
        }

        return ScoreResult(
            overall_score=overall_score,
            signal_scores=signal_results,
            risk_flags=risk_flags,
            details=details,
        )


if __name__ == "__main__":
    # Test the scoring engine with mock data
    from signals.extractor import SignalResult

    # Mock signal results
    mock_signals = {
        "commit_consistency": SignalResult("commit_consistency", 85, 0.8, {}),
        "language_diversity": SignalResult("language_diversity", 70, 0.7, {}),
        "issue_engagement": SignalResult("issue_engagement", 60, 0.6, {}),
        "pr_patterns": SignalResult("pr_patterns", 75, 0.75, {}),
        "project_ownership": SignalResult("project_ownership", 80, 0.8, {}),
        "review_patterns": SignalResult("review_patterns", 65, 0.65, {}),
        "response_time": SignalResult("response_time", 90, 0.9, {}),
        "readme_quality": SignalResult("readme_quality", 55, 0.55, {}),
    }

    engine = ScoringEngine()
    overall = engine.calculate_overall_score(mock_signals)
    print(f"Overall score: {overall:.2f}")

    risk_flags = engine.generate_risk_flags(mock_signals)
    print(f"Risk flags: {risk_flags}")

    # Demonstrate role switching
    engine.set_role("marketing")
    overall_mkt = engine.calculate_overall_score(mock_signals)
    print(f"Marketing overall score: {overall_mkt:.2f}")
