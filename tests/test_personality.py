"""
Unit tests for the personality inference module.
"""
import pytest
from datetime import datetime, timezone, timedelta
from crawler.github_api import GitHubRepo, GitHubCommit, GitHubPR, GitHubIssue
from signals.personality import (
    FlexibilitySignal,
    AmbiguityComfortSignal,
    ChangeReadinessClassifier,
    _classify_domain,
    extract_personality,
    _DOMAIN_KEYWORDS,
)
from signals.extractor import SignalResult


def _make_repo(name, desc="", lang="Python", is_fork=False):
    return GitHubRepo(
        name=name,
        full_name=f"user/{name}",
        description=desc,
        language=lang,
        stars=0,
        forks=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        pushed_at=datetime.now(timezone.utc),
        is_fork=is_fork,
        is_private=False,
    )


def _make_commit(sha, date, additions=10, deletions=5):
    return GitHubCommit(
        sha=sha,
        message="test commit",
        author="testuser",
        date=date,
        additions=additions,
        deletions=deletions,
    )


def _make_pr(number, created_at, merged_at=None):
    return GitHubPR(
        number=number,
        title="test PR",
        state="MERGED" if merged_at else "OPEN",
        created_at=created_at,
        closed_at=merged_at,
        merged_at=merged_at,
        additions=10,
        deletions=5,
        changed_files=2,
        comments=3,
        review_comments=2,
        author="testuser",
    )


class TestDomainClassification:
    def test_classify_api_repo(self):
        repo = _make_repo("user-api", "REST API backend service", "TypeScript")
        assert _classify_domain(repo) == "web_backend"

    def test_classify_ml_repo(self):
        repo = _make_repo("ml-pipeline", "data processing and ML training", "Python")
        assert _classify_domain(repo) == "data_science"

    def test_classify_docs_repo(self):
        repo = _make_repo("knowledge-base", "technical documentation wiki", "Markdown")
        assert _classify_domain(repo) == "docs_content"

    def test_classify_uncategorized(self):
        repo = _make_repo("zxy-random-thing", "", "Rust")
        # Rust is not in any domain keyword list, description is empty
        assert _classify_domain(repo) == "uncategorized"

    def test_classify_security_repo(self):
        repo = _make_repo("zk-proof-system", "zero-knowledge blockchain attestation", "Solidity")
        assert _classify_domain(repo) == "security"


class TestFlexibilitySignal:
    def test_no_data_returns_neutral(self):
        extractor = FlexibilitySignal()
        result = extractor.extract({"commits": [], "prs": []})
        assert result.score == 50
        assert result.confidence <= 0.1

    def test_rapid_iteration_high_flexibility(self):
        now = datetime.now(timezone.utc)
        commits = [
            _make_commit("a", now - timedelta(hours=2)),
            _make_commit("b", now - timedelta(hours=1, minutes=50)),
            _make_commit("c", now - timedelta(hours=1, minutes=40)),
            _make_commit("d", now - timedelta(hours=1)),
            _make_commit("e", now - timedelta(minutes=50)),
            _make_commit("f", now - timedelta(minutes=40)),
        ]
        result = FlexibilitySignal().extract({"commits": commits, "prs": [], "repos": [], "issues": []})
        assert result.score >= 50  # Fast iteration density = decent flexibility

    def test_low_activity_lower_flexibility(self):
        now = datetime.now(timezone.utc)
        commits = [
            _make_commit("a", now - timedelta(days=30)),
            _make_commit("b", now - timedelta(days=1)),
        ]
        result = FlexibilitySignal().extract({"commits": commits, "prs": [], "repos": [], "issues": []})
        assert result.score < 70  # Few spread-out commits

    def test_fast_merge_boosts_responsiveness(self):
        now = datetime.now(timezone.utc)
        prs = [
            _make_pr(1, now - timedelta(hours=2), now - timedelta(hours=1)),
            _make_pr(2, now - timedelta(days=1), now - timedelta(hours=20)),
        ]
        result = FlexibilitySignal().extract({"commits": [], "prs": prs, "repos": [], "issues": []})
        assert result.details.get("responsiveness", 0) >= 70

    def test_multiple_languages_boosts_flexibility(self):
        repos = [
            _make_repo("py-project", lang="Python"),
            _make_repo("ts-project", lang="TypeScript"),
            _make_repo("rs-project", lang="Rust"),
            _make_repo("go-project", lang="Go"),
        ]
        result = FlexibilitySignal().extract({"commits": [], "prs": [], "repos": repos, "issues": []})
        assert result.details.get("lang_switching", 0) == 50  # 4 langs = tier 2


