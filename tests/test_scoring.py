"""
Unit tests for the scoring engine.
"""
import pytest
from datetime import datetime
from scoring.engine import ScoringEngine
from signals.extractor import SignalResult


def test_scoring_engine_initialization():
    engine = ScoringEngine()
    assert len(engine.weights) == 12
    assert "commit_consistency" in engine.weights
    assert "commit_semantics" in engine.weights
    assert "cicd_maturity" in engine.weights
    assert "contribution_consistency" in engine.weights
    assert "ai_usage_patterns" in engine.weights
    assert engine.weights["commit_consistency"] == 0.10


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
        "commit_semantics": SignalResult("commit_semantics", 80, 0.8, {}),
        "cicd_maturity": SignalResult("cicd_maturity", 70, 0.7, {}),
        "contribution_consistency": SignalResult("contribution_consistency", 75, 0.75, {}),
        "ai_usage_patterns": SignalResult("ai_usage_patterns", 65, 0.65, {}),
    }
    
    overall = engine.calculate_overall_score(mock_signals)
    assert 0 <= overall <= 100
    assert abs(overall - 73.1) < 0.01


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
    assert len(result.signal_scores) == 12


def test_extract_readme_quality_with_content():
    """readme_quality should score higher with actual README content vs fallback."""
    from signals.extractor import SignalExtractor
    from crawler.github_api import GitHubRepo, GitHubReadme

    extractor = SignalExtractor()
    now = datetime.now()

    repos = [
        GitHubRepo("repo1", "user/repo1", "desc", "Python", 1, 0, now, now, now, False, False),
        GitHubRepo("repo2", "user/repo2", "desc2", "JS", 1, 0, now, now, now, False, False),
    ]

    # With README content
    readmes = {
        "user/repo1": GitHubReadme(
            content="# Project\n\n## Install\n\nCode:\n```\npip install\n```\n\n- Item 1\n- Item 2",
            size_bytes=80, encoding="base64", name="README.md",
            detected_sections=["Install"], badge_count=0,
            has_code_blocks=True, code_block_count=1,
            has_emoji=False, list_count=2,
        ),
        "user/repo2": GitHubReadme(
            content="# Another\n\n## Usage\n\n```py\nfoo()\n```",
            size_bytes=50, encoding="base64", name="README.md",
            detected_sections=["Usage"], badge_count=0,
            has_code_blocks=True, code_block_count=1,
            has_emoji=False, list_count=0,
        ),
    }

    result_readme = extractor.extract_readme_quality(repos, readmes)
    assert result_readme.name == "readme_quality"
    assert 0 <= result_readme.score <= 100
    assert result_readme.details.get("mode") == "readme_content"
    assert result_readme.details.get("repos_with_readme") == 2

    # Fallback (no readmes) should use description mode
    result_fallback = extractor.extract_readme_quality(repos)
    assert result_fallback.details.get("mode") == "description_fallback"

    # Empty repos
    result_empty = extractor.extract_readme_quality([])
    assert result_empty.score == 0
    assert result_empty.confidence == 0


def test_extract_commit_semantics():
    """commit_semantics should score conventional commits higher."""
    from signals.extractor import SignalExtractor
    from crawler.github_api import GitHubCommit

    extractor = SignalExtractor()
    now = datetime.now()

    # Well-structured commits (conventional, multi-line, imperative)
    good_commits = [
        GitHubCommit("a", "feat: add login page", "user", now, 10, 0),
        GitHubCommit("b", "fix(core): resolve timeout\n\nExtended body with details", "user", now, 5, 2),
        GitHubCommit("c", "docs: update README with setup", "user", now, 1, 0),
        GitHubCommit("d", "refactor: extract validation\n\nSeparated concerns", "user", now, 20, 15),
    ]

    # Poorly structured commits (no conventional prefix, short, single-line, non-imperative)
    bad_commits = [
        GitHubCommit("e", "fixed stuff", "user", now, 3, 1),
        GitHubCommit("f", "Updated the thing", "user", now, 2, 0),
        GitHubCommit("g", "x", "user", now, 1, 1),
    ]

    good_result = extractor.extract_commit_semantics(good_commits)
    bad_result = extractor.extract_commit_semantics(bad_commits)

    assert good_result.name == "commit_semantics"
    assert 0 <= good_result.score <= 100
    assert 0 <= bad_result.score <= 100
    assert good_result.score > bad_result.score, (
        f"Good commits ({good_result.score}) should score higher than bad ({bad_result.score})"
    )
    assert good_result.details.get("conventional_commit_ratio", 0) >= 0.75
    assert bad_result.details.get("conventional_commit_ratio", 1) < 0.34

    # Empty commits
    empty_result = extractor.extract_commit_semantics([])
    assert empty_result.score == 0
    assert empty_result.confidence == 0


