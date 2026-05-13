"""
GitHub GraphQL API Crawler
Handles fetching user data, repos, commits, issues, and PRs from GitHub.
"""
import os
import time
import json
import base64
import re
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import requests
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
GITHUB_REST_URL = "https://api.github.com"

# Well-known CI/CD config file paths
CICD_CONFIG_PATHS: List[str] = [
    ".github/workflows",
    "Jenkinsfile",
    ".circleci/config.yml",
    ".travis.yml",
    ".gitlab-ci.yml",
    "Dockerfile",
    "appveyor.yml",
    ".drone.yml",
    ".buildkite/pipeline.yml",
    ".woodpecker.yml",
    ".github/codeql/codeql-config.yml",
]

# CI/CD config type mapping
CICD_CONFIG_TYPES: Dict[str, str] = {
    ".github/workflows": "github_actions",
    "Jenkinsfile": "jenkins",
    ".circleci/config.yml": "circleci",
    ".travis.yml": "travis",
    ".gitlab-ci.yml": "gitlab_ci",
    "Dockerfile": "docker",
    "appveyor.yml": "appveyor",
    ".drone.yml": "drone",
    ".buildkite/pipeline.yml": "buildkite",
    ".woodpecker.yml": "woodpecker",
    ".github/codeql/codeql-config.yml": "codeql",
}

# Regex for README section headers
README_SECTION_RE = re.compile(r'^##+\s+(.+)$', re.MULTILINE)

# Regex for markdown badges
BADGE_RE = re.compile(r'\[!\[.*?\]\(.*?\)\]\(.*?\)')

# Basic emoji detection pattern
EMOJI_PATTERN = re.compile(
    '[\U0001F600-\U0001F64F'
    '\U0001F300-\U0001F5FF'
    '\U0001F680-\U0001F6FF'
    '\U0001F1E0-\U0001F1FF'
    '\U00002702-\U000027B0'
    '\U000024C2-\U0001F251'
    '\U0001F900-\U0001F9FF'
    '\U0001FA00-\U0001FA6F'
    '\U0001FA70-\U0001FAFF'
    '\U00002600-\U000026FF'
    '\U00002700-\U000027BF]'
)

# Conventional commit patterns
CONVENTIONAL_COMMIT_RE = re.compile(r'^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?!?:\s.*', re.IGNORECASE)


@dataclass
class GitHubUser:
    """Parsed GitHub user data."""
    username: str
    name: Optional[str]
    bio: Optional[str]
    company: Optional[str]
    location: Optional[str]
    created_at: datetime
    updated_at: datetime
    public_repos: int
    followers: int
    following: int


@dataclass
class GitHubRepo:
    """Parsed GitHub repository data."""
    name: str
    full_name: str
    description: Optional[str]
    language: Optional[str]
    stars: int
    forks: int
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    is_fork: bool
    is_private: bool


@dataclass
class GitHubCommit:
    """Parsed GitHub commit data."""
    sha: str
    message: str
    author: str
    date: datetime
    additions: int
    deletions: int


@dataclass
class GitHubIssue:
    """Parsed GitHub issue data."""
    number: int
    title: str
    state: str
    created_at: datetime
    closed_at: Optional[datetime]
    comments: int
    author: str


@dataclass
class GitHubPR:
    """Parsed GitHub pull request data."""
    number: int
    title: str
    state: str
    created_at: datetime
    closed_at: Optional[datetime]
    merged_at: Optional[datetime]
    additions: int
    deletions: int
    changed_files: int
    comments: int
    review_comments: int
    author: str


@dataclass
class GitHubReadme:
    """Parsed GitHub README content from REST API."""
    content: Optional[str]
    size_bytes: int
    encoding: str
    name: str
    detected_sections: List[str] = field(default_factory=list)
    badge_count: int = 0
    has_code_blocks: bool = False
    code_block_count: int = 0
    has_emoji: bool = False
    list_count: int = 0


@dataclass
class GitHubCICDConfig:
    """Detected CI/CD configuration file in a repository."""
    path: str
    config_type: str
    exists: bool
    size_bytes: int = 0
    content_summary: str = ""


@dataclass
class GitHubContributionDay:
    """A single day in the contribution calendar."""
    date: datetime
    contribution_count: int


