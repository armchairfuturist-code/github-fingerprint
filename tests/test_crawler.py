"""
Unit tests for the GitHub API crawler.
"""
import pytest
import base64
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
from crawler.github_api import (
    GitHubUser, GitHubRepo, GitHubCommit, GitHubIssue, GitHubPR,
    GitHubReadme, GitHubCICDConfig, GitHubContributionDay,
    GitHubContributionData, GitHubAPIClient, CrawlCache,
)


def _mock_response(status_code=200, json_data=None, headers=None):
    """Create a mock requests.Response with given attributes."""
    resp = Mock()
    resp.status_code = status_code
    if json_data is not None:
        resp.json.return_value = json_data
    resp.headers = headers or {}
    return resp


class TestGitHubDataClasses:
    """Test data classes for GitHub entities."""

    def test_github_user_creation(self):
        user = GitHubUser(
            username="testuser",
            name="Test User",
            bio="Test bio",
            company="Test Corp",
            location="Test City",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            public_repos=10,
            followers=100,
            following=50
        )
        assert user.username == "testuser"
        assert user.name == "Test User"
        assert user.public_repos == 10

    def test_github_repo_creation(self):
        repo = GitHubRepo(
            name="test-repo",
            full_name="user/test-repo",
            description="Test description",
            language="Python",
            stars=100,
            forks=50,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            pushed_at=datetime.now(),
            is_fork=False,
            is_private=False
        )
        assert repo.name == "test-repo"
        assert repo.language == "Python"
        assert repo.stars == 100

    def test_github_commit_creation(self):
        commit = GitHubCommit(
            sha="abc123",
            message="Test commit",
            author="testuser",
            date=datetime.now(),
            additions=10,
            deletions=5
        )
        assert commit.sha == "abc123"
        assert commit.additions == 10
        assert commit.deletions == 5

    def test_github_issue_creation(self):
        issue = GitHubIssue(
            number=1,
            title="Test issue",
            state="CLOSED",
            created_at=datetime.now(),
            closed_at=datetime.now(),
            comments=5,
            author="testuser"
        )
        assert issue.number == 1
        assert issue.state == "CLOSED"
        assert issue.comments == 5

    def test_github_pr_creation(self):
        pr = GitHubPR(
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
            author="testuser"
        )
        assert pr.number == 1
        assert pr.state == "MERGED"
        assert pr.changed_files == 2

    def test_github_readme_creation(self):
        readme = GitHubReadme(
            content="# My Project\n\n## Installation\n\n```bash\nnpm install\n```\n\n## Usage\n\n- Item 1\n- Item 2",
            size_bytes=100,
            encoding="base64",
            name="README.md",
            detected_sections=["Installation", "Usage"],
            badge_count=0,
            has_code_blocks=True,
            code_block_count=1,
            has_emoji=False,
            list_count=2,
        )
        assert readme.name == "README.md"
        assert len(readme.detected_sections) == 2
        assert readme.has_code_blocks is True
        assert readme.code_block_count == 1

    def test_github_readme_with_content_none(self):
        readme = GitHubReadme(
            content=None,
            size_bytes=0,
            encoding="",
            name="README.md",
        )
        assert readme.content is None
        assert readme.size_bytes == 0

    def test_github_cicd_config_creation(self):
        config = GitHubCICDConfig(
            path=".github/workflows/ci.yml",
            config_type="github_actions",
            exists=True,
            size_bytes=2048,
            content_summary="CI workflow file",
        )
        assert config.path == ".github/workflows/ci.yml"
        assert config.config_type == "github_actions"
        assert config.exists is True

    def test_github_cicd_config_not_found(self):
        config = GitHubCICDConfig(
            path="Jenkinsfile",
            config_type="jenkins",
            exists=False,
        )
        assert config.exists is False
        assert config.size_bytes == 0

    def test_github_contribution_day_creation(self):
        day = GitHubContributionDay(
            date=datetime(2024, 1, 15),
            contribution_count=5,
        )
        assert day.date.year == 2024
        assert day.contribution_count == 5

    def test_github_contribution_data_creation(self):
        data = GitHubContributionData(
            total_contributions=500,
            contribution_years=[2022, 2023, 2024],
            contribution_days=[GitHubContributionDay(datetime(2024, 1, 1), 3)],
            weeks_with_contributions=40,
            total_weeks=52,
            first_contribution_date=datetime(2022, 3, 1),
            longest_streak=30,
            current_streak=5,
        )
        assert data.total_contributions == 500
        assert len(data.contribution_years) == 3
        assert data.longest_streak == 30