def test_readme_quality_scores_above_zero_with_readme_data():
    """When readme data is present, score should be > 0."""
    from signals.extractor import SignalExtractor
    from crawler.github_api import GitHubRepo, GitHubReadme

    extractor = SignalExtractor()
    now = datetime.now()

    repos = [
        GitHubRepo("r1", "u/r1", "desc", "Go", 5, 2, now, now, now, False, False),
    ]
    readmes = {
        "u/r1": GitHubReadme(
            content="# R1\n\n## Intro\n\n```sh\ngo run\n```\n\n- A\n- B\n\n[![CI](https://img)](https://ci.com)",
            size_bytes=100, encoding="base64", name="README.md",
            detected_sections=["Intro"], badge_count=1,
            has_code_blocks=True, code_block_count=1,
            has_emoji=False, list_count=2,
        ),
    }

    result = extractor.extract_readme_quality(repos, readmes)
    assert result.score > 0
    assert result.details.get("repos_with_readme") == 1


def test_commit_semantics_details():
    """commit_semantics details should include breakdown info."""
    from signals.extractor import SignalExtractor
    from crawler.github_api import GitHubCommit

    extractor = SignalExtractor()
    now = datetime.now()

    commits = [
        GitHubCommit("a", "feat: new feature", "u", now, 5, 0),
        GitHubCommit("b", "fix: bugfix", "u", now, 3, 1),
        GitHubCommit("c", "docs: docs update", "u", now, 1, 0),
    ]

    result = extractor.extract_commit_semantics(commits)

    assert "conventional_breakdown" in result.details
    assert "feat" in result.details["conventional_breakdown"]
    assert "fix" in result.details["conventional_breakdown"]
    assert "docs" in result.details["conventional_breakdown"]
    assert result.details["conventional_breakdown"]["feat"] == 1
    assert result.details["total_commits"] == 3
    assert "avg_message_length" in result.details
    assert "multi_line_ratio" in result.details
    assert "imperative_mood_ratio" in result.details


# ---- CI/CD Maturity Tests ----

def test_cicd_maturity_empty():
    """cicd_maturity should return 0 for no data."""
    from signals.extractor import SignalExtractor

    extractor = SignalExtractor()
    result = extractor.extract_cicd_maturity(None, None)
    assert result.name == "cicd_maturity"
    assert result.score == 0
    assert result.confidence == 0


def test_cicd_maturity_no_configs():
    """cicd_maturity should return 0 when no CI/CD configs found."""
    from signals.extractor import SignalExtractor
    from crawler.github_api import GitHubRepo, GitHubCICDConfig

    extractor = SignalExtractor()
    now = datetime.now()
    repo = GitHubRepo("r1", "u/r1", "desc", "Py", 1, 0, now, now, now, False, False)
    repos = [repo]
    cicd_configs = {
        "u/r1": [
            GitHubCICDConfig(".travis.yml", "travis", False),
            GitHubCICDConfig("Dockerfile", "docker", False),
        ]
    }

    result = extractor.extract_cicd_maturity(cicd_configs, repos)
    assert result.score == 0
    assert 0 <= result.confidence <= 1
    assert "No CI/CD detected" in result.details.get("message", "")


def test_cicd_maturity_with_configs():
    """cicd_maturity should score higher with more CI/CD types."""
    from signals.extractor import SignalExtractor
    from crawler.github_api import GitHubRepo, GitHubCICDConfig

    extractor = SignalExtractor()
    now = datetime.now()
    repos = [
        GitHubRepo("r1", "u/r1", "desc", "Py", 1, 0, now, now, now, False, False),
        GitHubRepo("r2", "u/r2", "desc", "JS", 1, 0, now, now, now, False, False),
    ]
    cicd_configs = {
        "u/r1": [
            GitHubCICDConfig(".github/workflows", "github_actions", True,
                             0, "directory with 3 file(s)"),
            GitHubCICDConfig("Dockerfile", "docker", True, 200, "Dockerfile (200 bytes)"),
            GitHubCICDConfig(".travis.yml", "travis", False),
        ],
        "u/r2": [
            GitHubCICDConfig(".github/workflows", "github_actions", True,
                             0, "directory with 1 file(s)"),
            GitHubCICDConfig("Dockerfile", "docker", False),
        ],
    }

    result = extractor.extract_cicd_maturity(cicd_configs, repos)
    assert result.name == "cicd_maturity"
    assert result.score > 0
    assert result.details.get("repos_with_ci", 0) >= 1
    assert "github_actions" in result.details.get("ci_types_found", [])
    assert 0 <= result.confidence <= 1


