# S02: Role-Adaptive Scoring — UAT

**Milestone:** M001
**Written:** 2026-05-12T06:01:20.843Z

# S02: Role-Adaptive Scoring — UAT

**Milestone:** M001
**Written:** 2025-07-13

## UAT Type

- **UAT mode:** artifact-driven
- **Why this mode is sufficient:** All behavioral contracts are verified through the test suite (129 tests). Scoring logic is pure computation with no external dependencies when mocked. API endpoints have comprehensive contract tests. No runtime deployment or human UX interaction is needed.

## Preconditions

- Python environment with dependencies installed
- GITHUB_TOKEN environment variable set (required for module-level import in api/main.py)
- All test dependencies available (pytest, fastapi, pydantic, httpx)

## Smoke Test

```bash
python -m pytest tests/ -v --tb=short
```

Expected: 129 passed, 0 failed, 0 errors.

## Test Cases

### 1. Three role profiles exist with correct weights

```bash
python -c "
from scoring.profiles import list_profiles, get_profile
profiles = list_profiles()
assert len(profiles) >= 3, f'Expected 3+ profiles, got {len(profiles)}'
for p in profiles:
    assert abs(sum(p.weights.values()) - 1.0) < 0.001, f'{p.name} weights do not sum to 1.0'
    assert all(0 <= t <= 1 for t in p.thresholds.values()), f'{p.name} has thresholds outside [0,1]'
print('OK: 3 profiles with correct weights')
"
```

### 2. Role switching produces different scores

```bash
python -c "
from scoring.engine import ScoringEngine
from signals.extractor import SignalResult

engine = ScoringEngine()
data = {f'test_{i}': SignalResult(name=f'signal_{i}', score=50.0, confidence=0.8, details={}) for i in range(1, 13)}
result_default = engine.score_user(data)
engine.set_role('marketing')
result_marketing = engine.score_user(data)
assert result_default.overall_score != result_marketing.overall_score, 'Scores should differ between roles'
print(f'OK: default={result_default.overall_score}, marketing={result_marketing.overall_score}')
"
```

### 3. Confidence threshold filtering excludes low-confidence signals

```bash
python -c "
from scoring.engine import ScoringEngine
from signals.extractor import SignalResult

engine = ScoringEngine()
engine.set_role('engineering')
# Create signals where one has very low confidence
data = {
    'signal_1': SignalResult(name='signal_1', score=90.0, confidence=0.95, details={}),
    'signal_2': SignalResult(name='signal_2', score=80.0, confidence=0.01, details={}),
}
result = engine.score_user(data)
assert 'signal_2' in result.details.get('signals_below_threshold', {}), 'Low confidence signal should be in below_threshold'
assert 'signals_scored' in result.details, 'Signals scored should be reported'
print('OK: confidence threshold filtering works')
"
```

### 4. /profiles endpoint returns profiles

```bash
python -c "
from api.main import app
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.get('/profiles')
assert response.status_code == 200
data = response.json()
assert len(data['profiles']) >= 3
names = [p['name'] for p in data['profiles']]
assert 'engineering' in names
assert 'marketing' in names
print('OK: /profiles returns 3 profiles')
"
```

### 5. /score with role parameter uses profile weights

```bash
python -c "
from api.main import app
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.post('/score', json={'username': 'testuser', 'role': 'engineering'})
assert response.status_code == 200
data = response.json()
assert data['profile'] == 'engineering'
assert 'profile_name' in data.get('details', {})
print(f'OK: /score with role returned profile={data[\"profile\"]}')
"
```

### 6. /score without role uses legacy weights (backward compatible)

```bash
python -c "
from api.main import app
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.post('/score', json={'username': 'testuser'})
assert response.status_code == 200
print('OK: /score without role works (backward compatible)')
"
```

### 7. /match uses profile-based matching

```bash
python -c "
from api.main import app, _resolve_role_for_matching
from fastapi.testclient import TestClient

# Test profile matching
profile, boosts = _resolve_role_for_matching('senior software engineer')
assert profile == 'engineering', f'Expected engineering, got {profile}'
assert boosts == {}, 'Expected no keyword boosts for exact match'

# Test keyword fallback
profile, boosts = _resolve_role_for_matching('some random description')
assert profile is None or boosts != {}, 'Expected fallback to keyword matching'

print('OK: profile matching and fallback work')
"
```

## Edge Cases

### Unknown role returns 400

```bash
python -c "
from api.main import app
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.post('/score', json={'username': 'testuser', 'role': 'nonexistent_role'})
assert response.status_code == 400
print('OK: unknown role returns 400')
"
```

### Custom weights override profile

```bash
python -c "
from scoring.engine import ScoringEngine
from signals.extractor import SignalResult

engine = ScoringEngine()
engine.set_role('engineering')
data = {f'test_{i}': SignalResult(name=f'signal_{i}', score=50.0, confidence=0.9, details={}) for i in range(1, 13)}
before = engine.score_user(data).overall_score
engine.weights = {'readme_quality': 1.0} | {k: 0.0 for k in engine.weights if k != 'readme_quality'}
after = engine.score_user(data).overall_score
assert before != after, 'Custom weights should change the score'
print(f'OK: custom weights override: before={before}, after={after}')
"
```

## Failure Signals

- Test failures: any test failure indicates regression in scoring logic
- /profiles returns less than 3 profiles: profile data model issue
- Incorrect role name in profile: weight distribution or threshold misconfiguration
- /score with role returning same score as default: role not being applied

## Not Proven By This UAT

- GITHUB_TOKEN integration with actual GitHub API calls (all API tests use mock client patterns internally via TestClient without making real HTTP calls)
- Long-running performance under concurrent requests
- UI integration with the /profiles endpoint
- Attestation signing of profile-aware scores (S03)

## Notes for Tester

- The api/main.py module requires GITHUB_TOKEN to be set at import time even for unit testing. Set GITHUB_TOKEN=test_value before running tests if executing manually.
- All API endpoint tests use FastAPI TestClient which does not make real HTTP calls.
- Scoring tests use mock SignalResult objects with deterministic values.

