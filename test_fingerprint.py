"""Quick script to score a GitHub profile and print results."""
import os
import sys
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from crawler.github_api import GitHubAPIClient
from signals.extractor import SignalExtractor
from scoring.engine import ScoringEngine
from signals.personality import extract_personality


def main(username: str):
    print(f"GitHub Fingerprint for: {username}")
    print("-" * 50)

    client = GitHubAPIClient()
    extractor = SignalExtractor()
    engine = ScoringEngine()

    data = client.get_user_activity(username)
    result = engine.score_user(data)

    # Personality inference
    personality = extract_personality(data)

    print(f"\nOverall Score: {result.overall_score:.1f}/100")
    print(f"Risk Flags: {result.risk_flags}")
    print()

    print("Signal Scores:")
    for name, sr in sorted(result.signal_scores.items(), key=lambda x: x[1].score, reverse=True):
        bar = "█" * int(sr.score / 5) + "░" * (20 - int(sr.score / 5))
        print(f"  {name:25s} {sr.score:5.1f}  {bar}  (conf: {sr.confidence:.2f})")

    print()
    print("Details:")
    for k, v in result.details.items():
        print(f"  {k}: {v}")

    # Build personality inferences
    print()
    print("=" * 50)
    print("PERSONALITY PROFILE — ExO × 4Rs Model")
    print("=" * 50)
    print()

    # 4Rs Segment
    cr = personality["change_readiness"]
    bar = "█" * int(cr["score"] / 5) + "░" * (20 - int(cr["score"] / 5))
    print(f"Change Readiness: {cr['segment']}")
    print(f"  4Rs Score:      {cr['score']:3d}/100  {bar}")
    print()

    # Personality signals
    psig = personality["signals"]
    for name in ["flexibility", "ambiguity_comfort"]:
        sr = psig[name]
        bar = "█" * int(sr.score / 5) + "░" * (20 - int(sr.score / 5))
        print(f"  {name:25s} {sr.score:5.1f}  {bar}  (conf: {sr.confidence:.2f})")
        for k, v in sr.details.items():
            if isinstance(v, str):
                continue
            print(f"    ├─ {k}: {v}")

    # Personality style label
    flex_score = psig["flexibility"].score
    amb_score = psig["ambiguity_comfort"].score

    print()
    if cr["segment"] == "Results":
        style = "🏆 Visionary Builder — thrives in ambiguity, experiments constantly, creates new paths"
    elif cr["segment"] == "Resilient":
        style = "🌱 Adaptive Builder — responds well to guidance, adapts quickly once the path is clear"
    elif cr["segment"] == "Reluctant":
        style = "🌿 Steady Builder — prefers proven approaches, adopts with peer reinforcement"
    else:
        style = "🌵 Early Stage / Limited Signal — needs more activity data for confident classification"

    print(f"Development Style: {style}")

    # ExO SCALE summary
    print()
    print("ExO SCALE Attributes (estimated):")
    exo = []
    if cr["score"] > 60:
        exo.append("  ⚡ Algorithms: Builds systematic, repeatable solutions")
    else:
        exo.append("  ⚡ Algorithms: Developing systematic approaches")

    if psig["ambiguity_comfort"].score > 50:
        exo.append("  🔬 Experimentation: Explores new tools and domains regularly")
    else:
        exo.append("  🔬 Experimentation: Prefers depth in familiar domains")

    if psig["flexibility"].details.get("responsiveness", 0) > 50:
        exo.append("  🤝 Engagement: Responsive to external input, iterates with feedback")
    else:
        exo.append("  🤝 Engagement: Works independently, self-directed")

    owned_ratio = result.signal_scores["project_ownership"].score
    if owned_ratio > 60:
        exo.append("  🚀 Autonomy: Self-starter, initiates own projects")
    else:
        exo.append("  🚀 Autonomy: Collaborative, builds on existing work")

    for e in exo:
        print(f"  {e}")

    print()
    print("-" * 50)
    print("Personality Inferences (legacy):")
    inferences = []

    if result.signal_scores["commit_consistency"].score > 70:
        inferences.append("✅ Consistent builder — regular commit cadence suggests reliable work patterns")
    else:
        inferences.append("📝 Sporadic committer — may work in bursts or be early in their coding journey")

    lang = result.signal_scores["language_diversity"]
    if lang.score > 70:
        inferences.append("🌈 Polyglot — comfortable across multiple languages/domains, adapts quickly")
    elif lang.score > 40:
        inferences.append("🔧 Focused specialist — deep in a few tools, strong opinionated work")
    else:
        inferences.append("💎 Single-stack — may be early in their journey or hyper-focused")

    issues = result.signal_scores["issue_engagement"]
    if issues.score > 60:
        inferences.append("💬 Community engager — participates in discussions, collaborative problem-solver")
    else:
        inferences.append("🔇 Quiet coder — focuses on solo work, less visible in community threads")

    prs = result.signal_scores["pr_patterns"]
    if prs.score > 60:
        inferences.append("🔀 Active collaborator — regular PR contributions, team player")
    else:
        inferences.append("🛠️ Independent builder — works primarily on own projects")

    reviews = result.signal_scores["review_patterns"]
    if reviews.score > 50:
        inferences.append("👁️ Thorough reviewer — engages in code review, cares about quality")
    else:
        inferences.append("🏗️ Builder mindset — focuses on shipping over reviewing")

    for inf in inferences:
        print(f"  {inf}")

    print()
    print("=" * 50)

    # Generate attestation
    try:
        from attestation.signer import sign_score
        att = sign_score(username, result.overall_score, {
            "username": username,
            "overall_score": result.overall_score,
            "signal_scores": {k: {"score": v.score, "confidence": v.confidence} for k, v in result.signal_scores.items()},
            "risk_flags": result.risk_flags,
            "details": result.details,
        })
        if att:
            print(f"\n✅ Signed Attestation Generated")
            print(f"  Public Key: {att.public_key[:16]}...")
            print(f"  Signature:  {att.signature[:16]}...")
            print(f"  Data Hash:  {att.response_hash[:16]}...")
            print(f"  Timestamp:  {att.timestamp}")
    except ImportError:
        print("\n⚠️  Attestation skipped (cryptography not available)")


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "armchairfuturist-code"
    main(username)
