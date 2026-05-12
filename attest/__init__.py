"""
Attestation Module
Ed25519-based signing and verification of score attestations.

Provides:
  - load_or_generate_signing_key: Key management (env/file/generate).
  - sign_score: Sign a score payload with an Ed25519 key.
  - verify_attestation: Verify a signed payload's Ed25519 signature.
"""
from attest.config import load_or_generate_signing_key
from attest.signer import sign_score, verify_attestation

__all__ = [
    "load_or_generate_signing_key",
    "sign_score",
    "verify_attestation",
]
