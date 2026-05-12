"""
Python vs Rust scoring comparison script.
Reads test fixtures, runs both engines, reports diffs.
"""
import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def load_fixture(path):
    """Load a ScoreInput fixture JSON."""
    with open(path) as f:
        return json.load(f)


def dict_to_repo(d):
    """Convert a dict to a GitHubRepo-like SimpleNamespace."""
    from types import SimpleNamespace
    return SimpleNamespace(
        name=d["name"],
        full_name=d["full_name"],
        description=d.get("description"),
        language=d.get("language"),
        stars=d.get("stars", 0),
        forks=d.get("forks", 0),
        is_fork=d.get("is_fork", False),
        is_private=d.get("is_private", False),
        pushed_at=parse_dt(d.get("pushed_at", "")),
    )


def dict_to_commit(d):
    from types import SimpleNamespace
    return SimpleNamespace(
        sha=d["sha"],
        message=d["message"],
        author=d.get("author", ""),
        date=parse_dt(d["date"]),
        additions=d.get("additions", 0),
        deletions=d.get("deletions", 0),
    )


def dict_to_issue(d):
    from types import SimpleNamespace
    return SimpleNamespace(
        number=d["number"],
        title=d["title"],
        state=d["state"],
        created_at=parse_dt(d["created_at"]),
        closed_at=parse_dt(d["closed_at"]) if d.get("closed_at") else None,
        comments=d.get("comments", 0),
        author=d.get("author", ""),
    )


def dict_to_pr(d):
    from types import SimpleNamespace
    return SimpleNamespace(
        number=d["number"],
        title=d["title"],
        state=d["state"],
        created_at=parse_dt(d["created_at"]),
        closed_at=parse_dt(d["closed_at"]) if d.get("closed_at") else None,
        merged_at=parse_dt(d["merged_at"]) if d.get("merged_at") else None,
        additions=d.get("additions", 0),
        deletions=d.get("deletions", 0),
        changed_files=d.get("changed_files", 0),
        comments=d.get("comments", 0),
        review_comments=d.get("review_comments", 0),
        author=d.get("author", ""),
    )


def dict_to_readme(d):
    from types import SimpleNamespace
    return SimpleNamespace(
        content=d.get("content"),
        size_bytes=d.get("size_bytes", 0),
        encoding=d.get("encoding", ""),
        name=d.get("name", "README.md"),
        detected_sections=d.get("detected_sections", []),
        badge_count=d.get("badge_count", 0),
        has_code_blocks=d.get("has_code_blocks", False),
        code_block_count=d.get("code_block_count", 0),
        has_emoji=d.get("has_emoji", False),
        list_count=d.get("list_count", 0),
    )


def dict_to_cicd(d):
    from types import SimpleNamespace
    return SimpleNamespace(
        path=d["path"],
        config_type=d["config_type"],
        exists=d["exists"],
        size_bytes=d.get("size_bytes", 0),
        content_summary=d.get("content_summary", ""),
    )


def dict_to_contrib_day(d):
    from types import SimpleNamespace
    return SimpleNamespace(
        date=parse_dt(d["date"]),
        contribution_count=d["contribution_count"],
    )


def dict_to_contributions(d):
    from types import SimpleNamespace
    days = [dict_to_contrib_day(cd) for cd in d.get("contribution_days", [])]
    return SimpleNamespace(
        total_contributions=d.get("total_contributions", 0),
        contribution_years=d.get("contribution_years", []),
        contribution_days=days,
        weeks_with_contributions=d.get("weeks_with_contributions", 0),
        total_weeks=d.get("total_weeks", 0),
        first_contribution_date=parse_dt(d["first_contribution_date"]) if d.get("first_contribution_date") else None,
        longest_streak=d.get("longest_streak", 0),
        current_streak=d.get("current_streak", 0),
    )


def parse_dt(s):
    if s is None:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def convert_data(data):
    """Convert raw JSON dicts to typed objects the Python engine expects."""
    return {
        "repos": [dict_to_repo(r) for r in data.get("repos", [])],
        "commits": [dict_to_commit(c) for c in data.get("commits", [])],
        "issues": [dict_to_issue(i) for i in data.get("issues", [])],
        "prs": [dict_to_pr(p) for p in data.get("prs", [])],
        "readmes": {
            k: dict_to_readme(v) for k, v in data.get("readmes", {}).items()
        },
        "cicd_configs": {
            k: [dict_to_cicd(c) for c in v]
            for k, v in data.get("cicd_configs", {}).items()
        },
        "contributions": (
            dict_to_contributions(data["contributions"])
            if data.get("contributions") else None
        ),
    }