class TestGitHubAPIClient:
    """Test GitHub API client."""

    def test_client_initialization_with_token(self):
        client = GitHubAPIClient(token="fake_token")
        assert client.token == "fake_token"
        assert "Authorization" in client.headers

    @patch('crawler.github_api.GITHUB_TOKEN', None)
    def test_client_initialization_without_token_raises_error(self):
        with pytest.raises(ValueError, match="GitHub token required"):
            GitHubAPIClient(token=None)

    @patch('crawler.github_api.requests.post')
    def test_execute_graphql_success(self, mock_post):
        mock_post.return_value = _mock_response(
            status_code=200,
            json_data={"data": {"user": {"name": "Test"}}},
            headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"},
        )

        client = GitHubAPIClient(token="fake_token")
        result = client._execute_graphql("query { user { name } }")

        assert result == {"user": {"name": "Test"}}
        mock_post.assert_called_once()

    @patch('crawler.github_api.requests.post')
    def test_execute_graphql_rate_limit_handling(self, mock_post):
        mock_post.side_effect = [
            _mock_response(
                status_code=403,
                json_data={},
                headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1234567890"},
            ),
            _mock_response(
                status_code=200,
                json_data={"data": {"user": {"name": "Test"}}},
                headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"},
            ),
        ]

        client = GitHubAPIClient(token="fake_token")
        client.rate_limit_remaining = 0
        client.rate_limit_reset = datetime(2020, 1, 1)

        result = client._execute_graphql("query { user { name } }")
        assert result == {"user": {"name": "Test"}}

    @patch('crawler.github_api.requests.post')
    def test_get_user(self, mock_post):
        mock_post.return_value = _mock_response(
            status_code=200,
            json_data={
                "data": {
                    "user": {
                        "name": "Test User",
                        "bio": "Test bio",
                        "company": "Test Corp",
                        "location": "Test City",
                        "createdAt": "2020-01-01T00:00:00Z",
                        "updatedAt": "2020-01-02T00:00:00Z",
                        "publicRepos": 10,
                        "followers": 100,
                        "following": 50,
                    }
                }
            },
            headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"},
        )

        client = GitHubAPIClient(token="fake_token")
        user = client.get_user("testuser")

        assert user.username == "testuser"
        assert user.name == "Test User"
        assert user.public_repos == 10

    @patch('crawler.github_api.requests.post')
    def test_get_user_repos(self, mock_post):
        mock_post.return_value = _mock_response(
            status_code=200,
            json_data={
                "data": {
                    "user": {
                        "repositories": {
                            "nodes": [
                                {
                                    "name": "test-repo",
                                    "nameWithOwner": "user/test-repo",
                                    "description": "Test",
                                    "primaryLanguage": {"name": "Python"},
                                    "stargazerCount": 100,
                                    "forkCount": 50,
                                    "createdAt": "2020-01-01T00:00:00Z",
                                    "updatedAt": "2020-01-02T00:00:00Z",
                                    "pushedAt": "2020-01-03T00:00:00Z",
                                    "isFork": False,
                                    "isPrivate": False,
                                }
                            ]
                        }
                    }
                }
            },
            headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"},
        )

        client = GitHubAPIClient(token="fake_token")
        repos = client.get_user_repos("testuser")

        assert len(repos) == 1
        assert repos[0].name == "test-repo"
        assert repos[0].language == "Python"

    @patch('crawler.github_api.requests.post')
    def test_get_repo_commits(self, mock_post):
        mock_post.return_value = _mock_response(
            status_code=200,
            json_data={
                "data": {
                    "repository": {
                        "defaultBranchRef": {
                            "target": {
                                "history": {
                                    "nodes": [
                                        {
                                            "oid": "abc123",
                                            "message": "Test commit",
                                            "author": {"name": "Test User", "email": "test@example.com"},
                                            "committedDate": "2020-01-01T00:00:00Z",
                                            "additions": 10,
                                            "deletions": 5,
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            },
            headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"},
        )

        client = GitHubAPIClient(token="fake_token")
        commits = client.get_repo_commits("owner", "repo")

        assert len(commits) == 1
        assert commits[0].sha == "abc123"
        assert commits[0].additions == 10

    @patch('crawler.github_api.requests.post')
    def test_get_repo_issues(self, mock_post):
        mock_post.return_value = _mock_response(
            status_code=200,
            json_data={
                "data": {
                    "repository": {
                        "issues": {
                            "nodes": [
                                {
                                    "number": 1,
                                    "title": "Test issue",
                                    "state": "CLOSED",
                                    "createdAt": "2020-01-01T00:00:00Z",
                                    "closedAt": "2020-01-02T00:00:00Z",
                                    "comments": {"totalCount": 5},
                                    "author": {"login": "testuser"},
                                }
                            ]
                        }
                    }
                }
            },
            headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"},
        )

        client = GitHubAPIClient(token="fake_token")
        issues = client.get_repo_issues("owner", "repo")

        assert len(issues) == 1
        assert issues[0].number == 1
        assert issues[0].state == "CLOSED"

    @patch('crawler.github_api.requests.post')
    def test_get_repo_prs(self, mock_post):
        mock_post.return_value = _mock_response(
            status_code=200,
            json_data={
                "data": {
                    "repository": {
                        "pullRequests": {
                            "nodes": [
                                {
                                    "number": 1,
                                    "title": "Test PR",
                                    "state": "MERGED",
                                    "createdAt": "2020-01-01T00:00:00Z",
                                    "closedAt": "2020-01-02T00:00:00Z",
                                    "mergedAt": "2020-01-02T00:00:00Z",
                                    "additions": 10,
                                    "deletions": 5,
                                    "changedFiles": 2,
                                    "comments": {"totalCount": 3},
                                    "reviewComments": {"totalCount": 2},
                                    "author": {"login": "testuser"},
                                }
                            ]
                        }
                    }
                }
            },
            headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"},
        )

        client = GitHubAPIClient(token="fake_token")
        prs = client.get_repo_prs("owner", "repo")

        assert len(prs) == 1
        assert prs[0].number == 1
        assert prs[0].state == "MERGED"
        assert prs[0].changed_files == 2

    @patch('crawler.github_api.requests.get')
    def test_execute_rest_success(self, mock_get):
        mock_get.return_value = _mock_response(
            status_code=200,
            json_data={"name": "README.md", "size": 100},
            headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"},
        )

        client = GitHubAPIClient(token="fake_token")
        result = client._execute_rest("/repos/owner/repo/readme")

        assert result == {"name": "README.md", "size": 100}

    @patch('crawler.github_api.requests.get')
    def test_execute_rest_404(self, mock_get):
        mock_get.return_value = _mock_response(
            status_code=404,
            json_data={},
            headers={},
        )

        client = GitHubAPIClient(token="fake_token")
        result = client._execute_rest("/repos/owner/repo/nonexistent")

        assert result is None

    @patch('crawler.github_api.requests.get')
    def test_get_repo_readme_success(self, mock_get):
        readme_content = (
            "# My Project\n\n"
            "## Installation\n\n"
            "```bash\npip install my-project\n```\n\n"
            "## Usage\n\n"
            "- Step 1\n- Step 2\n\n"
            "[![Build Status](https://img.shields.io/badge/build-passing-green)](https://example.com)\n"
        )
        encoded_content = base64.b64encode(readme_content.encode()).decode()

        mock_get.return_value = _mock_response(
            status_code=200,
            json_data={
                "name": "README.md",
                "size": len(readme_content),
                "encoding": "base64",
                "content": encoded_content,
            },
            headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"},
        )

        client = GitHubAPIClient(token="fake_token")
        readme = client.get_repo_readme("owner", "my-project")

        assert readme is not None
        assert readme.name == "README.md"
        assert "Installation" in readme.detected_sections
        assert "Usage" in readme.detected_sections
        assert readme.has_code_blocks is True
        assert readme.code_block_count == 1
        assert readme.badge_count == 1
        assert readme.list_count == 2
        assert readme.size_bytes == len(readme_content)

    @patch('crawler.github_api.requests.get')
    def test_get_repo_readme_not_found(self, mock_get):
        mock_get.return_value = _mock_response(
            status_code=404,
            json_data={},
            headers={},
        )

        client = GitHubAPIClient(token="fake_token")
        readme = client.get_repo_readme("owner", "no-readme-repo")

        assert readme is None

    @patch('crawler.github_api.requests.get')
    def test_get_repo_readme_with_emoji(self, mock_get):
        content = "# Cool Project 🚀\n\n## Features\n\nThis project is awesome! ✨\n"
        encoded = base64.b64encode(content.encode()).decode()

        mock_get.return_value = _mock_response(
            status_code=200,
            json_data={
                "name": "README.md",
                "size": len(content),
                "encoding": "base64",
                "content": encoded,
            },
            headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"},
        )

        client = GitHubAPIClient(token="fake_token")
        readme = client.get_repo_readme("owner", "cool-project")

        assert readme is not None
        assert readme.has_emoji is True

    @patch('crawler.github_api.requests.post')
    def test_get_user_contributions_success(self, mock_post):
        mock_post.return_value = _mock_response(
            status_code=200,
            json_data={
                "data": {
                    "user": {
                        "contributionsCollection": {
                            "contributionCalendar": {
                                "totalContributions": 350,
                                "weeks": [
                                    {
                                        "contributionDays": [
                                            {"contributionCount": 5, "date": "2024-01-01"},
                                            {"contributionCount": 3, "date": "2024-01-02"},
                                            {"contributionCount": 0, "date": "2024-01-03"},
                                        ]
                                    },
                                    {
                                        "contributionDays": [
                                            {"contributionCount": 2, "date": "2024-01-08"},
                                            {"contributionCount": 0, "date": "2024-01-09"},
                                            {"contributionCount": 7, "date": "2024-01-10"},
                                        ]
                                    },
                                ]
                            }
                        },
                        "contributionYears": [2022, 2023, 2024],
                    }
                }
            },
            headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"},
        )

        client = GitHubAPIClient(token="fake_token")
        contrib = client.get_user_contributions("testuser")

        assert contrib is not None
        assert contrib.total_contributions == 350
        assert contrib.contribution_years == [2022, 2023, 2024]
        assert contrib.total_weeks == 2
        assert contrib.weeks_with_contributions == 2
        assert len(contrib.contribution_days) == 6

    @patch('crawler.github_api.requests.post')
    def test_get_user_contributions_no_data(self, mock_post):
        mock_post.return_value = _mock_response(
            status_code=200,
            json_data={
                "data": {
                    "user": {
                        "contributionsCollection": {
                            "contributionCalendar": {
                                "totalContributions": 0,
                                "weeks": [],
                            }
                        },
                        "contributionYears": [],
                    }
                }
            },
            headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"},
        )

        client = GitHubAPIClient(token="fake_token")
        contrib = client.get_user_contributions("inactive_user")

        assert contrib is not None
        assert contrib.total_contributions == 0
        assert contrib.total_weeks == 0

    @patch('crawler.github_api.requests.get')
    def test_get_repo_cicd_configs_found(self, mock_get):
        """Test CI/CD detection returns configs for found files."""

        def mock_side_effect(url, headers=None):
            if ".github/workflows" in url:
                return _mock_response(
                    status_code=200,
                    json_data=[
                        {"name": "ci.yml", "type": "file", "size": 500},
                        {"name": "deploy.yml", "type": "file", "size": 300},
                    ],
                    headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"},
                )
            elif "Jenkinsfile" in url:
                return _mock_response(
                    status_code=200,
                    json_data={"name": "Jenkinsfile", "size": 200, "type": "file"},
                    headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"},
                )
            else:
                return _mock_response(status_code=404, json_data={}, headers={})

        mock_get.side_effect = mock_side_effect

        client = GitHubAPIClient(token="fake_token")
        configs = client.get_repo_cicd_configs("owner", "cicd-project")

        found = [c for c in configs if c.exists]
        not_found = [c for c in configs if not c.exists]

        assert len(found) == 2
        assert len(not_found) > 0
        assert any(c.config_type == "github_actions" for c in found)
        assert any(c.config_type == "jenkins" for c in found)

    @patch('crawler.github_api.requests.get')
    def test_get_repo_cicd_configs_none_found(self, mock_get):
        """Test CI/CD detection when nothing is found."""
        mock_get.return_value = _mock_response(status_code=404, json_data={}, headers={})

        client = GitHubAPIClient(token="fake_token")
        configs = client.get_repo_cicd_configs("owner", "no-cicd")

        assert len(configs) > 0
        assert all(c.exists is False for c in configs)

    @patch('crawler.github_api.requests.get')
    @patch('crawler.github_api.requests.post')
    def test_get_user_activity_includes_deep_data(self, mock_post, mock_get):
        """Verify get_user_activity returns deep pipeline keys."""
        client = GitHubAPIClient(token="fake_token")

        # Mock individual methods to verify deep data keys flow through
        client.get_user = Mock(return_value=GitHubUser(
            username="testuser", name="T", bio=None, company=None,
            location=None, created_at=datetime.now(), updated_at=datetime.now(),
            public_repos=1, followers=0, following=0,
        ))
        client.get_user_repos = Mock(return_value=[
            GitHubRepo(
                name="test-repo", full_name="user/test-repo",
                description="Test", language="Python",
                stars=0, forks=0,
                created_at=datetime.now(), updated_at=datetime.now(),
                pushed_at=datetime.now(), is_fork=False, is_private=False,
            )
        ])
        client.get_repo_commits = Mock(return_value=[])
        client.get_repo_issues = Mock(return_value=[])
        client.get_repo_prs = Mock(return_value=[])

        # Deep data mocks
        client.get_repo_readme = Mock(return_value=GitHubReadme(
            content="# Test\n\n## Install\n\nTest content",
            size_bytes=40, encoding="base64", name="README.md",
            detected_sections=["Install"], badge_count=0,
            has_code_blocks=False, code_block_count=0,
            has_emoji=False, list_count=0,
        ))
        client.get_repo_cicd_configs = Mock(return_value=[
            GitHubCICDConfig(
                path="Jenkinsfile", config_type="jenkins",
                exists=True, size_bytes=200,
                content_summary="Jenkinsfile (200 bytes)",
            ),
        ])
        client.get_user_contributions = Mock(return_value=GitHubContributionData(
            total_contributions=100,
            contribution_years=[2024],
            weeks_with_contributions=1,
            total_weeks=1,
            longest_streak=5,
            current_streak=3,
        ))

        activity = client.get_user_activity("testuser")

        assert "readmes" in activity
        assert "cicd_configs" in activity
        assert "contributions" in activity
        assert "user/test-repo" in activity["readmes"]
        assert activity["contributions"] is not None
        assert activity["contributions"].total_contributions == 100

        # Verify deep data methods were called
        client.get_repo_readme.assert_called_once()
        client.get_repo_cicd_configs.assert_called_once()
        client.get_user_contributions.assert_called_once_with("testuser")


class TestCrawlCache:
    """Test the incremental crawl cache."""

    # ---- helpers ----

    @staticmethod
    def _make_repo(full_name: str, pushed_at: datetime) -> GitHubRepo:
        return GitHubRepo(
            name=full_name.split("/")[1],
            full_name=full_name,
            description="Test repo",
            language="Python",
            stars=5, forks=2,
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 2),
            pushed_at=pushed_at,
            is_fork=False,
            is_private=False,
        )

    # ---- init and I/O ----

    def test_init_creates_directory(self, tmp_path):
        cache_dir = tmp_path / "my_cache"
        cache = CrawlCache(str(cache_dir))
        assert cache_dir.exists()

    def test_save_and_load_roundtrip(self, tmp_path):
        cache = CrawlCache(str(tmp_path))
        entry = {"last_crawled_at": "2024-01-01T00:00:00", "repos": {}}
        cache.save("testuser", entry)

        assert cache.has("testuser")
        loaded = cache.load("testuser")
        assert loaded == entry

    def test_load_nonexistent_returns_none(self, tmp_path):
        cache = CrawlCache(str(tmp_path))
        assert cache.load("nonexistent") is None
        assert not cache.has("nonexistent")

    def test_new_entry_structure(self, tmp_path):
        cache = CrawlCache(str(tmp_path))
        entry = cache.new_entry()
        assert "last_crawled_at" in entry
        assert entry["last_crawled_at"] is None
        assert "repos" in entry
        assert entry["repos"] == {}

    # ---- build_entry ----

    def test_build_entry_includes_last_crawled_at(self, tmp_path):
        cache = CrawlCache(str(tmp_path))
        repo = self._make_repo("user/repo1", datetime(2024, 6, 1))
        data = {"repos": [repo], "commits": [], "issues": [], "prs": [],
                "readmes": {}, "cicd_configs": {}, "contributions": None}
        entry = cache.build_entry(data)
        assert entry["last_crawled_at"] is not None
        assert "user/repo1" in entry["repos"]
        assert entry["repos"]["user/repo1"]["pushed_at"] is not None

    def test_build_entry_with_deep_data(self, tmp_path):
        cache = CrawlCache(str(tmp_path))
        repo = self._make_repo("user/repo1", datetime(2024, 6, 1))
        commit = GitHubCommit(sha="abc", message="fix: bug", author="user",
                              date=datetime(2024, 6, 1), additions=10, deletions=5)
        issue = GitHubIssue(number=1, title="Bug", state="OPEN",
                            created_at=datetime(2024, 6, 1), closed_at=None,
                            comments=3, author="user")
        pr = GitHubPR(number=1, title="PR", state="OPEN", created_at=datetime(2024, 6, 1),
                      closed_at=None, merged_at=None, additions=20, deletions=10,
                      changed_files=3, comments=2, review_comments=1, author="user")
        readme = GitHubReadme(content="# Test", size_bytes=10, encoding="base64",
                              name="README.md", detected_sections=["Intro"],
                              badge_count=1, has_code_blocks=False, code_block_count=0,
                              has_emoji=False, list_count=0)
        cicd = GitHubCICDConfig(path=".github/workflows/ci.yml", config_type="github_actions",
                                exists=True, size_bytes=500, content_summary="CI workflow")

        data = {
            "repos": [repo],
            "commits": [commit],
            "issues": [issue],
            "prs": [pr],
            "readmes": {"user/repo1": readme},
            "cicd_configs": {"user/repo1": [cicd]},
            "contributions": None,
            "repos_data": {"user/repo1": {"commits": [commit], "issues": [issue], "prs": [pr]}},
        }
        entry = cache.build_entry(data)
        repo_entry = entry["repos"]["user/repo1"]

        assert "commits" in repo_entry
        assert len(repo_entry["commits"]) == 1
        assert repo_entry["commits"][0]["sha"] == "abc"

        assert "issues" in repo_entry
        assert len(repo_entry["issues"]) == 1
        assert repo_entry["issues"][0]["number"] == 1

        assert "prs" in repo_entry
        assert len(repo_entry["prs"]) == 1
        assert repo_entry["prs"][0]["number"] == 1

        assert "readme" in repo_entry
        assert repo_entry["readme"]["name"] == "README.md"

        assert "cicd_configs" in repo_entry
        assert len(repo_entry["cicd_configs"]) == 1
        assert repo_entry["cicd_configs"][0]["config_type"] == "github_actions"

    def test_build_entry_with_contributions(self, tmp_path):
        cache = CrawlCache(str(tmp_path))
        repo = self._make_repo("user/repo1", datetime(2024, 6, 1))
        contrib = GitHubContributionData(
            total_contributions=500,
            contribution_years=[2023, 2024],
            contribution_days=[GitHubContributionDay(datetime(2024, 1, 1), 5)],
            weeks_with_contributions=40,
            total_weeks=52,
            first_contribution_date=datetime(2022, 3, 1),
            longest_streak=30,
            current_streak=5,
        )
        data = {"repos": [repo], "commits": [], "issues": [], "prs": [],
                "readmes": {}, "cicd_configs": {}, "contributions": contrib}
        entry = cache.build_entry(data)
        assert "contributions" in entry
        assert entry["contributions"]["total_contributions"] == 500

    # ---- get_stale_repos ----

    def test_stale_all_fresh_when_no_cache(self, tmp_path):
        cache = CrawlCache(str(tmp_path))
        repos = [self._make_repo("user/repo1", datetime(2024, 6, 1))]
        stale, stats = cache.get_stale_repos("new_user", repos)
        assert stale == {"user/repo1"}
        assert stats["cached_repos"] == 0
        assert stats["fresh_repos"] == 1
        assert stats["total_repos"] == 1

    def test_stale_all_cached_when_up_to_date(self, tmp_path):
        cache = CrawlCache(str(tmp_path))
        earlier = datetime(2024, 5, 1)

        # Seed cache
        cache_entry = cache.new_entry()
        cache_entry["repos"]["user/repo1"] = {"pushed_at": earlier.isoformat()}
        cache.save("testuser", cache_entry)

        # Same pushed_at repos
        repos = [self._make_repo("user/repo1", earlier)]
        stale, stats = cache.get_stale_repos("testuser", repos)
        assert len(stale) == 0
        assert stats["cached_repos"] == 1
        assert stats["fresh_repos"] == 0

    def test_stale_mixed_cached_and_fresh(self, tmp_path):
        cache = CrawlCache(str(tmp_path))
        earlier = datetime(2024, 5, 1)
        later = datetime(2024, 6, 1)

        # Seed cache with repo1 at earlier time
        cache_entry = cache.new_entry()
        cache_entry["repos"]["user/repo1"] = {"pushed_at": earlier.isoformat()}
        cache.save("testuser", cache_entry)

        # Remote has repo1 (same ts) and repo2 (new)
        repos = [
            self._make_repo("user/repo1", earlier),
            self._make_repo("user/repo2", later),
        ]
        stale, stats = cache.get_stale_repos("testuser", repos)
        assert stale == {"user/repo2"}
        assert stats["cached_repos"] == 1
        assert stats["fresh_repos"] == 1
        assert stats["total_repos"] == 2

    def test_stale_detects_newer_remote(self, tmp_path):
        cache = CrawlCache(str(tmp_path))
        cached_ts = datetime(2024, 5, 1)
        remote_ts = datetime(2024, 6, 1)

        cache_entry = cache.new_entry()
        cache_entry["repos"]["user/repo1"] = {"pushed_at": cached_ts.isoformat()}
        cache.save("testuser", cache_entry)

        repos = [self._make_repo("user/repo1", remote_ts)]
        stale, stats = cache.get_stale_repos("testuser", repos)
        assert stale == {"user/repo1"}
        assert stats["cached_repos"] == 0
        assert stats["fresh_repos"] == 1

    # ---- merge_deep_data ----

    def test_merge_with_no_cache(self, tmp_path):
        cache = CrawlCache(str(tmp_path))
        fresh = {
            "commits": [GitHubCommit("a", "msg", "u", datetime(2024, 1, 1), 1, 0)],
            "issues": [],
            "prs": [],
            "readmes": {},
            "cicd_configs": {},
            "contributions": None,
        }
        merged = cache.merge_deep_data("new_user", fresh, set())
        assert len(merged["commits"]) == 1

    def test_merge_cached_with_fresh(self, tmp_path):
        cache = CrawlCache(str(tmp_path))
        earlier = datetime(2024, 5, 1)
        later = datetime(2024, 6, 1)

        # Seed cache with repo1 data
        cache_entry = cache.new_entry()
        cache_entry["repos"]["user/repo1"] = {
            "pushed_at": earlier.isoformat(),
            "commits": [{"sha": "cached", "message": "old commit", "author": "user",
                         "date": earlier.isoformat(), "additions": 5, "deletions": 2}],
            "issues": [{"number": 1, "title": "old bug", "state": "CLOSED",
                        "created_at": earlier.isoformat(), "closed_at": earlier.isoformat(),
                        "comments": 1, "author": "user"}],
            "prs": [],
        }
        cache_entry["repos"]["user/repo2"] = {
            "pushed_at": earlier.isoformat(),
            "readme": {"content": "# Old README", "size_bytes": 20, "encoding": "base64",
                       "name": "README.md", "detected_sections": [], "badge_count": 0,
                       "has_code_blocks": False, "code_block_count": 0,
                       "has_emoji": False, "list_count": 0},
        }
        cache.save("testuser", cache_entry)

        # Fresh data for repo1 only (repo2 not in stale set)
        fresh = {
            "commits": [GitHubCommit("new", "new commit", "user", later, 10, 3)],
            "issues": [],
            "prs": [],
            "readmes": {},
            "cicd_configs": {},
            "contributions": None,
            "repos_data": {"user/repo1": {"commits": [GitHubCommit("new", "new commit", "user", later, 10, 3)], "issues": [], "prs": []}},
        }

        merged = cache.merge_deep_data("testuser", fresh, {"user/repo1"})

        # repo1 is stale — has fresh commit; repo2 is cached — keeps old data
        commit_messages = {c.message for c in merged["commits"]}
        assert "new commit" in commit_messages  # fresh data for stale repo1
        assert "old commit" not in commit_messages  # repo1 cached data was replaced
        assert len(merged["commits"]) == 1  # only 1 fresh commit, not 2

        # repo2 is cached — its issue from cache should be excluded (repo2 has no issues in cache)
        assert len(merged["issues"]) == 0  # fresh issues was empty for both repos
        assert len(merged["prs"]) == 0

        # repo2's cached readme should be preserved
        assert "user/repo2" in merged["readmes"]
        assert merged["readmes"]["user/repo2"].content == "# Old README"

        # repos_data should have repo1 data from fresh (stale), repo2 data from cache
        assert "user/repo1" in merged["repos_data"]
        assert len(merged["repos_data"]["user/repo1"]["commits"]) == 1
        assert merged["repos_data"]["user/repo1"]["commits"][0].message == "new commit"
        assert "user/repo2" in merged["repos_data"]
        assert merged["repos_data"]["user/repo2"]["commits"] == []

    # ---- integration with get_user_activity ----

    @patch("crawler.github_api.requests.post")
    @patch("crawler.github_api.requests.get")
    def test_get_user_activity_with_cache_first_run(self, mock_get, mock_post, tmp_path):
        """First crawl with use_cache=True should fetch everything and save cache."""
        # Mock GraphQL responses (user + repos + commits + issues + prs + contributions)
        user_resp = _mock_response(200,
            {"data": {"user": {"name": "T", "bio": None, "company": None, "location": None,
                               "createdAt": "2024-01-01T00:00:00Z",
                               "updatedAt": "2024-01-02T00:00:00Z",
                               "publicRepos": 1, "followers": 0, "following": 0}}},
            {"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"})

        repos_resp = _mock_response(200,
            {"data": {"user": {"repositories": {"nodes": []}}}},  # empty repos for simplicity
            {"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"})

        # contributions response
        contrib_resp = _mock_response(200,
            {"data": {"user": {"contributionsCollection": {
                "contributionCalendar": {"totalContributions": 0, "weeks": []}},
                "contributionYears": []}}},
            {"X-RateLimit-Remaining": "4999", "X-RateLimit-Reset": "1234567890"})

        mock_post.return_value = user_resp
        # Need to handle multiple calls: user, repos, contributions
        mock_post.side_effect = [user_resp, repos_resp, contrib_resp]

        client = GitHubAPIClient(token="fake_token")
        cache = CrawlCache(str(tmp_path / "crawl_cache"))

        result = client.get_user_activity("testuser", use_cache=True, cache=cache)

        assert "cache_stats" in result
        assert result["cache_stats"] is not None
        assert result["cache_stats"]["cached_repos"] == 0
        assert result["cache_stats"]["fresh_repos"] == 0  # no repos in mock
        assert cache.has("testuser")

    def test_get_user_activity_cache_hit_skips_fetching(self, tmp_path):
        """Second crawl with unchanged repos should skip deep data."""
        client = GitHubAPIClient(token="fake_token")
        cache = CrawlCache(str(tmp_path / "crawl_cache"))

        # Seed cache with a repo that has up-to-date pushed_at
        now = datetime.now()
        cache_entry = cache.new_entry()
        cache_entry["repos"]["user/cached-repo"] = {
            "pushed_at": now.isoformat(),
            "commits": [{"sha": "cached", "message": "cached commit", "author": "user",
                         "date": now.isoformat(), "additions": 1, "deletions": 0}],
        }
        cache.save("testuser", cache_entry)

        # Mock user and repos to return a repo with same pushed_at
        client.get_user = Mock(return_value=GitHubUser(
            username="testuser", name="T", bio=None, company=None, location=None,
            created_at=datetime.now(), updated_at=datetime.now(),
            public_repos=1, followers=0, following=0))
        client.get_user_repos = Mock(return_value=[
            self._make_repo("user/cached-repo", now)
        ])
        client.get_user_contributions = Mock(return_value=GitHubContributionData(
            total_contributions=50, contribution_years=[2024],
            weeks_with_contributions=10, total_weeks=52,
            longest_streak=5, current_streak=2))

        # These should NOT be called for the cached repo
        client.get_repo_commits = Mock()
        client.get_repo_issues = Mock()
        client.get_repo_prs = Mock()
        client.get_repo_readme = Mock()
        client.get_repo_cicd_configs = Mock()

        result = client.get_user_activity("testuser", use_cache=True, cache=cache)

        # Verify deep data methods were NOT called (cache hit)
        client.get_repo_commits.assert_not_called()
        client.get_repo_issues.assert_not_called()
        client.get_repo_prs.assert_not_called()
        client.get_repo_readme.assert_not_called()
        client.get_repo_cicd_configs.assert_not_called()

        # Verify cache_stats reflect the hit
        assert result["cache_stats"]["cached_repos"] == 1
        assert result["cache_stats"]["fresh_repos"] == 0

        # Verify cached commit data was merged in
        assert any(c.message == "cached commit" for c in result["commits"])

    def test_get_user_activity_cache_refreshes_stale_repo(self, tmp_path):
        """Repo with newer pushed_at should be re-fetched."""
        client = GitHubAPIClient(token="fake_token")
        cache = CrawlCache(str(tmp_path / "crawl_cache"))

        old_ts = datetime(2024, 1, 1)
        new_ts = datetime(2024, 6, 1)

        # Seed cache with old data
        cache_entry = cache.new_entry()
        cache_entry["repos"]["user/stale-repo"] = {
            "pushed_at": old_ts.isoformat(),
            "commits": [{"sha": "old", "message": "old commit", "author": "user",
                         "date": old_ts.isoformat(), "additions": 1, "deletions": 0}],
        }
        cache.save("testuser", cache_entry)

        # Mock fresh user and repos
        client.get_user = Mock(return_value=GitHubUser(
            username="testuser", name="T", bio=None, company=None, location=None,
            created_at=datetime.now(), updated_at=datetime.now(),
            public_repos=1, followers=0, following=0))
        client.get_user_repos = Mock(return_value=[
            self._make_repo("user/stale-repo", new_ts)
        ])
        client.get_user_contributions = Mock(return_value=None)

        # Mock deep data methods called for stale repo
        commit = GitHubCommit(sha="new", message="new commit", author="user",
                              date=new_ts, additions=10, deletions=3)
        client.get_repo_commits = Mock(return_value=[commit])
        client.get_repo_issues = Mock(return_value=[])
        client.get_repo_prs = Mock(return_value=[])

        readme = GitHubReadme(content="# Fresh README", size_bytes=15, encoding="base64",
                              name="README.md")
        client.get_repo_readme = Mock(return_value=readme)
        client.get_repo_cicd_configs = Mock(return_value=[
            GitHubCICDConfig(path="Dockerfile", config_type="docker", exists=True)
        ])

        result = client.get_user_activity("testuser", use_cache=True, cache=cache)

        # Should have only the fresh commit (old was replaced)
        assert any(c.message == "new commit" for c in result["commits"])
        assert not any(c.message == "old commit" for c in result["commits"])

        # Cache stats
        assert result["cache_stats"]["fresh_repos"] == 1
        assert result["cache_stats"]["cached_repos"] == 0

        # Cache should be updated
        updated_cache = cache.load("testuser")
        assert updated_cache is not None
        assert updated_cache["repos"]["user/stale-repo"]["pushed_at"] == new_ts.isoformat()

