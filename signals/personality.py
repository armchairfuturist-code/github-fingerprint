"""
Personality inference signals for the GitHub Fingerprint model.

Combines ExO (SCALE/IDEAS) attributes with the 4Rs segmentation
(Resistant → Reluctant → Resilient → Results) to produce a
comprehensive Developer Operating Model from GitHub activity data.

See docs/personality-model.md for the full model specification.
"""
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, timezone
from collections import Counter, defaultdict

from signals.extractor import SignalResult

logger = logging.getLogger(__name__)

# ---- Domain classification ----

_DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "web_frontend": ["react", "vue", "angular", "svelte", "next", "nuxt", "html", "css",
                     "webapp", "dashboard", "ui", "frontend", "component", "tailwind"],
    "web_backend": ["api", "rest", "graphql", "fastapi", "flask", "django", "express",
                    "server", "backend", "middleware", "endpoint", "microservice"],
    "data_science": ["data", "ml", "ai", "machine-learning", "deep-learning", "pytorch",
                     "tensorflow", "dataset", "notebook", "analytics", "pipeline"],
    "devops_infra": ["docker", "kubernetes", "k8s", "deploy", "terraform", "ansible",
                     "ci", "cd", "infrastructure", "monitoring", "observability"],
    "cli_tools": ["cli", "terminal", "command", "tool", "utility", "script", "automation"],
    "mobile": ["mobile", "android", "ios", "react-native", "flutter", "swift"],
    "game_dev": ["game", "unity", "godot", "phaser", "gaming"],
    "docs_content": ["docs", "blog", "wiki", "knowledge", "content", "tutorial",
                     "guide", "reference"],
    "security": ["security", "crypto", "auth", "encryption", "zero-knowledge", "blockchain",
                 "solidity", "zkp", "attestation"],
    "prototype_experiment": ["prototype", "demo", "poc", "experiment", "sandbox",
                             "playground", "scratch", "hackathon"],
}

# ---- Personality constants ----

_FLEXIBILITY_BATCH_THRESHOLD = 3600  # 1 hour — commits closer than this are same "batch"
_FLEXIBILITY_RESPONSE_WINDOW = 7 * 24 * 3600  # 7 days — max time for "responsive"
_AMBIGUITY_MIN_REPOS = 5  # minimum repos to have confidence in domain diversity
_CHANGE_READINESS_SEGMENTS = [
    (0, 20, "Resistant / Insufficient Data"),
    (21, 50, "Reluctant"),
    (51, 75, "Resilient"),
    (76, 100, "Results"),
]


def _classify_domain(repo) -> str:
    """Classify a repo into a functional domain based on name, description, and language."""
    signals = f"{repo.name} {repo.description or ''} {repo.language or ''}".lower()
    scores: Dict[str, int] = defaultdict(int)

    for domain, keywords in _DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw in signals:
                scores[domain] += 1

    if not scores:
        return "uncategorized"
    return max(scores, key=scores.get)


