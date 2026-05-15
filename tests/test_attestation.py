"""
Unit tests for the cryptographic attestation/signing module.
"""
import json
import hashlib
import pytest

from attestation.signer import (
    Attestation,
    _compute_response_hash,
    sign_score,
    verify_attestation,
    _CRYPTO_AVAILABLE,
)


pytestmark = pytest.mark.skipif(
    not _CRYPTO_AVAILABLE,
    reason="cryptography package not installed",
)


class TestResponseHash:
    """Test payload hashing for attestation commitments."""

    def test_hash_is_deterministic(self):
        payload = {"a": 1, "b": [2, 3], "c": {"d": "hello"}}
        h1 = _compute_response_hash(payload)
        h2 = _compute_response_hash(payload)
        assert h1 == h2

    def test_hash_changes_with_data(self):
        payload_a = {"score": 75, "user": "test"}
        payload_b = {"score": 80, "user": "test"}
        assert _compute_response_hash(payload_a) != _compute_response_hash(payload_b)

    def test_hash_is_sha256(self):
        payload = {"msg": "hello"}
        result = _compute_response_hash(payload)
        assert len(result) == 64  # 256 bits = 64 hex chars
        int(result, 16)  # valid hex


class TestSignAndVerify:
    """Test full sign -> verify round-trip."""

    def test_sign_and_verify_round_trip(self):
        payload = {
            "username": "testuser",
            "overall_score": 85.5,
            "signal_scores": {
                "commit_consistency": {"score": 90, "confidence": 0.8}
            },
        }

        attestation = sign_score("testuser", 85.5, payload)
        assert attestation is not None
        assert attestation.username == "testuser"
        assert attestation.overall_score == 85.5
        assert len(attestation.signature) > 0
        assert len(attestation.public_key) > 0
        assert attestation.timestamp > 0

        # Verify round-trip
        assert verify_attestation(attestation) is True

    def test_verify_tampered_score_fails(self):
        payload = {"username": "user1", "overall_score": 70.0}
        attestation = sign_score("user1", 70.0, payload)
        assert attestation is not None

        # Tamper with the score
        attestation.overall_score = 99.9
        assert verify_attestation(attestation) is False

    def test_verify_tampered_hash_fails(self):
        payload = {"username": "user2", "overall_score": 60.0}
        attestation = sign_score("user2", 60.0, payload)
        assert attestation is not None

        # Tamper with the response hash
        attestation.response_hash = hashlib.sha256(b"fake").hexdigest()
        assert verify_attestation(attestation) is False

    def test_verify_tampered_signature_fails(self):
        payload = {"username": "user3", "overall_score": 50.0}
        attestation = sign_score("user3", 50.0, payload)
        assert attestation is not None

        # Corrupt the signature
        attestation.signature = "a" * len(attestation.signature)
        assert verify_attestation(attestation) is False

    def test_verify_tampered_username_fails(self):
        payload = {"username": "real_user", "overall_score": 80.0}
        attestation = sign_score("real_user", 80.0, payload)
        assert attestation is not None

        attestation.username = "different_user"
        assert verify_attestation(attestation) is False

    def test_key_persistence(self):
        """Keys generated on first call persist to disk for subsequent calls."""
        payload = {"username": "persist", "overall_score": 90.0}
        a1 = sign_score("persist", 90.0, payload)
        a2 = sign_score("persist", 90.0, payload)
        assert a1 is not None and a2 is not None

        # Same public key across calls
        assert a1.public_key == a2.public_key

        # Both verify
        assert verify_attestation(a1) is True
        assert verify_attestation(a2) is True

    def test_different_users_get_verifiable_attestations(self):
        payload1 = {"user": "alice", "score": 80.0}
        payload2 = {"user": "bob", "score": 70.0}

        a1 = sign_score("alice", 80.0, payload1)
        a2 = sign_score("bob", 70.0, payload2)

        assert a1 is not None and a2 is not None
        assert verify_attestation(a1) is True
        assert verify_attestation(a2) is True
        assert a1.signature != a2.signature


class TestAttestationFormat:
    """Test attestation data structure and serialization."""

    def test_attestation_dataclass_fields(self):
        att = Attestation(
            username="u",
            overall_score=75.0,
            response_hash="a" * 64,
            timestamp=1234567890,
            signature="abcd",
            public_key="1234",
            version="1",
        )
        assert att.version == "1"

    def test_attestation_can_be_serialized(self):
        payload = {"test": "data"}
        att = sign_score("serialize", 65.0, payload)
        assert att is not None

        # Can round-trip through dict/JSON
        data = {
            "username": att.username,
            "overall_score": att.overall_score,
            "response_hash": att.response_hash,
            "timestamp": att.timestamp,
            "signature": att.signature,
            "public_key": att.public_key,
            "version": att.version,
        }
        json_str = json.dumps(data, sort_keys=True)
        restored = json.loads(json_str)

        assert restored["username"] == "serialize"
        assert restored["overall_score"] == 65.0
        assert restored["signature"] == att.signature
