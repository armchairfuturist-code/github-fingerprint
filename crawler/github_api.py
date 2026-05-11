"""
GitHub GraphQL API Crawler
Handles fetching user data, repos, commits, issues, and PRs from GitHub.
"""
import os
import time
import json
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import requests
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_URL = "https://api.github.com/graphql"


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
                GITHUB_API_URL,
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
                publicRepos
                followers
                following
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
            public_repos=user_data["publicRepos"],
            followers=user_data["followers"],
            following=user_data["following"],
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

    def get_user_activity(self, username: str) -> Dict[str, Any]:
        """Fetch all user activity data in one call."""
        user = self.get_user(username)
        repos = self.get_user_repos(username, limit=100)

        all_commits = []
        all_issues = []
        all_prs = []

        for repo in repos[:10]:
            owner, repo_name = repo.full_name.split("/")
            all_commits.extend(self.get_repo_commits(owner, repo_name, limit=50))
            all_issues.extend(self.get_repo_issues(owner, repo_name, limit=50))
            all_prs.extend(self.get_repo_prs(owner, repo_name, limit=50))

        return {
            "user": user,
            "repos": repos,
            "commits": all_commits,
            "issues": all_issues,
            "prs": all_prs,
        }


if __name__ == "__main__":
    # Test the client
    client = GitHubAPIClient()
    activity = client.get_user_activity("torvalds")
    print(f"Fetched data for user: {activity['user'].username}")
    print(f"Repos: {len(activity['repos'])}")
    print(f"Commits: {len(activity['commits'])}")
    print(f"Issues: {len(activity['issues'])}")
    print(f"PRs: {len(activity['prs'])}")
