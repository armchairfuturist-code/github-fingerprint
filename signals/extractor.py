"""
Signal Extraction Module
Extracts behavioral signals from GitHub activity data.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter
from dataclasses import dataclass

from crawler.github_api import CONVENTIONAL_COMMIT_RE, CICD_CONFIG_TYPES


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

    def extract_readme_quality(self, repos: List[Any],
                                readmes: Optional[Dict[str, Any]] = None) -> SignalResult:
        """
        Analyze README content quality as proxy for communication skills.

        When actual README content is available (via the ``readmes`` dict mapping
        repo full_name to GitHubReadme objects), scores based on:
          - README presence ratio across repos
          - Character count (content length)
          - Section headers count
          - Code block count
          - List count
          - Badge count
          - Emoji presence

        Falls back to description-only scoring when no README data is available.

        Returns a 0-100 score where higher = more complete, well-structured READMEs.
        """
        if not repos:
            return SignalResult(
                name="readme_quality",
                score=0,
                confidence=0,
                details={"message": "No repos found"}
            )

        readmes = readmes or {}

        if not readmes:
            # Fallback: description-only scoring
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
                confidence=min(0.7, len(repos) / 30),
                details={
                    "repos_with_description": repos_with_desc,
                    "avg_description_length": avg_length,
                    "mode": "description_fallback",
                }
            )

        # Analyze actual README content
        repos_with_readme = 0
        total_chars = 0
        total_sections = 0
        total_code_blocks = 0
        total_lists = 0
        total_badges = 0
        repos_with_emoji = 0

        for repo in repos:
            readme = readmes.get(repo.full_name)
            if readme is None or readme.content is None:
                continue
            repos_with_readme += 1
            total_chars += len(readme.content)
            total_sections += len(readme.detected_sections)
            total_code_blocks += readme.code_block_count
            total_lists += readme.list_count
            total_badges += readme.badge_count
            if readme.has_emoji:
                repos_with_emoji += 1

        if repos_with_readme == 0:
            return SignalResult(
                name="readme_quality",
                score=0,
                confidence=0.5,
                details={"message": "No repos with README content"}
            )

        total_repos = len(repos)

        # Presence sub-score (0-30): what fraction of repos have actual READMEs
        presence_score = (repos_with_readme / total_repos) * 30

        # Structure sub-score (0-30): sections + code blocks + lists
        avg_sections = total_sections / repos_with_readme
        avg_code_blocks = total_code_blocks / repos_with_readme
        avg_lists = total_lists / repos_with_readme

        structure_score = min(30, (avg_sections * 5) + (avg_code_blocks * 3) + (avg_lists * 1.5))

        # Richness sub-score (0-25): content length + badges
        avg_chars = total_chars / repos_with_readme
        avg_badges = total_badges / repos_with_readme
        chars_score = min(15, avg_chars / 66.7)  # ~1000 chars = 15 pts
        badge_score = min(10, avg_badges * 2)      # 5 badges = 10 pts
        richness_score = chars_score + badge_score

        # Polish sub-score (0-15): emoji usage signals engagement
        emoji_ratio = repos_with_emoji / repos_with_readme if repos_with_readme > 0 else 0
        polish_score = emoji_ratio * 15

        quality_score = presence_score + structure_score + richness_score + polish_score

        return SignalResult(
            name="readme_quality",
            score=min(100, quality_score),
            confidence=min(0.9, repos_with_readme / 20),
            details={
                "repos_with_readme": repos_with_readme,
                "avg_char_count": round(avg_chars, 1),
                "avg_sections": round(avg_sections, 1),
                "avg_code_blocks": round(avg_code_blocks, 1),
                "avg_lists": round(avg_lists, 1),
                "avg_badges": round(avg_badges, 1),
                "emoji_ratio": round(emoji_ratio, 2),
                "mode": "readme_content",
            }
        )

    def extract_commit_semantics(self, commits: List[Any]) -> SignalResult:
        """
        Analyze commit message semantics as proxy for code quality and
        communication discipline.

        Evaluates:
          - Conventional commit pattern usage (feat:, fix:, docs:, etc.)
          - Average message length (descriptive messages score higher)
          - Multi-line message ratio (body indicates thoroughness)
          - Imperative mood usage (messages starting with a verb)

        Returns a 0-100 score where higher = structured, descriptive commits.
        """
        if not commits:
            return SignalResult(
                name="commit_semantics",
                score=0,
                confidence=0,
                details={"message": "No commits found"}
            )

        total = len(commits)
        conventional_count = 0
        multi_line_count = 0
        total_length = 0

        # Common imperative verbs for heuristic detection
        imperative_verbs = {
            "add", "remove", "fix", "update", "change", "implement", "refactor",
            "rename", "move", "delete", "create", "merge", "bump", "upgrade",
            "downgrade", "revert", "introduce", "extract", "replace", "migrate",
            "enable", "disable", "improve", "simplify", "clean", "bump",
            "bootstrap", "initialize", "convert", "handle", "support",
        }
        imperative_count = 0

        for commit in commits:
            message = commit.message
            total_length += len(message)

            # Check conventional commit pattern
            if CONVENTIONAL_COMMIT_RE.match(message):
                conventional_count += 1

            # Check multi-line (has body after subject line)
            if "\n" in message.strip():
                lines = [l for l in message.split("\n") if l.strip()]
                if len(lines) > 1:
                    multi_line_count += 1

            # Check imperative mood: first word of subject is a known imperative verb
            subject = message.split("\n")[0].strip()
            first_word = subject.split(":")[-1].strip().split()[0].lower().rstrip(".,!;")
            if first_word in imperative_verbs:
                imperative_count += 1

        # Conventional commit ratio (0-30)
        conventional_ratio = conventional_count / total
        conventional_score = conventional_ratio * 30

        # Average message length (0-25): short messages get partial, 50+ chars = full
        avg_length = total_length / total
        length_score = min(25, (avg_length / 50) * 25)

        # Multi-line ratio (0-25): body indicates thorough descriptions
        multi_line_ratio = multi_line_count / total
        multi_line_score = multi_line_ratio * 25

        # Imperative mood ratio (0-20)
        imperative_ratio = imperative_count / total
        imperative_score = imperative_ratio * 20

        semantics_score = conventional_score + length_score + multi_line_score + imperative_score

        return SignalResult(
            name="commit_semantics",
            score=min(100, semantics_score),
            confidence=min(0.9, total / 100),
            details={
                "total_commits": total,
                "conventional_commit_ratio": round(conventional_ratio, 2),
                "conventional_breakdown": self._conventional_breakdown(commits),
                "avg_message_length": round(avg_length, 1),
                "multi_line_ratio": round(multi_line_ratio, 2),
                "imperative_mood_ratio": round(imperative_ratio, 2),
            }
        )

    def _conventional_breakdown(self, commits: List[Any]) -> Dict[str, int]:
        """Count conventional commit types across commits."""
        counts: Dict[str, int] = {}
        for commit in commits:
            m = CONVENTIONAL_COMMIT_RE.match(commit.message)
            if m:
                prefix = m.group(1).lower()
                counts[prefix] = counts.get(prefix, 0) + 1
        return dict(sorted(counts.items()))

    def extract_cicd_maturity(self,
                               cicd_configs: Optional[Dict[str, List[Any]]] = None,
                               repos: Optional[List[Any]] = None) -> SignalResult:
        """
        Analyze CI/CD maturity based on configuration files detected across repos.

        Scoring:
          - GitHub Actions = 20pts per repo with it
          - Other CI systems = 15pts each per repo
          - Dockerfile = 10pts per repo
          - Higher scores for multiple CI types across repos
          - Normalized to 0-100 based on diversity and prevalence

        Returns a 0-100 score where higher = more sophisticated CI/CD usage.
        """
        if not cicd_configs or not repos:
            return SignalResult(
                name="cicd_maturity",
                score=0,
                confidence=0,
                details={"message": "No CI/CD data available"}
            )

        # Build per-repo: set of unique CI types found
        repo_ci_types: Dict[str, set] = {}
        for repo_full_name, configs in cicd_configs.items():
            found_types = {
                c.config_type for c in configs
                if c.exists
            }
            if found_types:
                repo_ci_types[repo_full_name] = found_types

        total_repos = len(repos)
        if total_repos == 0:
            return SignalResult(
                name="cicd_maturity",
                score=0,
                confidence=0,
                details={"message": "No repos found"}
            )

        repos_with_ci = len(repo_ci_types)
        if repos_with_ci == 0:
            return SignalResult(
                name="cicd_maturity",
                score=0,
                confidence=0.5,
                details={"message": "No CI/CD detected in any repo"}
            )

        # Score components
        prevalence_score = (repos_with_ci / total_repos) * 30

        # Count unique CI types across all repos
        all_types: set = set()
        type_frequency: Counter = Counter()
        for types in repo_ci_types.values():
            all_types.update(types)
            type_frequency.update(types)

        # Diversity: how many distinct CI types are used
        # 0-30: 0 types = 0, 4+ types = 30
        diversity_score = min(30, len(all_types) * 7.5)

        # Depth: weighted per-type score
        # GitHub Actions = 20, other CI = 15, Docker = 10
        type_scores = {
            "github_actions": 20,
            "docker": 10,
        }
        other_ci_types = {t for t in all_types if t not in type_scores}
        depth_score = 0
        if type_frequency.get("github_actions", 0) > 0:
            depth_score += 20
        if type_frequency.get("docker", 0) > 0:
            depth_score += 10
        # Each additional CI type beyond GA + Docker
        for t in other_ci_types:
            depth_score += 15

        # Cap depth at 40
        depth_score = min(40, depth_score)

        maturity_score = prevalence_score + diversity_score + depth_score

        return SignalResult(
            name="cicd_maturity",
            score=min(100, maturity_score),
            confidence=min(0.85, 0.3 + (repos_with_ci / max(total_repos, 1)) * 0.5),
            details={
                "repos_with_ci": repos_with_ci,
                "total_repos": total_repos,
                "ci_type_count": len(all_types),
                "ci_types_found": sorted(all_types),
                "type_frequency": dict(type_frequency.most_common()),
            }
        )

    def extract_contribution_consistency(self,
                                          contributions: Optional[Any] = None,
                                          commits: Optional[List[Any]] = None) -> SignalResult:
        """
        Analyze contribution consistency using contribution calendar data.

        Evaluates:
          - Regular vs bursty contribution patterns
          - Long gaps (30+ days of inactivity)
          - Spread of contributions across days/weeks

        Higher scores = consistent, ongoing contributions.
        Lower scores = sporadic or bursty patterns with long gaps.
        """
        has_contrib_data = contributions is not None and hasattr(contributions, 'contribution_days')

        # Fall back to commit-based analysis if no contribution calendar data
        if not has_contrib_data and not commits:
            return SignalResult(
                name="contribution_consistency",
                score=0,
                confidence=0,
                details={"message": "No contribution data available"}
            )

        if has_contrib_data:
            days = contributions.contribution_days
            if not days:
                return SignalResult(
                    name="contribution_consistency",
                    score=0,
                    confidence=0.5,
                    details={"message": "Empty contribution calendar"}
                )

            sorted_days = sorted(days, key=lambda d: d.date)
            total_days = len(sorted_days)
            days_with_contributions = sum(1 for d in sorted_days if d.contribution_count > 0)
            zero_days = total_days - days_with_contributions

            # Activity ratio (0-35)
            activity_ratio = days_with_contributions / total_days if total_days > 0 else 0
            activity_score = activity_ratio * 35

            # Detect long gaps (0-35): penalty for 30+ day gaps
            gap_penalty = 0
            max_gap = 0
            current_gap = 0
            for day in sorted_days:
                if day.contribution_count == 0:
                    current_gap += 1
                    max_gap = max(max_gap, current_gap)
                else:
                    current_gap = 0

            if max_gap >= 30:
                gap_penalty = 35  # Full penalty for 30+ day gap
            elif max_gap >= 14:
                gap_penalty = 25   # Partial for 2-week gap
            elif max_gap >= 7:
                gap_penalty = 15   # Small for 1-week gap
            gap_score = 35 - gap_penalty

            # Consistency spread (0-30): weekly consistency
            weekly_counts: Counter = Counter()
            for day in sorted_days:
                week_key = day.date.isocalendar()[1]  # ISO week number
                weekly_counts[week_key] += day.contribution_count

            if weekly_counts:
                weekly_values = list(weekly_counts.values())
                mean_weekly = sum(weekly_values) / len(weekly_values)
                if mean_weekly > 0:
                    variance = sum((v - mean_weekly) ** 2 for v in weekly_values) / len(weekly_values)
                    weekly_cv = (variance ** 0.5) / mean_weekly  # Coefficient of variation
                    # Lower CV = more consistent. Score inversely.
                    spread_score = max(0, 30 * (1 - min(weekly_cv, 2.0) / 2.0))
                else:
                    spread_score = 0
            else:
                spread_score = 0

            consistency_score = activity_score + gap_score + spread_score

            return SignalResult(
                name="contribution_consistency",
                score=min(100, consistency_score),
                confidence=min(0.9, 0.4 + activity_ratio * 0.5),
                details={
                    "total_days": total_days,
                    "days_with_contributions": days_with_contributions,
                    "activity_ratio": round(activity_ratio, 3),
                    "max_gap_days": max_gap,
                    "longest_streak": contributions.longest_streak,
                    "current_streak": contributions.current_streak,
                    "weekly_cv": round(weekly_cv, 3) if weekly_counts and mean_weekly > 0 else None,
                    "mode": "contribution_calendar",
                }
            )
        else:
            # Fallback: commit-based consistency estimate
            sorted_commits = sorted(commits, key=lambda c: c.date)
            if len(sorted_commits) < 2:
                return SignalResult(
                    name="contribution_consistency",
                    score=25,
                    confidence=0.3,
                    details={"message": "Too few commits for pattern analysis",
                             "mode": "commit_fallback"}
                )

            # Analyze commit date spread
            first_date = sorted_commits[0].date
            last_date = sorted_commits[-1].date
            span_days = (last_date - first_date).total_seconds() / 86400

            if span_days < 1:
                return SignalResult(
                    name="contribution_consistency",
                    score=30,
                    confidence=0.3,
                    details={"message": "All commits in a single day — likely burst",
                             "mode": "commit_fallback"}
                )

            commits_per_day = len(sorted_commits) / max(span_days, 1)
            # Higher density = more bursty, lower = more sparse
            # Ideal: 0.5-3 commits/day = consistent contributor
            if 0.5 <= commits_per_day <= 3:
                density_score = 60
            elif commits_per_day < 0.5:
                density_score = 30 + (commits_per_day / 0.5) * 30  # 30-60
            else:
                density_score = max(10, 60 - (commits_per_day - 3) * 5)  # 60 down to 10

            # Gap detection on commit dates
            gaps = []
            for i in range(1, len(sorted_commits)):
                gap = (sorted_commits[i].date - sorted_commits[i - 1].date).total_seconds() / 86400
                gaps.append(gap)

            max_commit_gap = max(gaps) if gaps else 0
            if max_commit_gap >= 30:
                gap_score_fb = 20
            elif max_commit_gap >= 14:
                gap_score_fb = 35
            else:
                gap_score_fb = 50

            consistency_score_fb = int((density_score + gap_score_fb) / 2)

            return SignalResult(
                name="contribution_consistency",
                score=min(100, consistency_score_fb),
                confidence=min(0.5, 0.2 + len(commits) / 200),
                details={
                    "total_commits": len(commits),
                    "span_days": round(span_days, 1),
                    "commits_per_day": round(commits_per_day, 2),
                    "max_commit_gap_days": round(max_commit_gap, 1),
                    "mode": "commit_fallback",
                }
            )

    def extract_ai_usage_patterns(self, commits: List[Any]) -> SignalResult:
        """
        Analyze commit patterns for potential AI-assisted vs organic development.

        Evaluates:
          - Timing clusters: are commits evenly distributed or clumped in short windows?
          - Message style uniformity: standard deviation of message length
          - Conventional commit consistency: very high consistency can indicate AI
          - Burst detection: many commits in very short timeframes

        Organic patterns show moderate variance in message style and timing.
        Highly uniform patterns with burst clusters may indicate AI assistance.

        Returns a 0-100 score where:
          - Higher (60+) = natural, organic patterns
          - Middle (30-60) = mixed or unclear
          - Lower (0-30) = highly uniform/bursty, potentially AI-assisted
        """
        if not commits:
            return SignalResult(
                name="ai_usage_patterns",
                score=50,  # Neutral — no signal
                confidence=0,
                details={"message": "No commits to analyze"}
            )

        total = len(commits)
        sorted_commits = sorted(commits, key=lambda c: c.date)

        # ---- 1. Message style uniformity (0-35) ----
        # Organic: moderate variance (std_dev 10-30 chars)
        # AI: very low variance (highly uniform messages) or very high variance
        msg_lengths = [len(c.message) for c in commits]
        avg_length = sum(msg_lengths) / len(msg_lengths)
        length_variance = sum((l - avg_length) ** 2 for l in msg_lengths) / len(msg_lengths)
        length_std = length_variance ** 0.5

        if length_std < 5:
            # Extremely uniform — suspicious
            style_score = 5
        elif length_std < 10:
            # Very uniform — potentially AI
            style_score = 20
        elif length_std < 30:
            # Moderate variance — organic sweet spot
            style_score = 35
        elif length_std < 50:
            # Higher variance — still organic
            style_score = 25
        else:
            # Very high variance — could be mix of AI and manual
            style_score = 15

        # ---- 2. Timing cluster analysis (0-35) ----
        if total >= 2:
            time_diffs = []
            for i in range(1, len(sorted_commits)):
                diff = (sorted_commits[i].date - sorted_commits[i - 1].date).total_seconds()
                time_diffs.append(diff)

            avg_diff = sum(time_diffs) / len(time_diffs)
            diff_variance = sum((d - avg_diff) ** 2 for d in time_diffs) / len(time_diffs)
            diff_std = diff_variance ** 0.5

            # Detect burst clusters: commits within 60 seconds of each other
            burst_clusters = 0
            current_cluster_size = 1
            for diff in time_diffs:
                if diff < 60:
                    current_cluster_size += 1
                else:
                    if current_cluster_size > 3:
                        burst_clusters += current_cluster_size
                    current_cluster_size = 1
            if current_cluster_size > 3:
                burst_clusters += current_cluster_size

            # Few bursts with consistent pacing = organic
            # Many bursts with very uniform diffs = potential AI
            burst_ratio = burst_clusters / total if total > 0 else 0

            if burst_ratio > 0.5 and diff_std < avg_diff * 0.5:
                # High burst ratio + very consistent pacing = AI pattern
                timing_score = 5
            elif burst_ratio > 0.3:
                # Some bursty clusters but not extreme
                timing_score = 20
            elif burst_ratio < 0.1 and avg_diff > 3600:
                # Few bursts, spread over hours = organic
                timing_score = 35
            elif burst_ratio < 0.2:
                timing_score = 30
            else:
                timing_score = 25
        else:
            timing_score = 20
            burst_ratio = 0

        # ---- 3. Conventional commit consistency (0-30) ----
        conventional_count = sum(
            1 for c in commits if CONVENTIONAL_COMMIT_RE.match(c.message)
        )
        conventional_ratio = conventional_count / total if total > 0 else 0

        # Extremely high conventional commit ratio (>95%) with low variance is unusual
        # Moderate (40-80%) is more organic
        if conventional_ratio > 0.95 and total >= 5:
            cc_score = 10  # Suspiciously consistent
        elif conventional_ratio > 0.80:
            cc_score = 20  # Good but possibly AI
        elif conventional_ratio > 0.40:
            cc_score = 30  # Sweet spot — organic range
        elif conventional_ratio > 0.10:
            cc_score = 25
        else:
            cc_score = 20  # Very few conventional commits

        ai_score = style_score + timing_score + cc_score

        # Confidence: more data = more reliable
        confidence = min(0.85, 0.2 + (total / 100) * 0.5)

        return SignalResult(
            name="ai_usage_patterns",
            score=min(100, ai_score),
            confidence=confidence,
            details={
                "total_commits": total,
                "msg_length_std": round(length_std, 1),
                "avg_msg_length": round(avg_length, 1),
                "burst_cluster_ratio": round(burst_ratio, 3),
                "conventional_commit_ratio": round(conventional_ratio, 2),
                "avg_time_between_commits_mins": round(avg_diff / 60, 1) if total >= 2 else None,
            }
        )

    def extract_all_signals(self, activity_data: Dict[str, Any]) -> Dict[str, SignalResult]:
        """Extract all signals from activity data."""
        repos = activity_data.get("repos", [])
        commits = activity_data.get("commits", [])
        issues = activity_data.get("issues", [])
        prs = activity_data.get("prs", [])
        readmes = activity_data.get("readmes", {})
        cicd_configs = activity_data.get("cicd_configs", {})
        contributions = activity_data.get("contributions")

        return {
            "commit_consistency": self.extract_commit_consistency(commits),
            "language_diversity": self.extract_language_diversity(repos),
            "issue_engagement": self.extract_issue_engagement(issues),
            "pr_patterns": self.extract_pr_patterns(prs),
            "project_ownership": self.extract_project_ownership(repos, prs),
            "review_patterns": self.extract_review_patterns(prs),
            "response_time": self.extract_response_time(prs, issues),
            "readme_quality": self.extract_readme_quality(repos, readmes),
            "commit_semantics": self.extract_commit_semantics(commits),
            "cicd_maturity": self.extract_cicd_maturity(cicd_configs, repos),
            "contribution_consistency": self.extract_contribution_consistency(contributions, commits),
            "ai_usage_patterns": self.extract_ai_usage_patterns(commits),
        }
