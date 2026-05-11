"""
Scoring Engine
Calculates weighted scores from extracted signals and generates risk flags.
"""
from typing import Dict, List, Any
from dataclasses import dataclass
from signals.extractor import SignalResult


@dataclass
class ScoreResult:
    """Result of scoring calculation."""
    overall_score: float
    signal_scores: Dict[str, SignalResult]
    risk_flags: List[str]
    details: Dict[str, Any]


class ScoringEngine:
    """Calculates overall score from signals and generates risk flags."""

    def __init__(self, weights: Dict[str, float] = None):
        """
        Initialize scoring engine with signal weights.
        
        Args:
            weights: Dictionary of signal names to weights. 
                     If None, uses default weights from plan.
        """
        if weights is None:
            # Default weights from the MVP plan
            self.weights = {
                "commit_consistency": 0.15,
                "language_diversity": 0.10,
                "issue_engagement": 0.15,
                "pr_patterns": 0.15,
                "project_ownership": 0.10,
                "review_patterns": 0.10,
                "response_time": 0.15,
                "readme_quality": 0.10,
            }
        else:
            self.weights = weights

    def calculate_overall_score(self, signal_results: Dict[str, SignalResult]) -> float:
        """Calculate weighted overall score from signal results."""
        total_weight = 0
        weighted_sum = 0

        for signal_name, result in signal_results.items():
            if signal_name in self.weights:
                weight = self.weights[signal_name]
                weighted_sum += result.score * weight
                total_weight += weight

        if total_weight == 0:
            return 0

        return weighted_sum / total_weight

    def generate_risk_flags(self, signal_results: Dict[str, SignalResult]) -> List[str]:
        """Generate risk flags based on low scores or low confidence."""
        risk_flags = []

        for signal_name, result in signal_results.items():
            if result.score < 30 and result.confidence > 0.5:
                risk_flags.append(f"Low {signal_name.replace('_', ' ')} score")
            
            if result.confidence < 0.3:
                risk_flags.append(f"Low confidence in {signal_name.replace('_', ' ')}")

        return risk_flags

    def score_user(self, activity_data: Dict[str, Any]) -> ScoreResult:
        """Score a user based on their GitHub activity data."""
        from signals.extractor import SignalExtractor
        
        extractor = SignalExtractor()
        signal_results = extractor.extract_all_signals(activity_data)
        
        overall_score = self.calculate_overall_score(signal_results)
        risk_flags = self.generate_risk_flags(signal_results)
        
        details = {
            "total_repos": len(activity_data.get("repos", [])),
            "total_commits": len(activity_data.get("commits", [])),
            "total_issues": len(activity_data.get("issues", [])),
            "total_prs": len(activity_data.get("prs", [])),
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