def test_cicd_maturity_multiple_types_higher():
    """More CI types across repos should yield higher score."""
    from signals.extractor import SignalExtractor
    from crawler.github_api import GitHubRepo, GitHubCICDConfig

    extractor = SignalExtractor()
    now = datetime.now()

    # Single type only
    repos_single = [
        GitHubRepo("r1", "u/r1", "d", "Py", 1, 0, now, now, now, False, False),
    ]
    cicd_single = {
        "u/r1": [
            GitHubCICDConfig(".github/workflows", "github_actions", True, 0, "wf"),
        ]
    }

    # Multiple types
    repos_multi = [
        GitHubRepo("r1", "u/r1", "d", "Py", 1, 0, now, now, now, False, False),
    ]
    cicd_multi = {
        "u/r1": [
            GitHubCICDConfig(".github/workflows", "github_actions", True, 0, "wf"),
            GitHubCICDConfig("Dockerfile", "docker", True, 200, "Dockerfile"),
            GitHubCICDConfig(".circleci/config.yml", "circleci", True, 500, "config"),
        ]
    }

    result_single = extractor.extract_cicd_maturity(cicd_single, repos_single)
    result_multi = extractor.extract_cicd_maturity(cicd_multi, repos_multi)

    assert result_multi.score >= result_single.score, (
        f"Multi-type ({result_multi.score}) should >= single ({result_single.score})"
    )
    assert result_multi.details.get("ci_type_count", 0) == 3
    assert result_single.details.get("ci_type_count", 0) == 1


# ---- Contribution Consistency Tests ----

def test_contribution_consistency_no_data():
    """contribution_consistency should return 0 for no data."""
    from signals.extractor import SignalExtractor

    extractor = SignalExtractor()
    result = extractor.extract_contribution_consistency(None, None)
    assert result.name == "contribution_consistency"
    assert result.score == 0
    assert result.confidence == 0


def test_contribution_consistency_empty_calendar():
    """contribution_consistency should handle empty calendar."""
    from signals.extractor import SignalExtractor
    from crawler.github_api import GitHubContributionData

    extractor = SignalExtractor()
    empty_contrib = GitHubContributionData(total_contributions=0, contribution_days=[])
    result = extractor.extract_contribution_consistency(empty_contrib, None)
    assert result.score == 0
    assert result.confidence == 0.5


def test_contribution_consistency_regular():
    """Regular daily contributions should score higher."""
    from signals.extractor import SignalExtractor
    from crawler.github_api import GitHubContributionData, GitHubContributionDay

    extractor = SignalExtractor()
    now = datetime.now()
    from datetime import timedelta

    # Regular: contributions every day for 90 days
    regular_days = []
    for i in range(90):
        day = now - timedelta(days=90 - i)
        regular_days.append(GitHubContributionDay(
            date=day.replace(hour=0, minute=0, second=0, microsecond=0),
            contribution_count=3 if i % 2 == 0 else 5,
        ))

    regular_contrib = GitHubContributionData(
        total_contributions=sum(d.contribution_count for d in regular_days),
        contribution_days=regular_days,
        total_weeks=13,
        weeks_with_contributions=13,
        longest_streak=90,
        current_streak=90,
    )

    result = extractor.extract_contribution_consistency(regular_contrib, None)
    assert result.name == "contribution_consistency"
    assert result.details.get("mode") == "contribution_calendar"
    assert result.score > 50, f"Regular pattern should score >50, got {result.score}"
    assert result.details.get("activity_ratio", 0) == 1.0
    assert result.details.get("max_gap_days", 0) == 0


def test_contribution_consistency_sporadic():
    """Sporadic contributions with long gaps should score lower."""
    from signals.extractor import SignalExtractor
    from crawler.github_api import GitHubContributionData, GitHubContributionDay

    extractor = SignalExtractor()
    now = datetime.now()
    from datetime import timedelta

    # Sporadic: contributions in bursts with 30+ day gaps
    sporadic_days = []
    for i in range(365):
        day = now - timedelta(days=365 - i)
        # Only contribute in two clusters: day 0-5 and day 300-305
        if i < 5 or (i > 300 and i < 305):
            sporadic_days.append(GitHubContributionDay(
                date=day.replace(hour=0, minute=0, second=0, microsecond=0),
                contribution_count=10,
            ))
        else:
            sporadic_days.append(GitHubContributionDay(
                date=day.replace(hour=0, minute=0, second=0, microsecond=0),
                contribution_count=0,
            ))

    sporadic_contrib = GitHubContributionData(
        total_contributions=sum(d.contribution_count for d in sporadic_days),
        contribution_days=sporadic_days,
        total_weeks=52,
        weeks_with_contributions=2,
        longest_streak=5,
        current_streak=5,
    )

    result = extractor.extract_contribution_consistency(sporadic_contrib, None)
    assert result.score < 50, f"Sporadic pattern should score <50, got {result.score}"
    assert result.details.get("max_gap_days", 0) >= 30