class FlexibilitySignal:
    """
    Measures how adaptively someone works.

    High flexibility = rapid iteration, quick response to external input,
    evidence of changing approaches when better options appear.

    Mapped ExO attributes: Engagement, Social Technologies
    """
    def __init__(self):
        self.name = "flexibility"

    def extract(self, activity_data: Dict[str, Any]) -> SignalResult:
        commits: list = activity_data.get("commits", [])
        prs: list = activity_data.get("prs", [])
        issues: list = activity_data.get("issues", [])

        repos: list = activity_data.get("repos", [])
        languages = set(r.language for r in repos if r.language)

        if not commits and not prs and not languages:
            return SignalResult(
                name=self.name,
                score=50,  # Neutral default
                confidence=0.1,
                details={"message": "Insufficient activity data"},
            )

        components = []

        # --- Iteration Velocity ---
        # Measure: commits per day over the active period.
        # Rapid iteration = high commit density.
        # Commits are collapsed into batches (same hour = 1 session),
        # then we look at unique day count.
        if len(commits) >= 2:
            sorted_commits = sorted(commits, key=lambda c: c.date)
            active_days = (sorted_commits[-1].date - sorted_commits[0].date).total_seconds() / 86400
            active_days = max(1, active_days)

            # Count commits per active day
            commits_per_day = len(commits) / active_days

            # Scale: < 0.1/day → 10, 1/day → 50, 5+/day → 95
            if commits_per_day >= 5:
                iteration_score = 95
            elif commits_per_day >= 2:
                iteration_score = 75
            elif commits_per_day >= 1:
                iteration_score = 50
            elif commits_per_day >= 0.3:
                iteration_score = 30
            else:
                iteration_score = 10
            components.append(("iteration_velocity", iteration_score, 0.3))
        else:
            components.append(("iteration_velocity", 0, 0.0))

        # --- External Responsiveness ---
        # Measure: time between PR creation and merge.
        # Fast merges = responsive, engaged.
        if prs:
            merged_prs = [pr for pr in prs if pr.merged_at]
            if merged_prs:
                response_times = []
                for pr in merged_prs:
                    delta = (pr.merged_at - pr.created_at).total_seconds()
                    response_times.append(delta)

                avg_response = sum(response_times) / len(response_times)
                # Scale: < 1 day → 100, < 1 week → 70, < 1 month → 40, > 1 month → 10
                if avg_response < 86400:  # 1 day
                    resp_score = 100
                elif avg_response < 604800:  # 1 week
                    resp_score = 70
                elif avg_response < 2592000:  # 1 month
                    resp_score = 40
                else:
                    resp_score = 10
                components.append(("responsiveness", resp_score, 0.3))
            else:
                components.append(("responsiveness", 50, 0.15))  # No merged PRs → neutral
        else:
            components.append(("responsiveness", 0, 0.0))

        # --- Language Switching ---
        # Measure: number of different languages across repos.
        # More languages = more adaptability in tool choice.
        lang_count = len(languages)
        # Scale: 1 lang → 10, 3 langs → 50, 5+ langs → 90
        if lang_count >= 5:
            lang_score = 90
        elif lang_count >= 3:
            lang_score = 50
        elif lang_count >= 2:
            lang_score = 25
        else:
            lang_score = 10
        components.append(("lang_switching", lang_score, 0.25))

        # --- Confidence from data volume ---
        confidence = min(0.9, (len(commits) / 50) * 0.4 + (len(prs) / 20) * 0.3 + (lang_count / 8) * 0.3)

        # Weighted composite
        total_weight = sum(w for _, _, w in components)
        if total_weight > 0:
            score = sum(s * w for _, s, w in components) / total_weight
        else:
            score = 50

        details = {c[0]: round(c[1], 1) for c in components}
        details["total_commits"] = len(commits)

        return SignalResult(
            name=self.name,
            score=round(min(100, max(0, score)), 1),
            confidence=round(confidence, 2),
            details=details,
        )


class AmbiguityComfortSignal:
    """
    Measures comfort with ambiguity and unstructured problems.

    High ambiguity comfort = diverse domains, varied project types,
    non-rigid patterns, exploration over convention.

    Mapped ExO attributes: Experimentation, Autonomy
    """
    def __init__(self):
        self.name = "ambiguity_comfort"

    def extract(self, activity_data: Dict[str, Any]) -> SignalResult:
        repos: list = activity_data.get("repos", [])
        commits: list = activity_data.get("commits", [])

        if not repos:
            return SignalResult(
                name=self.name,
                score=50,
                confidence=0.1,
                details={"message": "No repos found"},
            )

        components = []

        # --- Domain Diversity ---
        # How many different domains does this person work across?
        domains = Counter()
        for repo in repos:
            domain = _classify_domain(repo)
            domains[domain] += 1

        num_domains = len(domains)
        # Scale: 1 domain → 10, 3 domains → 50, 6+ domains → 95
        if num_domains >= 6:
            domain_score = 95
        elif num_domains >= 4:
            domain_score = 65
        elif num_domains >= 2:
            domain_score = 35
        else:
            domain_score = 10
        components.append(("domain_diversity", domain_score, 0.35))

        # --- Project Type Variety ---
        # Fork ratio + description analysis
        owned_repos = [r for r in repos if not r.is_fork]
        fork_ratio = len(owned_repos) / max(1, len(repos))
        # High ownership ratio = initiator. Low = consumer/follower.
        # Both are valid signals — initiators demonstrate higher ambiguity comfort.
        variety_score = fork_ratio * 100
        components.append(("ownership_variety", round(variety_score, 1), 0.2))

        # --- Rigidity Index (inverse) ---
        # Low rigidity = varied commit sizes, varied PR sizes, varied project scopes.
        # We use commit size variation as a proxy.
        if len(commits) >= 5:
            additions = [c.additions for c in commits]
            mean_adds = sum(additions) / len(additions)
            if mean_adds > 0:
                abs_dev = sum(abs(a - mean_adds) for a in additions) / len(additions)
                # Coefficient of variation as rigidity proxy
                cv = abs_dev / mean_adds
                # High CV = high variation = low rigidity = high ambiguity comfort
                # CV > 1 → 90, CV ~0.5 → 50, CV < 0.2 → 10
                rigidity_inverse = min(100, cv * 100)
            else:
                rigidity_inverse = 50
        else:
            rigidity_inverse = 50
        components.append(("non_rigidity", round(rigidity_inverse, 1), 0.25))

        # --- Uncategorized Project Ratio ---
        # Projects that don't fit a clear domain suggest exploration
        uncategorized = domains.get("uncategorized", 0)
        uncat_ratio = uncategorized / max(1, len(repos))
        exploration_score = uncat_ratio * 100
        components.append(("exploration_ratio", round(exploration_score, 1), 0.2))

        # --- Confidence ---
        confidence = min(0.9, len(repos) / _AMBIGUITY_MIN_REPOS)

        # Weighted composite
        total_weight = sum(w for _, _, w in components)
        score = sum(s * w for _, s, w in components) / total_weight if total_weight > 0 else 50

        return SignalResult(
            name=self.name,
            score=round(min(100, max(0, score)), 1),
            confidence=round(confidence, 2),
            details={
                "domains": dict(domains.most_common(5)),
                "num_domains": num_domains,
                "owned_repo_ratio": round(fork_ratio, 2),
                "uncategorized_ratio": round(uncategorized / max(1, len(repos)), 2),
                "non_rigidity": round(rigidity_inverse, 1),
            },
        )