@dataclass
class GitHubContributionData:
    """Contribution calendar data from GraphQL contributionsCollection."""
    total_contributions: int
    contribution_years: List[int] = field(default_factory=list)
    contribution_days: List[GitHubContributionDay] = field(default_factory=list)
    weeks_with_contributions: int = 0
    total_weeks: int = 0
    first_contribution_date: Optional[datetime] = None
    longest_streak: int = 0
    current_streak: int = 0


# ---------------------------------------------------------------------------
# Serialization helpers for cache (dataclass <-> JSON dict)
# ---------------------------------------------------------------------------

def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string, handling Z suffix."""
    if s is None:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _commit_to_dict(c: GitHubCommit) -> dict:
    return {"sha": c.sha, "message": c.message, "author": c.author,
            "date": c.date.isoformat(), "additions": c.additions, "deletions": c.deletions}


def _commit_from_dict(d: dict) -> GitHubCommit:
    return GitHubCommit(sha=d["sha"], message=d["message"], author=d["author"],
                        date=_parse_dt(d["date"]), additions=d["additions"], deletions=d["deletions"])


def _issue_to_dict(i: GitHubIssue) -> dict:
    return {"number": i.number, "title": i.title, "state": i.state,
            "created_at": i.created_at.isoformat(),
            "closed_at": i.closed_at.isoformat() if i.closed_at else None,
            "comments": i.comments, "author": i.author}


def _issue_from_dict(d: dict) -> GitHubIssue:
    return GitHubIssue(number=d["number"], title=d["title"], state=d["state"],
                       created_at=_parse_dt(d["created_at"]),
                       closed_at=_parse_dt(d["closed_at"]),
                       comments=d["comments"], author=d["author"])


def _pr_to_dict(p: GitHubPR) -> dict:
    return {"number": p.number, "title": p.title, "state": p.state,
            "created_at": p.created_at.isoformat(),
            "closed_at": p.closed_at.isoformat() if p.closed_at else None,
            "merged_at": p.merged_at.isoformat() if p.merged_at else None,
            "additions": p.additions, "deletions": p.deletions,
            "changed_files": p.changed_files, "comments": p.comments,
            "review_comments": p.review_comments, "author": p.author}


def _pr_from_dict(d: dict) -> GitHubPR:
    return GitHubPR(number=d["number"], title=d["title"], state=d["state"],
                    created_at=_parse_dt(d["created_at"]),
                    closed_at=_parse_dt(d["closed_at"]),
                    merged_at=_parse_dt(d["merged_at"]),
                    additions=d["additions"], deletions=d["deletions"],
                    changed_files=d["changed_files"],
                    comments=d["comments"], review_comments=d["review_comments"],
                    author=d["author"])


def _readme_to_dict(r: GitHubReadme) -> dict:
    return {"content": r.content, "size_bytes": r.size_bytes, "encoding": r.encoding,
            "name": r.name, "detected_sections": r.detected_sections,
            "badge_count": r.badge_count, "has_code_blocks": r.has_code_blocks,
            "code_block_count": r.code_block_count, "has_emoji": r.has_emoji,
            "list_count": r.list_count}


def _readme_from_dict(d: dict) -> GitHubReadme:
    return GitHubReadme(content=d.get("content"), size_bytes=d.get("size_bytes", 0),
                        encoding=d.get("encoding", ""), name=d.get("name", ""),
                        detected_sections=d.get("detected_sections", []),
                        badge_count=d.get("badge_count", 0),
                        has_code_blocks=d.get("has_code_blocks", False),
                        code_block_count=d.get("code_block_count", 0),
                        has_emoji=d.get("has_emoji", False),
                        list_count=d.get("list_count", 0))


def _cicd_to_dict(c: GitHubCICDConfig) -> dict:
    return {"path": c.path, "config_type": c.config_type, "exists": c.exists,
            "size_bytes": c.size_bytes, "content_summary": c.content_summary}


def _cicd_from_dict(d: dict) -> GitHubCICDConfig:
    return GitHubCICDConfig(path=d["path"], config_type=d["config_type"],
                            exists=d["exists"], size_bytes=d.get("size_bytes", 0),
                            content_summary=d.get("content_summary", ""))


def _contrib_day_to_dict(d: GitHubContributionDay) -> dict:
    return {"date": d.date.isoformat(), "contribution_count": d.contribution_count}


def _contrib_day_from_dict(d: dict) -> GitHubContributionDay:
    return GitHubContributionDay(date=_parse_dt(d["date"]),
                                 contribution_count=d["contribution_count"])


def _contrib_data_to_dict(c: GitHubContributionData) -> dict:
    return {"total_contributions": c.total_contributions,
            "contribution_years": c.contribution_years,
            "contribution_days": [_contrib_day_to_dict(d) for d in c.contribution_days],
            "weeks_with_contributions": c.weeks_with_contributions,
            "total_weeks": c.total_weeks,
            "first_contribution_date": c.first_contribution_date.isoformat() if c.first_contribution_date else None,
            "longest_streak": c.longest_streak,
            "current_streak": c.current_streak}


def _contrib_data_from_dict(d: dict) -> GitHubContributionData:
    return GitHubContributionData(
        total_contributions=d["total_contributions"],
        contribution_years=d.get("contribution_years", []),
        contribution_days=[_contrib_day_from_dict(dd) for dd in d.get("contribution_days", [])],
        weeks_with_contributions=d.get("weeks_with_contributions", 0),
        total_weeks=d.get("total_weeks", 0),
        first_contribution_date=_parse_dt(d.get("first_contribution_date")),
        longest_streak=d.get("longest_streak", 0),
        current_streak=d.get("current_streak", 0),
    )


# ---------------------------------------------------------------------------
# CrawlCache — incremental per-user cache
# ---------------------------------------------------------------------------

class CrawlCache:
    """Persistent incremental cache for GitHub crawl data.

    Stores per-username JSON files in a configurable directory. Each cache
    entry contains a last-crawled timestamp and per-repo data keyed by
    full_name with pushed_at timestamps. On subsequent crawls, only repos
    whose remote pushed_at is newer than the cached value are re-fetched.

    Cache directory is auto-created on first use.
    """

    def __init__(self, cache_dir: str = ".crawl_cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _cache_path(self, username: str) -> str:
        return os.path.join(self.cache_dir, f"{username}.json")

    # ---- public API ----

    def load(self, username: str) -> Optional[Dict[str, Any]]:
        """Load raw cache entry for *username*. Returns None if absent."""
        path = self._cache_path(username)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, username: str, cache_entry: Dict[str, Any]) -> None:
        """Persist *cache_entry* for *username* to disk."""
        path = self._cache_path(username)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cache_entry, f, indent=2, default=str)

    def has(self, username: str) -> bool:
        """Return True if a cache entry exists for *username*."""
        return os.path.exists(self._cache_path(username))

    # ---- cache entry construction ----

    def new_entry(self) -> Dict[str, Any]:
        """Return a fresh empty cache entry structure."""
        return {
            "last_crawled_at": None,
            "repos": {},
        }

    def build_entry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a crawl result dict into a JSON-serializable cache entry.

        Extracts per-repo deep data (commits, issues, PRs, readme, CI/CD)
        and contributions, keyed by repo full_name with pushed_at.

        The *data* dict should include a ``repos_data`` key — a dict mapping
        each repo full_name to a dict with ``commits``, ``issues``, ``prs``,
        ``readme``, and ``cicd_configs`` keys. If absent, only pushed_at
        and the top-level readmes/cicd_configs are stored (no per-repo
        commit/issue/PR caching).
        """
        now = datetime.now().isoformat()
        repos: Dict[str, GitHubRepo] = data.get("repos", {})
        if isinstance(repos, list):
            repos = {r.full_name: r for r in repos}

        entry = self.new_entry()
        entry["last_crawled_at"] = now

        per_repo = data.get("repos_data", {})
        readmes = data.get("readmes", {})
        cicd_configs = data.get("cicd_configs", {})

        for repo_name, repo in repos.items():
            repo_entry: Dict[str, Any] = {
                "pushed_at": repo.pushed_at.isoformat(),
            }

            # Per-repo deep data from repos_data dict
            rd = per_repo.get(repo_name, {})
            if "commits" in rd:
                repo_entry["commits"] = [_commit_to_dict(c) for c in rd["commits"]]
            if "issues" in rd:
                repo_entry["issues"] = [_issue_to_dict(i) for i in rd["issues"]]
            if "prs" in rd:
                repo_entry["prs"] = [_pr_to_dict(p) for p in rd["prs"]]

            if repo_name in readmes and readmes[repo_name] is not None:
                repo_entry["readme"] = _readme_to_dict(readmes[repo_name])
            if repo_name in cicd_configs:
                repo_entry["cicd_configs"] = [_cicd_to_dict(c) for c in cicd_configs[repo_name]]

            entry["repos"][repo_name] = repo_entry

        # Contributions (user-level, not per-repo)
        contributions = data.get("contributions")
        if contributions is not None:
            entry["contributions"] = _contrib_data_to_dict(contributions)

        return entry

    # ---- stale-repo detection ----

    def get_stale_repos(self, username: str, remote_repos: List[GitHubRepo]) -> tuple:
        """Compare remote *remote_repos* against cached pushed_at values.

        Returns (stale_repo_names: set[str], cache_stats: dict).
        *stale_repo_names* contains full_names of repos whose remote pushed_at
        is newer than the cached value (and repos not yet in cache).
        *cache_stats* reports cached_repo_count, fresh_repo_count, and total.
        """
        cached = self.load(username)
        stale: set = set()
        cached_count = 0
        fresh_count = 0

        if cached is None:
            # No cache at all — all repos are fresh
            stale = {r.full_name for r in remote_repos}
            return stale, {"cached_repos": 0, "fresh_repos": len(stale), "total_repos": len(remote_repos)}

        cached_repos = cached.get("repos", {})
        for repo in remote_repos:
            cached_repo = cached_repos.get(repo.full_name)
            if cached_repo is None:
                # Not in cache — fresh
                stale.add(repo.full_name)
                fresh_count += 1
            else:
                cached_pushed = _parse_dt(cached_repo.get("pushed_at"))
                if cached_pushed is None or repo.pushed_at > cached_pushed:
                    stale.add(repo.full_name)
                    fresh_count += 1
                else:
                    cached_count += 1

        return stale, {"cached_repos": cached_count, "fresh_repos": fresh_count, "total_repos": len(remote_repos)}

    # ---- merge ----

    def merge_deep_data(self, username: str, fresh_data: Dict[str, Any],
                        stale_repo_names: set) -> Dict[str, Any]:
        """Merge fresh deep data with cached data for unchanged repos.

        *fresh_data* already contains freshly-fetched data for stale repos.
        *stale_repo_names* is the set of repos that were re-fetched.
        Returns a dict with merged commits, issues, prs, readmes, cicd_configs,
        and repos_data (for cache serialization).
        """
        cached = self.load(username)
        if cached is None:
            return {
                "commits": fresh_data.get("commits", []),
                "issues": fresh_data.get("issues", []),
                "prs": fresh_data.get("prs", []),
                "readmes": fresh_data.get("readmes", {}),
                "cicd_configs": fresh_data.get("cicd_configs", {}),
                "contributions": fresh_data.get("contributions"),
                "repos_data": fresh_data.get("repos_data", {}),
            }

        cached_repos = cached.get("repos", {})

        # Start with fresh data
        merged_commits = list(fresh_data.get("commits", []))
        merged_issues = list(fresh_data.get("issues", []))
        merged_prs = list(fresh_data.get("prs", []))
        merged_readmes = dict(fresh_data.get("readmes", {}))
        merged_cicd = dict(fresh_data.get("cicd_configs", {}))

        # Start repos_data with fresh data, then add cached for unchanged repos
        merged_repos_data = dict(fresh_data.get("repos_data", {}))

        # For repos NOT in stale set, bring cached data forward
        for repo_name, repo_entry in cached_repos.items():
            if repo_name in stale_repo_names:
                continue  # Fresh data already covers this repo

            # Deserialize cached deep data
            cached_commits = [_commit_from_dict(c) for c in repo_entry.get("commits", [])]
            cached_issues = [_issue_from_dict(i) for i in repo_entry.get("issues", [])]
            cached_prs = [_pr_from_dict(p) for p in repo_entry.get("prs", [])]

            merged_repos_data[repo_name] = {
                "commits": cached_commits,
                "issues": cached_issues,
                "prs": cached_prs,
            }

            merged_commits.extend(cached_commits)
            merged_issues.extend(cached_issues)
            merged_prs.extend(cached_prs)

            if "readme" in repo_entry and repo_entry["readme"] is not None:
                merged_readmes[repo_name] = _readme_from_dict(repo_entry["readme"])
            if "cicd_configs" in repo_entry:
                merged_cicd[repo_name] = [_cicd_from_dict(c) for c in repo_entry["cicd_configs"]]

        # Contributions — if fresh data doesn't have them, use cached
        merged_contributions = fresh_data.get("contributions")
        if merged_contributions is None and "contributions" in (cached or {}):
            merged_contributions = _contrib_data_from_dict(cached["contributions"])

        return {
            "commits": merged_commits,
            "issues": merged_issues,
            "prs": merged_prs,
            "readmes": merged_readmes,
            "cicd_configs": merged_cicd,
            "contributions": merged_contributions,
            "repos_data": merged_repos_data,
        }