def test_contribution_consistency_commit_fallback():
    """contribution_consistency should fall back to commit analysis."""
    from signals.extractor import SignalExtractor
    from crawler.github_api import GitHubCommit

    extractor = SignalExtractor()
    now = datetime.now()
    from datetime import timedelta

    # Spread over 30 days with reasonable gaps
    commits = []
    for i in range(20):
        commits.append(GitHubCommit(
            str(i), f"commit {i}", "u",
            now - timedelta(days=30 - i, hours=i * 3),
            5, 0
        ))

    result = extractor.extract_contribution_consistency(None, commits)
    assert result.name == "contribution_consistency"
    assert result.details.get("mode") == "commit_fallback"
    assert 0 <= result.score <= 100


# ---- AI Usage Pattern Tests ----

def test_ai_usage_patterns_no_commits():
    """ai_usage_patterns should return neutral score for no data."""
    from signals.extractor import SignalExtractor

    extractor = SignalExtractor()
    result = extractor.extract_ai_usage_patterns([])
    assert result.name == "ai_usage_patterns"
    assert result.score == 50  # Neutral
    assert result.confidence == 0


def test_ai_usage_patterns_organic():
    """Natural organic commit patterns should score higher (60+)."""
    from signals.extractor import SignalExtractor
    from crawler.github_api import GitHubCommit

    extractor = SignalExtractor()
    now = datetime.now()
    from datetime import timedelta

    # Organic pattern: varied message lengths, spread over days, moderate conventional
    commits = []
    messages = [
        "Added unit tests for the parser module",
        "fix: resolve edge case in config loading",
        "Update dependencies",
        "feat: add search bar component",
        "Clean up debug logging",
        "fix(api): handle null response gracefully",
        "Bump version to 2.1.0",
        "docs: update API reference",
        "Refactor database connection pooling",
        "Fix typo in error message",
        "feat(core): implement retry logic",
        "Remove dead code from legacy module",
    ]
    for i, msg in enumerate(messages):
        commits.append(GitHubCommit(
            str(i), msg, "user",
            now - timedelta(hours=i * 6),  # Spread over 3 days
            5 + i, 1 + (i % 3),
        ))

    result = extractor.extract_ai_usage_patterns(commits)
    assert result.score >= 50, f"Organic pattern should score >=50, got {result.score}"


def test_ai_usage_patterns_suspicious():
    """Highly uniform burst patterns should score lower."""
    from signals.extractor import SignalExtractor
    from crawler.github_api import GitHubCommit

    extractor = SignalExtractor()
    now = datetime.now()
    from datetime import timedelta

    # Suspicious: all conventional commits, very uniform lengths, burst in 5 minutes
    commits = []
    for i in range(30):
        commits.append(GitHubCommit(
            str(i),
            f"feat: update module {i}",
            "user",
            now - timedelta(seconds=10 * i),  # All within ~5 minutes
            10, 0,
        ))

    result = extractor.extract_ai_usage_patterns(commits)
    assert result.score < 50, f"Uniform burst should score <50, got {result.score}"


def test_ai_usage_patterns_details():
    """ai_usage_patterns should include timing and style details."""
    from signals.extractor import SignalExtractor
    from crawler.github_api import GitHubCommit

    extractor = SignalExtractor()
    now = datetime.now()
    from datetime import timedelta

    commits = [
        GitHubCommit("a", "feat: add feature", "u", now, 5, 0),
        GitHubCommit("b", "fix: resolve bug", "u", now + timedelta(hours=2), 3, 1),
        GitHubCommit("c", "docs: update docs", "u", now + timedelta(hours=5), 1, 0),
    ]

    result = extractor.extract_ai_usage_patterns(commits)
    assert "total_commits" in result.details
    assert "msg_length_std" in result.details
    assert "avg_msg_length" in result.details
    assert "conventional_commit_ratio" in result.details
    assert result.details["total_commits"] == 3


# ---- Role Profile Tests ----


def test_list_profiles_returns_three():
    """list_profiles should return at least 3 built-in profiles."""
    from scoring.profiles import list_profiles
    profiles = list_profiles()
    assert len(profiles) >= 3
    names = [p.name for p in profiles]
    assert "engineering" in names
    assert "marketing" in names
    assert "non-technical" in names


def test_get_profile_by_name():
    """get_profile should retrieve profiles by machine key."""
    from scoring.profiles import get_profile

    eng = get_profile("engineering")
    assert eng.display_name == "Engineering"
    assert eng.name == "engineering"
    assert len(eng.weights) == 12
    assert len(eng.confidence_thresholds) == 12

    mkt = get_profile("marketing")
    assert mkt.display_name == "Marketing"
    assert mkt.weights["readme_quality"] == 0.20


def test_get_profile_unknown_raises_valueerror():
    """get_profile should raise ValueError for unknown profile names."""
    from scoring.profiles import get_profile
    import pytest

    with pytest.raises(ValueError, match="Unknown profile 'bogus'"):
        get_profile("bogus")
    with pytest.raises(ValueError, match="Unknown profile ''"):
        get_profile("")