class TestAmbiguityComfortSignal:
    def test_no_repos_returns_neutral(self):
        result = AmbiguityComfortSignal().extract({"repos": [], "commits": []})
        assert result.score == 50
        assert result.confidence <= 0.1

    def test_multiple_domains_high_ambiguity(self):
        repos = [
            _make_repo("api-service", "REST backend", "Python"),
            _make_repo("react-dashboard", "frontend UI", "TypeScript"),
            _make_repo("ml-model", "data pipeline ML", "Python"),
            _make_repo("docker-infra", "deployment infra", "HCL"),
            _make_repo("cli-tool", "command line utility", "Rust"),
            _make_repo("zk-proof", "crypto attestation", "Solidity"),
        ]
        result = AmbiguityComfortSignal().extract({"repos": repos, "commits": []})
        assert result.score >= 60
        assert result.details.get("num_domains", 0) >= 4

    def test_single_domain_low_ambiguity(self):
        repos = [
            _make_repo("api-v1", "REST API", "Python"),
            _make_repo("api-v2", "REST API rev2", "Python"),
            _make_repo("api-lib", "API library", "Python"),
        ]
        result = AmbiguityComfortSignal().extract({"repos": repos, "commits": []})
        assert result.score < 60

    def test_high_variation_in_commit_sizes(self):
        commits = [
            _make_commit("a", datetime.now(timezone.utc), additions=1, deletions=0),
            _make_commit("b", datetime.now(timezone.utc), additions=100, deletions=50),
            _make_commit("c", datetime.now(timezone.utc), additions=2, deletions=1),
            _make_commit("d", datetime.now(timezone.utc), additions=500, deletions=200),
            _make_commit("e", datetime.now(timezone.utc), additions=10, deletions=5),
            _make_commit("f", datetime.now(timezone.utc), additions=0, deletions=300),
        ]
        result = AmbiguityComfortSignal().extract({"repos": [_make_repo("test")], "commits": commits})
        # High variation = high non-rigidity
        assert result.details.get("non_rigidity", 0) > 50


class TestChangeReadinessClassifier:
    def test_classify_results_segment(self):
        scores = {
            "flexibility": SignalResult("flexibility", 90, 0.8, {}),
            "ambiguity_comfort": SignalResult("ambiguity_comfort", 85, 0.8, {}),
            "issue_engagement": SignalResult("issue_engagement", 80, 0.7, {}),
            "review_patterns": SignalResult("review_patterns", 75, 0.7, {}),
            "pr_patterns": SignalResult("pr_patterns", 70, 0.7, {}),
            "project_ownership": SignalResult("project_ownership", 80, 0.8, {}),
            "language_diversity": SignalResult("language_diversity", 85, 0.8, {}),
            "commit_consistency": SignalResult("commit_consistency", 70, 0.7, {}),
        }
        classifier = ChangeReadinessClassifier()
        segment, score = classifier.classify(scores)
        assert segment == "Results"
        assert score >= 76

    def test_classify_reluctant_segment(self):
        scores = {
            "flexibility": SignalResult("flexibility", 30, 0.6, {}),
            "ambiguity_comfort": SignalResult("ambiguity_comfort", 25, 0.6, {}),
            "issue_engagement": SignalResult("issue_engagement", 20, 0.5, {}),
            "review_patterns": SignalResult("review_patterns", 15, 0.5, {}),
            "pr_patterns": SignalResult("pr_patterns", 25, 0.5, {}),
            "project_ownership": SignalResult("project_ownership", 35, 0.6, {}),
            "language_diversity": SignalResult("language_diversity", 20, 0.6, {}),
            "commit_consistency": SignalResult("commit_consistency", 30, 0.6, {}),
        }
        classifier = ChangeReadinessClassifier()
        segment, score = classifier.classify(scores)
        assert segment == "Reluctant"

    def test_empty_scores_defaults_insufficient(self):
        classifier = ChangeReadinessClassifier()
        segment, score = classifier.classify({})
        assert "Resistant" in segment or "Insufficient" in segment

    def test_extract_personality_returns_all_keys(self):
        data = {
            "repos": [_make_repo("test")],
            "commits": [],
            "prs": [],
            "issues": [],
        }
        result = extract_personality(data)
        assert "signals" in result
        assert "flexibility" in result["signals"]
        assert "ambiguity_comfort" in result["signals"]
        assert "change_readiness" in result
        assert "segment" in result["change_readiness"]
        assert "score" in result["change_readiness"]