class ChangeReadinessClassifier:
    """
    4Rs Classifier — places a developer on the Resistant → Results spectrum.

    Combines flexibility, ambiguity comfort, and existing signals to
    estimate change readiness and AI adoption likelihood.

    Segments:
        Results (76-100):   Thrives under ambiguity, experiments constantly
        Resilient (51-75):  Adapts quickly with clear guidance
        Reluctant (21-50):  Will change with enough evidence
        Resistant (0-20):   Actively opposed or insufficient data
    """
    def __init__(self):
        self.name = "change_readiness"

    def classify(self, all_scores: Dict[str, SignalResult]) -> Tuple[str, int]:
        """
        Classify into a 4Rs segment based on all signal scores.

        Returns:
            Tuple of (segment_name, score_0_to_100)
        """
        components = []

        # Flexibility → directly maps to Experimentation
        if "flexibility" in all_scores:
            components.append(("flexibility", all_scores["flexibility"].score, 0.25))

        # Ambiguity Comfort → directly maps to tolerance for unknown
        if "ambiguity_comfort" in all_scores:
            components.append(("ambiguity_comfort", all_scores["ambiguity_comfort"].score, 0.25))

        # Existing signals → proxies for ExO attributes
        community_signals = {
            "issue_engagement", "review_patterns", "pr_patterns"
        }
        community_score = 0
        weight = 0
        for sig in community_signals:
            if sig in all_scores:
                community_score += all_scores[sig].score * all_scores[sig].confidence
                weight += 1
        if weight > 0:
            components.append(("community_engagement", community_score / weight, 0.15))

        if "project_ownership" in all_scores:
            components.append(("autonomy", all_scores["project_ownership"].score, 0.15))

        if "language_diversity" in all_scores:
            components.append(("experimentation", all_scores["language_diversity"].score, 0.10))

        if "commit_consistency" in all_scores:
            components.append(("reliability", all_scores["commit_consistency"].score, 0.10))

        total_weight = sum(w for _, _, w in components)
        composite = sum(s * w for _, s, w in components) / total_weight if total_weight > 0 else 0

        score = round(min(100, max(0, composite)), 0)
        segment = "Resistant / Insufficient Data"

        for lo, hi, name in _CHANGE_READINESS_SEGMENTS:
            if lo <= score <= hi:
                segment = name
                break

        return segment, int(score)


# ---- Convenience wrapper ----

def extract_personality(activity_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run all personality inference extractors on GitHub activity data.

    Returns:
        Dict with signal results and 4Rs classification.
    """
    results = {}

    flex = FlexibilitySignal()
    results["flexibility"] = flex.extract(activity_data)

    amb = AmbiguityComfortSignal()
    results["ambiguity_comfort"] = amb.extract(activity_data)

    classifier = ChangeReadinessClassifier()
    segment, score = classifier.classify(results)

    return {
        "signals": results,
        "change_readiness": {
            "segment": segment,
            "score": score,
        },
    }