def test_profile_weights_sum_to_one():
    """Each built-in profile's weights should sum to approximately 1.0."""
    from scoring.profiles import list_profiles

    for p in list_profiles():
        total = sum(p.weights.values())
        assert abs(total - 1.0) < 0.001, (
            f"Profile '{p.name}' weights sum to {total:.4f}"
        )


def test_all_signals_present_in_every_profile():
    """All 12 signal names must appear in every profile's weights and thresholds."""
    from scoring.profiles import list_profiles, ALL_SIGNALS

    for p in list_profiles():
        for signal in ALL_SIGNALS:
            assert signal in p.weights, f"{p.name} missing weight for {signal}"
            assert signal in p.confidence_thresholds, (
                f"{p.name} missing threshold for {signal}"
            )


def test_resolve_role_profile_defaults_to_engineering():
    """resolve_role_profile(None) should return engineering profile."""
    from scoring.profiles import resolve_role_profile

    p = resolve_role_profile(None)
    assert p.name == "engineering"

    p2 = resolve_role_profile("non-technical")
    assert p2.name == "non-technical"

    p3 = resolve_role_profile("marketing")
    assert p3.name == "marketing"


def test_resolve_role_profile_unknown_raises():
    """resolve_role_profile should raise ValueError for unknown roles."""
    from scoring.profiles import resolve_role_profile
    import pytest

    with pytest.raises(ValueError):
        resolve_role_profile("nonexistent_role")


def test_engineering_thresholds_mark_tech_higher():
    """Engineering profile should have higher thresholds for tech signals."""
    from scoring.profiles import get_profile, TECH_SIGNALS, PROCESS_SIGNALS

    eng = get_profile("engineering")
    for signal in TECH_SIGNALS:
        assert eng.confidence_thresholds[signal] >= 0.4, (
            f"Engineering threshold for tech signal '{signal}' should be >=0.4"
        )
    for signal in PROCESS_SIGNALS:
        assert eng.confidence_thresholds[signal] >= 0.3, (
            f"Engineering threshold for process signal '{signal}' should be >=0.3"
        )


def test_marketing_thresholds_mark_comms_higher():
    """Marketing profile should have higher thresholds for comms signals."""
    from scoring.profiles import get_profile, COMMS_SIGNALS, CODE_SIGNALS

    mkt = get_profile("marketing")
    for signal in COMMS_SIGNALS:
        assert mkt.confidence_thresholds[signal] >= 0.3, (
            f"Marketing threshold for comms signal '{signal}' should be >=0.3"
        )
    for signal in CODE_SIGNALS:
        assert mkt.confidence_thresholds[signal] >= 0.2, (
            f"Marketing threshold for code signal '{signal}' should be >=0.2"
        )


def test_non_technical_thresholds_mark_project_higher():
    """Non-technical profile should have higher thresholds for project signals."""
    from scoring.profiles import get_profile, PROJECT_SIGNALS, CODE_SIGNALS

    nt = get_profile("non-technical")
    for signal in PROJECT_SIGNALS:
        assert nt.confidence_thresholds[signal] >= 0.25, (
            f"Non-technical threshold for project signal '{signal}' should be >=0.25"
        )
    for signal in CODE_SIGNALS:
        assert nt.confidence_thresholds[signal] >= 0.1, (
            f"Non-technical threshold for code signal '{signal}' should be >=0.1"
        )


def test_confidence_thresholds_in_range():
    """All confidence thresholds should be between 0.0 and 1.0."""
    from scoring.profiles import list_profiles

    for p in list_profiles():
        for signal, threshold in p.confidence_thresholds.items():
            assert 0.0 <= threshold <= 1.0, (
                f"{p.name} threshold for '{signal}' is {threshold}"
            )


def test_roleprofile_invalid_weights_raises():
    """RoleProfile construction with bad weights should raise ValueError."""
    from scoring.profiles import RoleProfile, ALL_SIGNALS
    import pytest

    # Weights that don't sum to 1.0
    bad_weights = {s: 0.01 for s in ALL_SIGNALS}  # sum = 0.12
    with pytest.raises(ValueError, match="weights sum to"):
        RoleProfile(
            name="bad",
            display_name="Bad",
            description="Bad profile",
            weights=bad_weights,
            confidence_thresholds={s: 0.5 for s in ALL_SIGNALS},
        )


