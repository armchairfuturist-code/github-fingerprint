"""
Tests for the attestation module (Ed25519 signing and verification).
"""
import json
import os

import pytest
from nacl.signing import SigningKey

from attest import (
    load_or_generate_signing_key,
    sign_score,
    verify_attestation,
)
from attest.config import ENV_KEY_NAME


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def signing_pair():
    """Return a (SigningKey, verify_key_bytes) pair from an ephemeral key."""
    sk, vk = load_or_generate_signing_key()
    return sk, vk


@pytest.fixture
def sample_signal_scores():
    return {
        "commit_consistency": {"score": 80, "confidence": 0.8},
        "language_diversity": {"score": 70, "confidence": 0.7},
    }


# ---------------------------------------------------------------------------
# Key loading
# ---------------------------------------------------------------------------


class TestKeyLoading:
    def test_generates_key_when_no_env(self):
        """Should generate an ephemeral key when no env var is set."""
        sk, vk = load_or_generate_signing_key()
        assert isinstance(sk, SigningKey)
        assert isinstance(vk, bytes)
        assert len(vk) == 32  # Ed25519 public key is 32 bytes

    def test_loads_from_env_var(self, monkeypatch):
        """Should load a signing key from ATTEST_PRIVATE_KEY (base64)."""
        import base64

        original = SigningKey.generate()
        seed_b64 = base64.b64encode(bytes(original._seed)).decode("ascii")
        monkeypatch.setenv(ENV_KEY_NAME, seed_b64)

        sk, vk = load_or_generate_signing_key()
        assert bytes(sk.verify_key) == bytes(original.verify_key)

    def test_empty_env_falls_back_to_generated(self, monkeypatch):
        """Should fall back to generation when env var is empty/invalid."""
        monkeypatch.setenv(ENV_KEY_NAME, "not-valid-base64!!")
        sk, vk = load_or_generate_signing_key()
        assert isinstance(sk, SigningKey)
        assert len(vk) == 32

    def test_rejects_short_seed(self, monkeypatch):
        """Should fall back to generation when seed is not 32 bytes."""
        import base64

        short_b64 = base64.b64encode(b"too short").decode("ascii")
        monkeypatch.setenv(ENV_KEY_NAME, short_b64)
        sk, vk = load_or_generate_signing_key()
        assert isinstance(sk, SigningKey)
        assert len(vk) == 32


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------


class TestSigning:
    def test_signs_and_returns_all_fields(self, signing_pair):
        sk, _ = signing_pair
        result = sign_score(
            username="alice",
            overall_score=75.0,
            signal_scores={},
            risk_flags=[],
            profile_name="engineering",
            private_key=sk,
        )
        assert "signature" in result
        assert "public_key" in result
        assert "signed_payload" in result
        assert "signed_at" in result
        # All values are strings
        for v in result.values():
            assert isinstance(v, str), f"Expected str, got {type(v)}: {v}"

    def test_signed_payload_contains_all_fields(self, signing_pair):
        sk, _ = signing_pair
        result = sign_score(
            username="bob",
            overall_score=88.5,
            signal_scores={"commit_consistency": {"score": 90, "confidence": 0.9}},
            risk_flags=["Low review patterns score"],
            profile_name="engineering",
            private_key=sk,
        )
        payload = json.loads(result["signed_payload"])
        assert payload["username"] == "bob"
        assert payload["overall_score"] == 88.5
        assert payload["risk_flags"] == ["Low review patterns score"]
        assert payload["profile_name"] == "engineering"
        assert "signed_at" in payload
        assert "signal_scores" in payload

    def test_signed_payload_has_sorted_keys(self, signing_pair):
        """Canonical payload must have signal_scores sorted by name."""
        sk, _ = signing_pair
        result = sign_score(
            username="multi",
            overall_score=85.0,
            signal_scores={
                "z_signal": {"score": 90, "confidence": 0.9},
                "a_signal": {"score": 80, "confidence": 0.8},
            },
            risk_flags=[],
            profile_name="engineering",
            private_key=sk,
        )
        payload = json.loads(result["signed_payload"])
        assert list(payload["signal_scores"].keys()) == [
            "a_signal",
            "z_signal",
        ]

    def test_risk_flags_sorted(self, signing_pair):
        """risk_flags should be sorted lexicographically."""
        sk, _ = signing_pair
        result = sign_score(
            username="sort",
            overall_score=60.0,
            signal_scores={},
            risk_flags=["z_flag", "a_flag"],
            profile_name="engineering",
            private_key=sk,
        )
        payload = json.loads(result["signed_payload"])
        assert payload["risk_flags"] == ["a_flag", "z_flag"]

    def test_signed_payload_deterministic(self, signing_pair):
        """Same inputs must produce identical signed payload."""
        sk, _ = signing_pair
        r1 = sign_score("det", 50.0, {}, [], "test", sk)
        r2 = sign_score("det", 50.0, {}, [], "test", sk)
        # Payloads must be identical except signed_at differs
        p1 = json.loads(r1["signed_payload"])
        p2 = json.loads(r2["signed_payload"])
        for key in ("username", "overall_score", "signal_scores", "risk_flags", "profile_name"):
            assert p1[key] == p2[key], f"Mismatch for {key}"

    def test_signed_at_is_iso8601(self, signing_pair):
        sk, _ = signing_pair
        result = sign_score("iso", 50.0, {}, [], "test", sk)
        assert "T" in result["signed_at"]
        assert result["signed_at"].endswith("Z")


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