def run_python_scorer(data):
    """Run the Python scoring engine on fixture data."""
    from scoring.engine import ScoringEngine
    from signals.extractor import SignalExtractor

    # Convert JSON to namespace objects matching Python dataclasses
    typed_data = convert_data(data)
    repos = typed_data["repos"]
    commits = typed_data["commits"]
    issues = typed_data["issues"]
    prs = typed_data["prs"]
    readmes = typed_data["readmes"]
    cicd_configs = typed_data["cicd_configs"]
    contributions = typed_data["contributions"]

    # Extract signals
    extractor = SignalExtractor()

    signals = {}
    signals["commit_consistency"] = extractor.extract_commit_consistency(commits)
    signals["language_diversity"] = extractor.extract_language_diversity(repos)
    signals["issue_engagement"] = extractor.extract_issue_engagement(issues)
    signals["pr_patterns"] = extractor.extract_pr_patterns(prs)
    signals["project_ownership"] = extractor.extract_project_ownership(repos, prs)
    signals["review_patterns"] = extractor.extract_review_patterns(prs)
    signals["response_time"] = extractor.extract_response_time(prs, issues)
    signals["readme_quality"] = extractor.extract_readme_quality(repos, readmes)
    signals["commit_semantics"] = extractor.extract_commit_semantics(commits)
    signals["cicd_maturity"] = extractor.extract_cicd_maturity(cicd_configs, repos)
    signals["contribution_consistency"] = extractor.extract_contribution_consistency(contributions, commits)
    signals["ai_usage_patterns"] = extractor.extract_ai_usage_patterns(commits)

    # Run scoring with engineering profile (matching Rust default)
    engine = ScoringEngine(profile="engineering")
    activity_data = {
        "repos": repos, "commits": commits, "issues": issues, "prs": prs,
        "readmes": readmes, "cicd_configs": cicd_configs, "contributions": contributions,
    }
    result = engine.score_user(activity_data)

    return {
        "overall_score": result.overall_score,
        "signal_scores": {
            name: {"score": s.score, "confidence": s.confidence}
            for name, s in result.signal_scores.items()
        },
        "risk_flags": result.risk_flags,
        "profile_name": result.details.get("profile_name", "legacy"),
        "signals_below_threshold": result.details.get("signals_below_threshold", []),
    }


def run_rust_scorer(fixture_path, role=None):
    """Run the Rust scoring CLI on a fixture."""
    cmd = [str(Path(__file__).resolve().parent.parent / "target" / "debug" / "scoring-cli.exe")]
    cmd.extend(["--input", fixture_path])
    if role:
        cmd.extend(["--role", role])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Rust CLI error: {result.stderr}")
        return None
    return json.loads(result.stdout)


def compare_scores(py, rs, tolerance=0.5):
    """Compare Python and Rust scores. Returns list of diffs exceeding tolerance."""
    diffs = []
    
    # Compare overall score
    overall_diff = abs(py["overall_score"] - rs["overall_score"])
    if overall_diff > tolerance:
        diffs.append(f"OVERALL: Python={py['overall_score']:.2f} Rust={rs['overall_score']:.2f} diff={overall_diff:.2f}")
    
    # Compare signal scores
    all_signals = set(list(py["signal_scores"].keys()) + list(rs["signal_scores"].keys()))
    for sig in sorted(all_signals):
        py_sig = py["signal_scores"].get(sig, {"score": 0, "confidence": 0})
        rs_sig = rs["signal_scores"].get(sig, {"score": 0, "confidence": 0})
        
        score_diff = abs(py_sig["score"] - rs_sig["score"])
        conf_diff = abs(py_sig["confidence"] - rs_sig["confidence"])
        
        if score_diff > tolerance or conf_diff > 0.1:
            diffs.append(
                f"{sig}: score Python={py_sig['score']:.2f} Rust={rs_sig['score']:.2f} "
                f"diff={score_diff:.2f} | conf Python={py_sig['confidence']:.2f} "
                f"Rust={rs_sig['confidence']:.2f}"
            )
    
    # Compare risk flags
    py_flags = set(py.get("risk_flags", []))
    rs_flags = set(rs.get("risk_flags", []))
    missing_from_rust = py_flags - rs_flags
    extra_in_rust = rs_flags - py_flags
    if missing_from_rust:
        diffs.append(f"Risk flags missing from Rust: {missing_from_rust}")
    if extra_in_rust:
        diffs.append(f"Extra risk flags in Rust: {extra_in_rust}")
    
    return diffs


def main():
    fixtures_dir = Path(__file__).resolve().parent / "fixtures"
    fixtures = sorted(fixtures_dir.glob("*.json"))
    
    if not fixtures:
        print("No fixtures found. Run generate_fixtures.py first.")
        return 1
    
    passed = 0
    failed = 0
    
    for fixture_path in fixtures:
        print(f"\n{'='*60}")
        print(f"Testing: {fixture_path.name}")
        print(f"{'='*60}")
        
        data = load_fixture(str(fixture_path))
        
        # Run Python scorer
        py_result = run_python_scorer(data)
        print(f"Python: overall={py_result['overall_score']:.2f}")
        
        # Run Rust scorer
        rs_result = run_rust_scorer(str(fixture_path))
        if rs_result is None:
            print(f"  FAILED: Rust CLI error")
            failed += 1
            continue
        print(f"Rust:   overall={rs_result['overall_score']:.2f}")
        
        # Compare
        diffs = compare_scores(py_result, rs_result)
        
        if diffs:
            print(f"  DIFFS ({len(diffs)}):")
            for d in diffs:
                print(f"    - {d}")
            failed += 1
        else:
            print(f"  PASS: All scores match within tolerance")
            passed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(fixtures)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