def test_roleprofile_missing_signals_raises():
    """RoleProfile with missing signal keys should raise ValueError."""
    from scoring.profiles import RoleProfile, ALL_SIGNALS
    import pytest

    # Missing one signal
    partial_weights = {s: (1.0 / len(ALL_SIGNALS)) for s in ALL_SIGNALS[:-1]}
    partial_thresholds = {s: 0.5 for s in ALL_SIGNALS[:-1]}

    with pytest.raises(ValueError, match="missing weights"):
        RoleProfile(
            name="partial",
            display_name="Partial",
            description="Missing a signal",
            weights=partial_weights,
            confidence_thresholds=partial_thresholds,
        )

    # Missing one threshold
    full_weights = {s: (1.0 / len(ALL_SIGNALS)) for s in ALL_SIGNALS}
    with pytest.raises(ValueError, match="missing thresholds"):
        RoleProfile(
            name="partial2",
            display_name="Partial2",
            description="Missing a threshold",
            weights=full_weights,
            confidence_thresholds=partial_thresholds,
        )


def test_roleprofile_bad_threshold_out_of_range():
    """RoleProfile with out-of-range threshold should raise ValueError."""
    from scoring.profiles import RoleProfile, ALL_SIGNALS
    import pytest

    weights = {s: (1.0 / len(ALL_SIGNALS)) for s in ALL_SIGNALS}
    bad_thresholds = {s: 0.5 for s in ALL_SIGNALS}
    bad_thresholds["commit_consistency"] = 1.5  # Out of range

    with pytest.raises(ValueError, match="expected \\[0.0, 1.0\\]"):
        RoleProfile(
            name="bad_thresh",
            display_name="Bad Thresh",
            description="Bad threshold",
            weights=weights,
            confidence_thresholds=bad_thresholds,
        )


def test_profile_display_names_readable():
    """Profile display names should be human-readable, not machine keys."""
    from scoring.profiles import list_profiles

    for p in list_profiles():
        assert p.display_name[0].isupper(), (
            f"Display name '{p.display_name}' should start uppercase"
        )
        assert len(p.display_name) > 2


def test_profiles_provide_descriptions():
    """Every profile should have a non-empty description."""
    from scoring.profiles import list_profiles

    for p in list_profiles():
        assert p.description, f"Profile '{p.name}' has empty description"
        assert len(p.description) > 20


# ---- ScoringEngine Negative Tests ----


def test_set_role_unknown_raises_valueerror():
    """set_role with unknown profile should raise ValueError."""
    engine = ScoringEngine()
    with pytest.raises(ValueError, match="Unknown profile 'bogus'"):
        engine.set_role("bogus")
    with pytest.raises(ValueError, match="Unknown profile ''"):
        engine.set_role("")


def test_constructor_with_invalid_profile_raises_valueerror():
    """Constructor with invalid profile name should raise ValueError."""
    with pytest.raises(ValueError, match="Unknown profile 'nonexistent'"):
        ScoringEngine(profile="nonexistent")


def test_calculate_overall_score_empty_signals():
    """Empty signal_results should return score of 0."""
    engine = ScoringEngine()
    score = engine.calculate_overall_score({})
    assert score == 0.0


def test_calculate_overall_score_all_below_threshold():
    """All signals below their confidence threshold should return score of 0."""
    engine = ScoringEngine(profile="engineering")
    signals = {
        "commit_consistency": SignalResult("commit_consistency", 50, 0.01, {}),
        "language_diversity": SignalResult("language_diversity", 50, 0.01, {}),
        "issue_engagement": SignalResult("issue_engagement", 50, 0.01, {}),
        "pr_patterns": SignalResult("pr_patterns", 50, 0.01, {}),
        "project_ownership": SignalResult("project_ownership", 50, 0.01, {}),
        "review_patterns": SignalResult("review_patterns", 50, 0.01, {}),
        "response_time": SignalResult("response_time", 50, 0.01, {}),
        "readme_quality": SignalResult("readme_quality", 50, 0.01, {}),
        "commit_semantics": SignalResult("commit_semantics", 50, 0.01, {}),
        "cicd_maturity": SignalResult("cicd_maturity", 50, 0.01, {}),
        "contribution_consistency": SignalResult("contribution_consistency", 50, 0.01, {}),
        "ai_usage_patterns": SignalResult("ai_usage_patterns", 50, 0.01, {}),
    }
    score = engine.calculate_overall_score(signals)
    assert score == 0.0
    assert len(engine._last_signals_below) == 12


def test_calculate_overall_score_unrecognized_weight():
    """Signals not in self.weights should be silently ignored."""
    engine = ScoringEngine()
    signals = {
        "bogus_signal": SignalResult("bogus_signal", 100, 0.9, {}),
    }
    score = engine.calculate_overall_score(signals)
    assert score == 0.0


def test_profile_scoring_with_details():
    """score_user with a role should populate profile details correctly."""
    from crawler.github_api import GitHubRepo, GitHubCommit, GitHubIssue, GitHubPR
    now = datetime.now()

    activity = {
        "repos": [GitHubRepo("r", "u/r", "d", "Py", 1, 0, now, now, now, False, False)],
        "commits": [GitHubCommit(str(i), "msg", "u", now, 5, 0) for i in range(5)],
        "issues": [],
        "prs": [],
    }

    engine = ScoringEngine()
    result = engine.score_user(activity, role="marketing")
    assert result.details["profile_name"] == "marketing"
    assert isinstance(result.details["signals_below_threshold"], list)
    assert isinstance(result.details["signals_scored"], int)
    assert result.details["signals_scored"] >= 0