class TestVerification:
    def test_verify_with_raw_bytes_key(self, signing_pair):
        """Verify using raw bytes public key from load_or_generate_signing_key."""
        sk, vk = signing_pair
        sig = sign_score("testuser", 75.0, {"cs": {"score": 80, "confidence": 0.8}}, [], "engineering", sk)
        result = verify_attestation(sig["signed_payload"], sig["signature"], vk)
        assert result["valid"] is True
        assert result["payload"]["username"] == "testuser"

    def test_verify_with_base64_key(self, signing_pair):
        """Verify using base64-encoded public key from sign_score result."""
        sk, _ = signing_pair
        sig = sign_score("testuser", 75.0, {"cs": {"score": 80, "confidence": 0.8}}, [], "engineering", sk)
        result = verify_attestation(sig["signed_payload"], sig["signature"], sig["public_key"])
        assert result["valid"] is True

    def test_tampered_payload_fails(self, signing_pair):
        """A modified payload should fail verification."""
        sk, vk = signing_pair
        sig = sign_score("testuser", 75.0, {}, [], "engineering", sk)
        result = verify_attestation('{"tampered": true}', sig["signature"], vk)
        assert result["valid"] is False
        assert "error" in result

    def test_wrong_key_fails(self):
        """Verification with a different public key should fail."""
        sk1, _ = load_or_generate_signing_key()
        _, vk2 = load_or_generate_signing_key()
        sig = sign_score("testuser", 75.0, {}, [], "engineering", sk1)
        result = verify_attestation(sig["signed_payload"], sig["signature"], vk2)
        assert result["valid"] is False

    def test_verify_non_empty_signals(self, signing_pair, sample_signal_scores):
        """Verify with multiple signals."""
        sk, vk = signing_pair
        sig = sign_score("multi", 85.0, sample_signal_scores, ["flag"], "engineering", sk)
        result = verify_attestation(sig["signed_payload"], sig["signature"], vk)
        assert result["valid"] is True
        assert "commit_consistency" in result["payload"]["signal_scores"]

    def test_returns_payload_on_failure(self, signing_pair):
        """Even failed verification should return the parsed payload."""
        sk, vk = signing_pair
        sig = sign_score("testuser", 75.0, {}, [], "engineering", sk)
        result = verify_attestation('{"test": 1}', sig["signature"], vk)
        assert result["valid"] is False
        # Should still have a payload (or error info)
        assert result["payload"] == {"test": 1} or result["payload"] is None

    def test_verify_with_empty_scores(self, signing_pair):
        """Should handle empty signal_scores and risk_flags."""
        sk, vk = signing_pair
        sig = sign_score("empty", 0.0, {}, [], "default", sk)
        result = verify_attestation(sig["signed_payload"], sig["signature"], vk)
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# Round-trip integration
# ---------------------------------------------------------------------------


class TestRoundTrip:
    """End-to-end signing and verification with various score shapes."""

    def test_typical_score(self, signing_pair):
        sk, vk = signing_pair
        signal_scores = {
            "commit_consistency": {"score": 85, "confidence": 0.9},
            "review_patterns": {"score": 72, "confidence": 0.75},
            "response_time": {"score": 90, "confidence": 0.85},
        }
        risk_flags = [
            "Low language diversity score",
            "Low confidence in ai_usage_patterns for engineering profile",
        ]
        sig = sign_score(
            "typical-user", 82.3, signal_scores, risk_flags, "engineering", sk
        )
        result = verify_attestation(sig["signed_payload"], sig["signature"], vk)
        assert result["valid"] is True
        payload = result["payload"]
        assert payload["username"] == "typical-user"
        assert payload["overall_score"] == 82.3
        assert len(payload["signal_scores"]) == 3
        assert len(payload["risk_flags"]) == 2
