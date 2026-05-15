---
estimated_steps: 15
estimated_files: 3
skills_used: []
---

# T03: Add /verify endpoint for signature verification

Add a POST /verify endpoint that accepts a verification request payload:

```python
class VerifyRequest(BaseModel):
    signed_payload: str
    signature: str
    public_key: str

class VerifyResponse(BaseModel):
    valid: bool
    payload: Optional[Dict[str, Any]] = None
```

The endpoint calls attest.verify_attestation() and returns the result. Handle malformed inputs gracefully:
- Invalid base64 → 400 with clear error message
- Invalid signature format → valid: false, error message in response
- Missing fields → 400 with field validation errors

Register the endpoint at `/verify` (POST only).

## Inputs

- `api/main.py`
- `attest/signer.py`

## Expected Output

- `api/main.py`

## Verification

grep -q "verify" api/main.py && grep -q "/verify" api/main.py