# ---- Scoring Behaviour Tests (Role-Adaptive) ----


def test_scoring_engine_with_role_engineering():
    """Engineering profile scores should reflect engineering weight distribution."""
    engine = ScoringEngine(profile="engineering")
    mock_signals = {
        "commit_consistency": SignalResult("commit_consistency", 80, 0.8, {}),
        "language_diversity": SignalResult("language_diversity", 60, 0.7, {}),
        "issue_engagement": SignalResult("issue_engagement", 70, 0.6, {}),
        "pr_patterns": SignalResult("pr_patterns", 75, 0.75, {}),
        "project_ownership": SignalResult("project_ownership", 85, 0.8, {}),
        "review_patterns": SignalResult("review_patterns", 65, 0.65, {}),
        "response_time": SignalResult("response_time", 90, 0.9, {}),
        "readme_quality": SignalResult("readme_quality", 55, 0.55, {}),
        "commit_semantics": SignalResult("commit_semantics", 80, 0.8, {}),
        "cicd_maturity": SignalResult("cicd_maturity", 70, 0.7, {}),
        "contribution_consistency": SignalResult("contribution_consistency", 75, 0.75, {}),
        "ai_usage_patterns": SignalResult("ai_usage_patterns", 65, 0.65, {}),
    }

    overall = engine.calculate_overall_score(mock_signals)
    assert 0 <= overall <= 100
    # Engineering weights differ from legacy; verify they produce a different result
    legacy = ScoringEngine()
    legacy_score = legacy.calculate_overall_score(mock_signals)
    assert abs(overall - legacy_score) > 0.01, (
        f"Engineering profile score ({overall:.4f}) should differ from "
        f"legacy score ({legacy_score:.4f})"
    )


def test_scoring_engine_with_role_marketing():
    """Marketing profile should produce different scores than engineering for same data."""
    mock_signals = {
        "commit_consistency": SignalResult("commit_consistency", 80, 0.8, {}),
        "language_diversity": SignalResult("language_diversity", 60, 0.7, {}),
        "issue_engagement": SignalResult("issue_engagement", 70, 0.6, {}),
        "pr_patterns": SignalResult("pr_patterns", 75, 0.75, {}),
        "project_ownership": SignalResult("project_ownership", 85, 0.8, {}),
        "review_patterns": SignalResult("review_patterns", 65, 0.65, {}),
        "response_time": SignalResult("response_time", 90, 0.9, {}),
        "readme_quality": SignalResult("readme_quality", 55, 0.55, {}),
        "commit_semantics": SignalResult("commit_semantics", 80, 0.8, {}),
        "cicd_maturity": SignalResult("cicd_maturity", 70, 0.7, {}),
        "contribution_consistency": SignalResult("contribution_consistency", 75, 0.75, {}),
        "ai_usage_patterns": SignalResult("ai_usage_patterns", 65, 0.65, {}),
    }

    eng = ScoringEngine(profile="engineering")
    mkt = ScoringEngine(profile="marketing")

    eng_score = eng.calculate_overall_score(mock_signals)
    mkt_score = mkt.calculate_overall_score(mock_signals)

    assert 0 <= eng_score <= 100
    assert 0 <= mkt_score <= 100
    assert abs(eng_score - mkt_score) > 0.01, (
        f"Engineering ({eng_score:.4f}) and Marketing ({mkt_score:.4f}) "
        f"scores should differ"
    )