class GitHubAPIClient:
    """GitHub GraphQL API client with rate limit handling."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or GITHUB_TOKEN
        if not self.token:
            raise ValueError("GitHub token required. Set GITHUB_TOKEN env var.")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = datetime.now()

    def _execute_graphql(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute GraphQL query with rate limit handling."""
        while True:
            response = requests.post(
                GITHUB_GRAPHQL_URL,
                headers=self.headers,
                json={"query": query, "variables": variables or {}},
            )

            remaining = response.headers.get("X-RateLimit-Remaining")
            reset = response.headers.get("X-RateLimit-Reset")
            if remaining:
                self.rate_limit_remaining = int(remaining)
            if reset:
                self.rate_limit_reset = datetime.fromtimestamp(int(reset))

            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    raise Exception(f"GraphQL error: {data['errors']}")
                return data["data"]

            elif response.status_code == 403 and self.rate_limit_remaining == 0:
                wait_seconds = (self.rate_limit_reset - datetime.now()).total_seconds()
                if wait_seconds > 0:
                    time.sleep(wait_seconds + 1)
                continue

            else:
                response.raise_for_status()

    def get_user(self, username: str) -> GitHubUser:
        """Fetch user data from GitHub."""
        query = """
        query($username: String!) {
            user(login: $username) {
                name
                bio
                company
                location
                createdAt
                updatedAt
                repositories(privacy: PUBLIC) {
                    totalCount
                }
                followers {
                    totalCount
                }
                following {
                    totalCount
                }
            }
        }
        """
        data = self._execute_graphql(query, {"username": username})
        user_data = data["user"]

        return GitHubUser(
            username=username,
            name=user_data.get("name"),
            bio=user_data.get("bio"),
            company=user_data.get("company"),
            location=user_data.get("location"),
            created_at=datetime.fromisoformat(user_data["createdAt"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(user_data["updatedAt"].replace("Z", "+00:00")),
            public_repos=user_data["repositories"]["totalCount"],
            followers=user_data["followers"]["totalCount"],
            following=user_data["following"]["totalCount"],
        )

    def get_user_repos(self, username: str, limit: int = 100) -> List[GitHubRepo]:
        """Fetch user's public repositories."""
        query = """
        query($username: String!, $limit: Int!) {
            user(login: $username) {
                repositories(first: $limit, orderBy: {field: UPDATED_AT, direction: DESC}) {
                    nodes {
                        name
                        nameWithOwner
                        description
                        primaryLanguage {
                            name
                        }
                        stargazerCount
                        forkCount
                        createdAt
                        updatedAt
                        pushedAt
                        isFork
                        isPrivate
                    }
                }
            }
        }
        """
        data = self._execute_graphql(query, {"username": username, "limit": limit})
        repos_data = data["user"]["repositories"]["nodes"]

        repos = []
        for repo in repos_data:
            repos.append(
                GitHubRepo(
                    name=repo["name"],
                    full_name=repo["nameWithOwner"],
                    description=repo.get("description"),
                    language=repo["primaryLanguage"]["name"] if repo["primaryLanguage"] else None,
                    stars=repo["stargazerCount"],
                    forks=repo["forkCount"],
                    created_at=datetime.fromisoformat(repo["createdAt"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(repo["updatedAt"].replace("Z", "+00:00")),
                    pushed_at=datetime.fromisoformat(repo["pushedAt"].replace("Z", "+00:00")),
                    is_fork=repo["isFork"],
                    is_private=repo["isPrivate"],
                )
            )

        return repos

    def get_repo_commits(self, owner: str, repo: str, limit: int = 100) -> List[GitHubCommit]:
        """Fetch commits for a repository."""
        query = """
        query($owner: String!, $repo: String!, $limit: Int!) {
            repository(owner: $owner, name: $repo) {
                defaultBranchRef {
                    target {
                        ... on Commit {
                            history(first: $limit) {
                                nodes {
                                    oid
                                    message
                                    author {
                                        name
                                        email
                                    }
                                    committedDate
                                    additions
                                    deletions
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        data = self._execute_graphql(query, {"owner": owner, "repo": repo, "limit": limit})

        if not data["repository"]["defaultBranchRef"]:
            return []

        commits_data = data["repository"]["defaultBranchRef"]["target"]["history"]["nodes"]
        commits = []

        for commit in commits_data:
            commits.append(
                GitHubCommit(
                    sha=commit["oid"],
                    message=commit["message"],
                    author=commit["author"]["name"] or commit["author"]["email"],
                    date=datetime.fromisoformat(commit["committedDate"].replace("Z", "+00:00")),
                    additions=commit["additions"],
                    deletions=commit["deletions"],
                )
            )

        return commits

    def get_repo_issues(self, owner: str, repo: str, limit: int = 100) -> List[GitHubIssue]:
        """Fetch issues for a repository."""
        query = """
        query($owner: String!, $repo: String!, $limit: Int!) {
            repository(owner: $owner, name: $repo) {
                issues(first: $limit, orderBy: {field: CREATED_AT, direction: DESC}) {
                    nodes {
                        number
                        title
                        state
                        createdAt
                        closedAt
                        comments {
                            totalCount
                        }
                        author {
                            login
                        }
                    }
                }
            }
        }
        """
        data = self._execute_graphql(query, {"owner": owner, "repo": repo, "limit": limit})
        issues_data = data["repository"]["issues"]["nodes"]

        issues = []
        for issue in issues_data:
            issues.append(
                GitHubIssue(
                    number=issue["number"],
                    title=issue["title"],
                    state=issue["state"],
                    created_at=datetime.fromisoformat(issue["createdAt"].replace("Z", "+00:00")),
                    closed_at=datetime.fromisoformat(issue["closedAt"].replace("Z", "+00:00")) if issue["closedAt"] else None,
                    comments=issue["comments"]["totalCount"],
                    author=issue["author"]["login"] if issue["author"] else "unknown",
                )
            )

        return issues

    def get_repo_prs(self, owner: str, repo: str, limit: int = 100) -> List[GitHubPR]:
        """Fetch pull requests for a repository."""
        query = """
        query($owner: String!, $repo: String!, $limit: Int!) {
            repository(owner: $owner, name: $repo) {
                pullRequests(first: $limit, orderBy: {field: CREATED_AT, direction: DESC}) {
                    nodes {
                        number
                        title
                        state
                        createdAt
                        closedAt
                        mergedAt
                        additions
                        deletions
                        changedFiles
                        comments {
                            totalCount
                        }
                        reviewComments {
                            totalCount
                        }
                        author {
                            login
                        }
                    }
                }
            }
        }
        """
        data = self._execute_graphql(query, {"owner": owner, "repo": repo, "limit": limit})
        prs_data = data["repository"]["pullRequests"]["nodes"]

        prs = []
        for pr in prs_data:
            prs.append(
                GitHubPR(
                    number=pr["number"],
                    title=pr["title"],
                    state=pr["state"],
                    created_at=datetime.fromisoformat(pr["createdAt"].replace("Z", "+00:00")),
                    closed_at=datetime.fromisoformat(pr["closedAt"].replace("Z", "+00:00")) if pr["closedAt"] else None,
                    merged_at=datetime.fromisoformat(pr["mergedAt"].replace("Z", "+00:00")) if pr["mergedAt"] else None,
                    additions=pr["additions"],
                    deletions=pr["deletions"],
                    changed_files=pr["changedFiles"],
                    comments=pr["comments"]["totalCount"],
                    review_comments=pr["reviewComments"]["totalCount"],
                    author=pr["author"]["login"] if pr["author"] else "unknown",
                )
            )

        return prs

    def _execute_rest(self, path: str) -> Optional[Dict]:
        """Execute REST API GET request with auth and rate-limit backoff.

        Returns the parsed JSON response, or None for 404 (not found).
        Raises on other HTTP errors.
        """
        url = f"{GITHUB_REST_URL}{path}"
        while True:
            response = requests.get(url, headers=self.headers)

            remaining = response.headers.get("X-RateLimit-Remaining")
            reset = response.headers.get("X-RateLimit-Reset")
            if remaining:
                self.rate_limit_remaining = int(remaining)
            if reset:
                self.rate_limit_reset = datetime.fromtimestamp(int(reset))

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            elif response.status_code == 403 and self.rate_limit_remaining == 0:
                wait_seconds = (self.rate_limit_reset - datetime.now()).total_seconds()
                if wait_seconds > 0:
                    time.sleep(wait_seconds + 1)
                continue
            else:
                response.raise_for_status()

    def get_repo_readme(self, owner: str, repo: str) -> Optional[GitHubReadme]:
        """Fetch README content via REST API.

        Returns a GitHubReadme with decoded content and parsed metadata,
        or None if the repo has no README.
        """
        data = self._execute_rest(f"/repos/{owner}/{repo}/readme")
        if data is None:
            return None

        # Decode base64 content
        content_bytes = base64.b64decode(data["content"])
        content = content_bytes.decode("utf-8", errors="replace")

        # Parse README structure
        sections = README_SECTION_RE.findall(content)
        badge_count = len(BADGE_RE.findall(content))
        code_fences = content.count("```")
        code_block_count = code_fences // 2 if code_fences >= 2 else 0
        has_code_blocks = code_block_count > 0
        has_emoji = bool(EMOJI_PATTERN.search(content))
        list_count = content.count("\n- ") + content.count("\n* ")

        return GitHubReadme(
            content=content,
            size_bytes=data.get("size", 0),
            encoding=data.get("encoding", ""),
            name=data.get("name", "README.md"),
            detected_sections=sections,
            badge_count=badge_count,
            has_code_blocks=has_code_blocks,
            code_block_count=code_block_count,
            has_emoji=has_emoji,
            list_count=list_count,
        )

    def get_user_contributions(self, username: str) -> Optional[GitHubContributionData]:
        """Fetch contribution calendar data via GraphQL contributionsCollection.

        Returns contribution counts per day for the last year along with
        streak data and contribution years.
        """
        query = """
        query($username: String!) {
            user(login: $username) {
                contributionsCollection {
                    contributionCalendar {
                        totalContributions
                        weeks {
                            contributionDays {
                                contributionCount
                                date
                            }
                        }
                    }
                               }
                contributionYears
            }
        }
        """
        data = self._execute_graphql(query, {"username": username})
        if not data or not data.get("user"):
            return None

        user_data = data["user"]
        contribution_years = user_data.get("contributionYears", [])

        calendar = user_data.get("contributionsCollection", {}).get("contributionCalendar", {})
        total_contributions = calendar.get("totalContributions", 0)
        weeks_data = calendar.get("weeks", [])

        # Flatten contribution days
        contribution_days = []
        for week in weeks_data:
            for day in week.get("contributionDays", []):
                contribution_days.append(GitHubContributionDay(
                    date=datetime.fromisoformat(day["date"]),
                    contribution_count=day["contributionCount"],
                ))

        total_weeks = len(weeks_data)
        weeks_with_contributions = sum(
            1 for week in weeks_data
            if any(d["contributionCount"] > 0 for d in week.get("contributionDays", []))
        )

        # Calculate streaks
        first_contribution_date = None
        longest_streak = 0
        current_streak = 0
        ongoing_streak = 0

        # Sort days chronologically for streak calculation
        sorted_days = sorted(contribution_days, key=lambda d: d.date)
        if sorted_days:
            first_contribution_date = sorted_days[0].date

            # Calculate longest streak
            temp_streak = 0
            for day in sorted_days:
                if day.contribution_count > 0:
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 0

            # Calculate current streak (trailing from today, going backward)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            for day in reversed(sorted_days):
                if day.date > today:
                    continue
                if day.contribution_count > 0:
                    ongoing_streak += 1
                else:
                    break

        return GitHubContributionData(
            total_contributions=total_contributions,
            contribution_years=contribution_years,
            contribution_days=contribution_days,
            weeks_with_contributions=weeks_with_contributions,
            total_weeks=total_weeks,
            first_contribution_date=first_contribution_date,
            longest_streak=longest_streak,
            current_streak=ongoing_streak,
        )

    def get_repo_cicd_configs(self, owner: str, repo: str) -> List[GitHubCICDConfig]:
        """Detect CI/CD configuration files in a repository.

        Checks well-known CI/CD config file paths via the REST Contents API.
        Returns a list of detected configs (found and not-found).
        """
        configs = []
        for path in CICD_CONFIG_PATHS:
            config_type = CICD_CONFIG_TYPES.get(path, "unknown")
            data = self._execute_rest(f"/repos/{owner}/{repo}/contents/{path}")

            if data is None:
                configs.append(GitHubCICDConfig(
                    path=path,
                    config_type=config_type,
                    exists=False,
                ))
                continue

            # For directory listings (like .github/workflows), count entries
            if isinstance(data, list):
                configs.append(GitHubCICDConfig(
                    path=path,
                    config_type=config_type,
                    exists=True,
                    size_bytes=0,
                    content_summary=f"directory with {len(data)} file(s)",
                ))
            else:
                # Single file
                name = data.get("name", path.split("/")[-1])
                size = data.get("size", 0)
                summary = f"{name} ({size} bytes)"
                configs.append(GitHubCICDConfig(
                    path=path,
                    config_type=config_type,
                    exists=True,
                    size_bytes=size,
                    content_summary=summary,
                ))

        return configs

    def get_user_activity(self, username: str, use_cache: bool = False,
                          cache: Optional[CrawlCache] = None) -> Dict[str, Any]:
        """Fetch all user activity data in one call.

        When *use_cache* is True, an incremental CrawlCache is used:
        - Only repos whose remote pushed_at is newer than cached are re-fetched
        - Cached deep data for unchanged repos is merged in
        - The result includes a ``cache_stats`` key with hit/miss counts

        Pass a pre-configured *cache* instance, or a default CrawlCache() is created.
        """
        user = self.get_user(username)
        repos = self.get_user_repos(username, limit=100)

        if use_cache:
            cc = cache or CrawlCache()
            stale_repo_names, cache_stats = cc.get_stale_repos(username, repos)
        else:
            stale_repo_names = {r.full_name for r in repos[:10]}
            cache_stats = None

        all_commits = []
        all_issues = []
        all_prs = []
        readmes = {}
        cicd_configs = {}
        repos_data = {}  # repo full_name -> {commits, issues, prs}

        # Only crawl repos that are stale (or all when not caching)
        for repo in repos[:10]:
            if use_cache and repo.full_name not in stale_repo_names:
                continue  # Will be filled from cache during merge

            owner, repo_name = repo.full_name.split("/")
            repo_commits = self.get_repo_commits(owner, repo_name, limit=50)
            repo_issues = self.get_repo_issues(owner, repo_name, limit=50)
            repo_prs = self.get_repo_prs(owner, repo_name, limit=50)

            all_commits.extend(repo_commits)
            all_issues.extend(repo_issues)
            all_prs.extend(repo_prs)

            repos_data[repo.full_name] = {
                "commits": repo_commits,
                "issues": repo_issues,
                "prs": repo_prs,
            }

            readme = self.get_repo_readme(owner, repo_name)
            if readme is not None:
                readmes[repo.full_name] = readme

            cicd = self.get_repo_cicd_configs(owner, repo_name)
            cicd_configs[repo.full_name] = cicd

        contributions = self.get_user_contributions(username)

        # Build our results
        result = {
            "user": user,
            "repos": repos,
            "commits": all_commits,
            "issues": all_issues,
            "prs": all_prs,
            "readmes": readmes,
            "cicd_configs": cicd_configs,
            "contributions": contributions,
            "repos_data": repos_data,  # for cache serialization
        }

        if use_cache:
            # Merge cached data for repos we skipped
            merged = cc.merge_deep_data(username, result, stale_repo_names)
            result.update(merged)

            # Persist updated cache
            cache_entry = cc.build_entry(result)
            cc.save(username, cache_entry)

            # Attach stats
            result["cache_stats"] = cache_stats
        else:
            result["cache_stats"] = None

        return result


if __name__ == "__main__":
    # Test the client
    client = GitHubAPIClient()
    activity = client.get_user_activity("torvalds")
    print(f"Fetched data for user: {activity['user'].username}")
    print(f"Repos: {len(activity['repos'])}")
    print(f"Commits: {len(activity['commits'])}")
    print(f"Issues: {len(activity['issues'])}")
    print(f"PRs: {len(activity['prs'])}")
