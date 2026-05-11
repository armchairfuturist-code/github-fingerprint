"""
Signal Extraction Module
Extracts behavioral signals from GitHub activity data.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter
from dataclasses import dataclass


@dataclass
class SignalResult:
    """Result of a signal extraction."""
    name: str
    score: float
    confidence: float
    details: Dict[str, Any]


class SignalExtractor:
    """Extracts behavioral signals from GitHub activity data."""

    def extract_commit_consistency(self, commits: List[Any]) -> SignalResult:
        """
        Analyze commit consistency as a proxy for work ethic.
        
        Signal: Regular commits indicate consistent work patterns.
        """
        if not commits:
            return SignalResult(
                name="commit_consistency",
                score=0,
                confidence=0,
                details={"message": "No commits found"}
            )

        sorted_commits = sorted(commits, key=lambda c: c.date)
        time_diffs = []
        for i in range(1, len(sorted_commits)):
            diff = (sorted_commits[i].date - sorted_commits[i-1].date).total_seconds()
            time_diffs.append(diff)

        if not time_diffs:
            return SignalResult(
                name="commit_consistency",
                score=50,
                confidence=0.5,
                details={"message": "Only one commit found"}
            )

        avg_diff = sum(time_diffs) / len(time_diffs)
        variance = sum((diff - avg_diff) ** 2 for diff in time_diffs) / len(time_diffs)
        std_dev = variance ** 0.5
        
        if avg_diff > 0:
            consistency_ratio = std_dev / avg_diff
            score = max(0, min(100, 100 * (1 - consistency_ratio)))
        else:
            score = 50

        return SignalResult(
            name="commit_consistency",
            score=score,
            confidence=min(0.9, len(commits) / 100),
            details={
                "total_commits": len(commits),
                "avg_time_between_commits_hours": avg_diff / 3600,
                "std_dev_hours": std_dev / 3600,
            }
        )

    def extract_language_diversity(self, repos: List[Any]) -> SignalResult:
        """
        Analyze language/tool diversity as proxy for role fit.
        
        Signal: Multiple languages indicate adaptability.
        """
        if not repos:
            return SignalResult(
                name="language_diversity",
                score=0,
                confidence=0,
                details={"message": "No repos found"}
            )

        languages = [repo.language for repo in repos if repo.language]
        language_counts = Counter(languages)

        if not language_counts:
            return SignalResult(
                name="language_diversity",
                score=0,
                confidence=0,
                details={"message": "No languages detected"}
            )

        total = sum(language_counts.values())
        entropy = 0
        for count in language_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * (p ** 0.5)

        max_entropy = len(language_counts) ** 0.5
        if max_entropy > 0:
            diversity_score = (entropy / max_entropy) * 100
        else:
            diversity_score = 0

        return SignalResult(
            name="language_diversity",
            score=min(100, diversity_score),
            confidence=min(0.9, len(repos) / 50),
            details={
                "unique_languages": len(language_counts),
                "top_languages": dict(language_counts.most_common(5)),
            }
        )

    def extract_issue_engagement(self, issues: List[Any]) -> SignalResult:
        """
        Analyze issue engagement as proxy for debugging style.
        
        Signal: Active issue engagement indicates collaborative debugging.
        """
        if not issues:
            return SignalResult(
                name="issue_engagement",
                score=0,
                confidence=0,
                details={"message": "No issues found"}
            )

        total_comments = sum(issue.comments for issue in issues)
        closed_issues = sum(1 for issue in issues if issue.state == "CLOSED")
        
        avg_comments = total_comments / len(issues) if issues else 0
        close_rate = closed_issues / len(issues) if issues else 0
        
        engagement_score = (avg_comments * 20) + (close_rate * 50)
        engagement_score = min(100, engagement_score)

        return SignalResult(
            name="issue_engagement",
            score=engagement_score,
            confidence=min(0.9, len(issues) / 30),
            details={
                "total_issues": len(issues),
                "total_comments": total_comments,
                "avg_comments_per_issue": avg_comments,
                "close_rate": close_rate,
            }
        )

    def extract_pr_patterns(self, prs: List[Any]) -> SignalResult:
        """
        Analyze PR patterns as proxy for code quality.
        
        Signal: Balanced PRs indicate thoughtful code changes.
        """
        if not prs:
            return SignalResult(
                name="pr_patterns",
                score=0,
                confidence=0,
                details={"message": "No PRs found"}
            )

        merged_prs = sum(1 for pr in prs if pr.merged_at)
        avg_additions = sum(pr.additions for pr in prs) / len(prs)
        avg_deletions = sum(pr.deletions for pr in prs) / len(prs)
        avg_files = sum(pr.changed_files for pr in prs) / len(prs)
        
        merge_rate = merged_prs / len(prs) if prs else 0
        
        if avg_additions + avg_deletions > 0:
            balance_ratio = min(avg_additions, avg_deletions) / (avg_additions + avg_deletions)
        else:
            balance_ratio = 0
        
        quality_score = (merge_rate * 40) + (balance_ratio * 30) + (min(1, 100 / (avg_files + 1)) * 30)
        quality_score = min(100, quality_score)

        return SignalResult(
            name="pr_patterns",
            score=quality_score,
            confidence=min(0.9, len(prs) / 30),
            details={
                "total_prs": len(prs),
                "merged_prs": merged_prs,
                "avg_additions": avg_additions,
                "avg_deletions": avg_deletions,
                "avg_files_changed": avg_files,
            }
        )

    def extract_project_ownership(self, repos: List[Any], prs: List[Any]) -> SignalResult:
        """
        Analyze project ownership as proxy for solo vs collaborative work.
        
        Signal: Mix of owned and contributed repos indicates collaboration skills.
        """
        if not repos:
            return SignalResult(
                name="project_ownership",
                score=0,
                confidence=0,
                details={"message": "No repos found"}
            )

        owned_repos = sum(1 for repo in repos if not repo.is_fork)
        forked_repos = sum(1 for repo in repos if repo.is_fork)
        
        total_repos = len(repos)
        if total_repos > 0:
            owned_ratio = owned_repos / total_repos
            fork_ratio = forked_repos / total_repos
            
            if owned_ratio > 0 and fork_ratio > 0:
                ownership_score = 50 + (abs(owned_ratio - 0.5) * 20)
            else:
                ownership_score = owned_ratio * 80
        else:
            ownership_score = 0

        return SignalResult(
            name="project_ownership",
            score=min(100, ownership_score),
            confidence=min(0.9, total_repos / 30),
            details={
                "total_repos": total_repos,
                "owned_repos": owned_repos,
                "forked_repos": forked_repos,
            }
        )

    def extract_review_patterns(self, prs: List[Any]) -> SignalResult:
        """
        Analyze code review patterns as proxy for technical depth.
        
        Signal: Participation in code reviews indicates technical communication skills.
        """
        if not prs:
            return SignalResult(
                name="review_patterns",
                score=0,
                confidence=0,
                details={"message": "No PRs found"}
            )

        total_comments = sum(pr.comments + pr.review_comments for pr in prs)
        avg_comments = total_comments / len(prs) if prs else 0
        
        review_score = min(100, avg_comments * 20)

        return SignalResult(
            name="review_patterns",
            score=review_score,
            confidence=min(0.9, len(prs) / 20),
            details={
                "total_prs": len(prs),
                "total_review_comments": total_comments,
                "avg_comments_per_pr": avg_comments,
            }
        )

    def extract_response_time(self, prs: List[Any], issues: List[Any]) -> SignalResult:
        """
        Analyze response time as proxy for velocity.
        
        Signal: Quick merges and issue resolution indicate responsiveness.
        """
        if not prs and not issues:
            return SignalResult(
                name="response_time",
                score=0,
                confidence=0,
                details={"message": "No PRs or issues found"}
            )

        merge_times = []
        for pr in prs:
            if pr.merged_at:
                time_to_merge = (pr.merged_at - pr.created_at).total_seconds()
                merge_times.append(time_to_merge)

        close_times = []
        for issue in issues:
            if issue.closed_at:
                time_to_close = (issue.closed_at - issue.created_at).total_seconds()
                close_times.append(time_to_close)

        all_times = merge_times + close_times
        
        if not all_times:
            return SignalResult(
                name="response_time",
                score=50,
                confidence=0.5,
                details={"message": "No completed PRs or issues"}
            )

        avg_time = sum(all_times) / len(all_times)
        
        capped_time = min(avg_time, 86400 * 7)
        response_score = max(0, 100 - (capped_time / 86400) * 10)

        return SignalResult(
            name="response_time",
            score=response_score,
            confidence=min(0.9, len(all_times) / 20),
            details={
                "avg_response_time_hours": avg_time / 3600,
                "total_completed": len(all_times),
            }
        )

    def extract_readme_quality(self, repos: List[Any]) -> SignalResult:
        """
        Analyze README quality as proxy for communication skills.
        
        Signal: Detailed READMEs indicate good documentation habits.
        """
        if not repos:
            return SignalResult(
                name="readme_quality",
                score=0,
                confidence=0,
                details={"message": "No repos found"}
            )

        repos_with_desc = sum(1 for repo in repos if repo.description)
        
        if repos_with_desc == 0:
            return SignalResult(
                name="readme_quality",
                score=0,
                confidence=0.5,
                details={"message": "No repos with descriptions"}
            )

        desc_lengths = [len(repo.description) for repo in repos if repo.description]
        avg_length = sum(desc_lengths) / len(desc_lengths)
        
        presence_score = (repos_with_desc / len(repos)) * 50
        length_score = min(50, avg_length / 10)
        quality_score = presence_score + length_score

        return SignalResult(
            name="readme_quality",
            score=min(100, quality_score),
            confidence=min(0.9, len(repos) / 30),
            details={
                "repos_with_description": repos_with_desc,
                "avg_description_length": avg_length,
            }
        )

    def extract_all_signals(self, activity_data: Dict[str, Any]) -> Dict[str, SignalResult]:
        """Extract all signals from activity data."""
        repos = activity_data.get("repos", [])
        commits = activity_data.get("commits", [])
        issues = activity_data.get("issues", [])
        prs = activity_data.get("prs", [])

        return {
            "commit_consistency": self.extract_commit_consistency(commits),
            "language_diversity": self.extract_language_diversity(repos),
            "issue_engagement": self.extract_issue_engagement(issues),
            "pr_patterns": self.extract_pr_patterns(prs),
            "project_ownership": self.extract_project_ownership(repos, prs),
            "review_patterns": self.extract_review_patterns(prs),
            "response_time": self.extract_response_time(prs, issues),
            "readme_quality": self.extract_readme_quality(repos),
        }