def test_scoring_engine_role_switching():
    """Switching roles mid-engine should change weights and scores."""
    import copy
    mock_signals = {
        "commit_consistency": SignalResult("commit_consistency", 80, 0.8, {}),
        "language_diversity": SignalResult("language_diversity", 60, 0.7, {}),
        "issue_engagement": SignalResult("issue_engagement", 70, 0.6, {}),
        "pr_patterns": SignalResult("pr_patterns", 75, 0.75, {}),
        "project_ownership": SignalResult("project_ownership", 85, 0.8, {}),
        "review_patterns": SignalResult("review_patterns", 65, 0.65, {}),
        "response_time": SignalResult("response_time", 90, 0.9, {}),
        "readme_quality": SignalResult("readme_quality", 55, 0.55, {}),
        "commit_semantics": SignalResult("commit_semantics", 80, 0.8, {}),
        "cicd_maturity": SignalResult("cicd_maturity", 70, 0.7, {}),
        "contribution_consistency": SignalResult("contribution_consistency", 75, 0.75, {}),
        "ai_usage_patterns": SignalResult("ai_usage_patterns", 65, 0.65, {}),
    }

    engine = ScoringEngine(profile="engineering")
    eng_weights = copy.copy(engine.weights)

    # Switch to marketing
    engine.set_role("marketing")
    assert engine.weights != eng_weights, "Weights should change after set_role"
    # Marketing gives more weight to readme_quality (0.20) vs engineering (0.06)
    assert engine.weights["readme_quality"] == 0.20

    # Switch to non-technical
    engine.set_role("non-technical")
    assert engine.weights["project_ownership"] == 0.20

    # Each profile should produce different scores
    eng = ScoringEngine(profile="engineering")
    mkt = ScoringEngine(profile="marketing")
    nt = ScoringEngine(profile="non-technical")

    eng_s = eng.calculate_overall_score(mock_signals)
    mkt_s = mkt.calculate_overall_score(mock_signals)
    nt_s = nt.calculate_overall_score(mock_signals)

    # All three should be distinct
    scores = [eng_s, mkt_s, nt_s]
    assert len(set(round(s, 4) for s in scores)) == 3, (
        f"All three profiles should produce distinct scores: {scores}"
    )


def test_confidence_threshold_filtering():
    """Signals with confidence below their profile threshold should be excluded."""
    engine = ScoringEngine(profile="engineering")

    # commit_consistency has threshold 0.4 (tech signal) — confidence 0.2 is below
    # pr_patterns has threshold 0.4 — confidence 0.35 is below
    # readme_quality has threshold 0.3 (process signal) — confidence 0.5 is above
    mock_signals = {
        "commit_consistency": SignalResult("commit_consistency", 80, 0.2, {}),
        "pr_patterns": SignalResult("pr_patterns", 75, 0.35, {}),
        "readme_quality": SignalResult("readme_quality", 55, 0.5, {}),
    }

    score = engine.calculate_overall_score(mock_signals)

    # readme_quality (0.06 weight) should be the only active signal
    # Weight redistribution: 0.06 / 0.06 = 1.0, score = 55 * 1.0 = 55.0
    assert score == 55.0, f"Expected 55.0 from single active signal, got {score}"
    assert len(engine._last_signals_below) == 2
    assert "commit_consistency" in engine._last_signals_below
    assert "pr_patterns" in engine._last_signals_below


def test_score_user_backward_compatible():
    """score_user() without role parameter should behave like pre-S02 default."""
    from crawler.github_api import GitHubRepo, GitHubCommit
    now = datetime.now()

    activity = {
        "repos": [GitHubRepo("r", "u/r", "d", "Py", 1, 0, now, now, now, False, False)],
        "commits": [GitHubCommit(str(i), "msg", "u", now, 5, 0) for i in range(3)],
        "issues": [],
        "prs": [],
    }

    # Engine constructed without profile uses legacy weights
    engine = ScoringEngine()

    # Both calls should use identical configuration
    result_none = engine.score_user(activity)
    result_explicit = engine.score_user(activity, role=None)

    assert result_none.overall_score == result_explicit.overall_score
    assert result_none.details["profile_name"] == result_explicit.details["profile_name"]

    # profile_name should be "legacy" (no profile loaded)
    assert result_none.details["profile_name"] == "legacy"

    # Call with explicit role should differ
    result_role = engine.score_user(activity, role="engineering")
    # After the role call, engine state is now "engineering" — the next call without
    # role will still use engineering weights. We only verify the explicit role path.
    assert result_role.details["profile_name"] == "engineering"


def test_generate_risk_flags_with_confidence_thresholds():
    """Risk flags should include confidence threshold violations."""
    engine = ScoringEngine(profile="engineering")

    # One signal below its confidence threshold
    signals_below = ["commit_consistency", "pr_patterns"]
    mock_signals = {
        "commit_consistency": SignalResult("commit_consistency", 25, 0.8, {}),
        "language_diversity": SignalResult("language_diversity", 60, 0.1, {}),
        "pr_patterns": SignalResult("pr_patterns", 80, 0.4, {}),
    }

    risk_flags = engine.generate_risk_flags(mock_signals, signals_below_threshold=signals_below)

    # Should include profile-specific threshold violation flags
    assert any(
        "Insufficient confidence" in flag and "engineering" in flag
        for flag in risk_flags
    ), f"Expected engineering profile confidence flags, got {risk_flags}"
    assert any(
        "commit_consistency" in flag for flag in risk_flags
    ), f"Expected commit_consistency in flags, got {risk_flags}"
    assert any(
        "pr_patterns" in flag for flag in risk_flags
    ), f"Expected pr_patterns in flags, got {risk_flags}"

    # Should also include standard low-score and low-confidence flags
    assert any("Low commit" in flag for flag in risk_flags)
    assert any("Low confidence" in flag for flag in risk_flags)
