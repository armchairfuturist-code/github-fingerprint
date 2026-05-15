"""Smoke test: verify fingerprint endpoint produces valid HTML."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from crawler.github_api import GitHubAPIClient
from scoring.engine import ScoringEngine
from signals.personality import extract_personality

client = GitHubAPIClient()
engine = ScoringEngine()

username = sys.argv[1] if len(sys.argv) > 1 else "armchairfuturist-code"

data = client.get_user_activity(username)
sr = engine.score_user(data)
personality = extract_personality(data)

cr = personality["change_readiness"]
psig = personality["signals"]

print(f"fingerprint/{username}")
print(f"  Overall: {sr.overall_score:.1f}/100")
print(f"  Segment: {cr['segment']} ({cr['score']}/100)")
print()
print("Signals:")
for name, s in sorted(sr.signal_scores.items(), key=lambda x: x[1].score, reverse=True):
    bar = "█" * int(s.score / 5) + "░" * (20 - int(s.score / 5))
    print(f"  {name:25s} {s.score:5.1f}  {bar}")
print()
print("Personality:")
for name in ["flexibility", "ambiguity_comfort"]:
    s = psig[name]
    bar = "█" * int(s.score / 5) + "░" * (20 - int(s.score / 5))
    print(f"  {name:25s} {s.score:5.1f}  {bar}")
print()
print("Deploy: uvicorn api.main:app --host 0.0.0.0 --port 8000")
print("Try:    curl -s http://localhost:8000/fingerprint/{username} | head -5")
