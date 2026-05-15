---
estimated_steps: 13
estimated_files: 2
skills_used: []
---

# T03: Proof status tracking and API endpoint

Add proof status tracking and API endpoint:
- Simple ProofStatus store: dict or SQLite (upgradable to PostgreSQL later)
  - proof_id: str
  - username: str
  - status: pending | proof_generating | proof_generated | on_chain | failed
  - created_at, updated_at
  - proof_path (nullable)
  - tx_hash (nullable, when submitted on-chain)
  - error (nullable)
- GET /proof/{username}/status returns current proof status
- Auto-submit proof on-chain after generation (optional — can be manual step for now)
- Endpoint returns Ed25519 attestation alongside proof status for full picture

Output: Proof status pollable via API. Status transitions correctly.

## Inputs

- `api/main.py`
- `api/celery_app.py`
- `api/proof_tasks.py`

## Expected Output

- `api/proof_status.py`
- `api/main.py (updated proof endpoints)`

## Verification

POST /score with username 'testuser' → status is 'proof_generating'. Wait for Celery task → status becomes 'proof_generated' or 'on_chain'. GET /proof/testuser/status returns correct status. Ed25519 attestation always returned regardless of proof status.
