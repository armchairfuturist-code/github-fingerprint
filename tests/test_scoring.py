"""
Unit tests for the scoring engine.
"""
import pytest
from scoring.engine import ScoringEngine
from signals.extractor import SignalResult


def test_scoring_engine_initialization():
    engine = ScoringEngine()
    assert len(engine.weights) == 8
    assert "commit_consistency" in engine.weights
    assert engine.weights["commit_consistency"] == 0.15


def test_scoring_engine_custom_weights():
    custom_weights = {"commit_consistency": 0.5, "language_diversity": 0.5}
    engine = ScoringEngine(weights=custom_weights)
    assert engine.weights == custom_weights


def test_calculate_overall_score():
    engine = ScoringEngine()
    mock_signals = {
        "commit_consistency": SignalResult("commit_consistency", 80, 0.8, {}),
        "language_diversity": SignalResult("language_diversity", 60, 0.7, {}),
        "issue_engagement": SignalResult("issue_engagement", 70, 0.6, {}),
        "pr_patterns": SignalResult("pr_patterns", 75, 0.75, {}),
        "project_ownership": SignalResult("project_ownership", 85, 0.8, {}),
        "review_patterns": SignalResult("review_patterns", 65, 0.65, {}),
        "response_time": SignalResult("response_time", 90, 0.9, {}),
        "readme_quality": SignalResult("readme_quality", 55, 0.55, {}),
    }
    
    overall = engine.calculate_overall_score(mock_signals)
    assert 0 <= overall <= 100
    assert abs(overall - 73.75) < 0.01


def test_generate_risk_flags():
    engine = ScoringEngine()
    mock_signals = {
        "commit_consistency": SignalResult("commit_consistency", 25, 0.8, {}),
        "language_diversity": SignalResult("language_diversity", 60, 0.2, {}),
        "issue_engagement": SignalResult("issue_engagement", 70, 0.6, {}),
    }
    
    risk_flags = engine.generate_risk_flags(mock_signals)
    assert len(risk_flags) == 2
    assert "Low commit consistency score" in risk_flags
    assert "Low confidence in language diversity" in risk_flags


def test_score_user():
    engine = ScoringEngine()
    mock_activity = {
        "repos": [],
        "commits": [],
        "issues": [],
        "prs": [],
    }
    
    result = engine.score_user(mock_activity)
    assert hasattr(result, "overall_score")
    assert hasattr(result, "signal_scores")
    assert hasattr(result, "risk_flags")
    assert hasattr(result, "details")


def test_score_user_with_data():
    from crawler.github_api import GitHubRepo, GitHubCommit, GitHubIssue, GitHubPR
    from datetime import datetime
    
    engine = ScoringEngine()
    
    mock_repo = GitHubRepo(
        name="test-repo",
        full_name="user/test-repo",
        description="Test repository",
        language="Python",
        stars=10,
        forks=5,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        pushed_at=datetime.now(),
        is_fork=False,
        is_private=False,
    )
    
    mock_commit = GitHubCommit(
        sha="abc123",
        message="Test commit",
        author="testuser",
        date=datetime.now(),
        additions=10,
        deletions=5,
    )
    
    mock_issue = GitHubIssue(
        number=1,
        title="Test issue",
        state="CLOSED",
        created_at=datetime.now(),
        closed_at=datetime.now(),
        comments=5,
        author="testuser",
    )
    
    mock_pr = GitHubPR(
        number=1,
        title="Test PR",
        state="MERGED",
        created_at=datetime.now(),
        closed_at=datetime.now(),
        merged_at=datetime.now(),
        additions=10,
        deletions=5,
        changed_files=2,
        comments=3,
        review_comments=2,
        author="testuser",
    )
    
    mock_activity = {
        "repos": [mock_repo],
        "commits": [mock_commit],
        "issues": [mock_issue],
        "prs": [mock_pr],
    }
    
    result = engine.score_user(mock_activity)
    assert result.overall_score >= 0
    assert result.overall_score <= 100
    assert len(result.signal_scores) == 8
