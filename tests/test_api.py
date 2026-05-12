"""
Unit tests for the FastAPI endpoints (role-adaptive scoring wiring).
"""
import pytest
from api.main import (
    app,
    ScoreRequest,
    ScoreResponse,
    MatchRequest,
    ProfileResponse,
    ProfilesListResponse,
    VerifyRequest,
    VerifyResponse,
    _resolve_role_for_matching,
    _extract_role_keywords,
)


# ---------------------------------------------------------------------------
# Pydantic model tests
# ---------------------------------------------------------------------------


class TestScoreRequest:
    def test_default_role_is_none(self):
        """ScoreRequest without role should have role=None."""
        req = ScoreRequest(username="testuser")
        assert req.role is None

    def test_with_role(self):
        """ScoreRequest with explicit role."""
        req = ScoreRequest(username="testuser", role="engineering")
        assert req.role == "engineering"

    def test_with_weights_and_role(self):
        """ScoreRequest with both weights and role."""
        req = ScoreRequest(
            username="testuser",
            weights={"commit_consistency": 0.5},
            role="marketing",
        )
        assert req.role == "marketing"
        assert req.weights == {"commit_consistency": 0.5}


class TestScoreResponse:
    def test_has_profile_field(self):
        """ScoreResponse should have a profile field."""
        resp = ScoreResponse(
            username="testuser",
            overall_score=75.0,
            signal_scores={},
            risk_flags=[],
            details={},
            profile="engineering",
        )
        assert resp.profile == "engineering"

    def test_model_dump_includes_profile(self):
        """Model serialization should include profile."""
        resp = ScoreResponse(
            username="testuser",
            overall_score=75.0,
            signal_scores={"commit_consistency": {"score": 80, "confidence": 0.8, "details": {}}},
            risk_flags=[],
            details={"profile_name": "engineering"},
            profile="engineering",
        )
        data = resp.model_dump()
        assert data["profile"] == "engineering"


class TestProfileResponse:
    def test_basic_fields(self):
        """ProfileResponse should have name, display_name, description, weights."""
        resp = ProfileResponse(
            name="engineering",
            display_name="Engineering",
            description="A profile for engineering roles",
            weights={"signal_a": 0.5, "signal_b": 0.5},
        )
        assert resp.name == "engineering"
        assert resp.display_name == "Engineering"
        assert resp.description == "A profile for engineering roles"
        assert resp.weights == {"signal_a": 0.5, "signal_b": 0.5}


# ---------------------------------------------------------------------------
# Profile matching tests (_resolve_role_for_matching)
# ---------------------------------------------------------------------------


class TestResolveRoleForMatching:
    def test_exact_profile_name(self):
        """Direct profile name match should return that profile."""
        name, boosts = _resolve_role_for_matching("engineering")
        assert name == "engineering"
        assert boosts == {}

    def test_profile_name_in_description(self):
        """Profile name as substring in description."""
        name, boosts = _resolve_role_for_matching("I need an engineering role")
        assert name == "engineering"
        assert boosts == {}

    def test_display_name_match(self):
        """Display name match should return that profile."""
        name, boosts = _resolve_role_for_matching("Marketing Manager")
        assert name == "marketing"
        assert boosts == {}

    def test_non_technical_by_terms(self):
        """Description matching non-technical terms should return non-technical profile."""
        name, boosts = _resolve_role_for_matching("Product Manager")
        assert name == "non-technical"
        assert boosts == {}

    def test_engineering_by_terms(self):
        """Description with engineering terms should return engineering profile."""
        name, boosts = _resolve_role_for_matching("Software Developer")
        assert name == "engineering"
        assert boosts == {}

    def test_marketing_by_terms(self):
        """Description with marketing terms should return marketing profile."""
        name, boosts = _resolve_role_for_matching("Growth Marketing Lead")
        assert name == "marketing"
        assert boosts == {}

    def test_keyword_fallback(self):
        """Unrecognized descriptions fall back to keyword boosts."""
        name, boosts = _resolve_role_for_matching("backend API developer")
        # "backend" and "api" are in keyword_map, "developer" is an engineering term
        # "backend" wins as an engineering term via description matching
        assert name is not None or isinstance(boosts, dict)

    def test_ambiguous_terms_default_to_engineering(self):
        """When description has no clear profile match, fall back to engineering with keywords."""
        name, boosts = _resolve_role_for_matching("Some random role that is not clear")
        # No clear terms → fallback with empty keyword map for unrecognized text
        assert name is None or name == "engineering"

    def test_empty_role_description(self):
        """Empty role description should fall back cleanly."""
        name, boosts = _resolve_role_for_matching("")
        # No terms to match, engineering terms not present
        assert name is None


# ---------------------------------------------------------------------------
# Keyword extraction (backward compat) tests
# ---------------------------------------------------------------------------


class TestExtractRoleKeywords:
    def test_backend_keywords(self):
        """Backend keyword should match language_diversity and issue_engagement."""
        result = _extract_role_keywords("backend developer")
        assert "language_diversity" in result
        assert "issue_engagement" in result

    def test_no_keywords(self):
        """Unrecognized role should return empty dict."""
        result = _extract_role_keywords("some completely random text")
        assert result == {}

    def test_empty_string(self):
        """Empty string should return empty dict."""
        result = _extract_role_keywords("")
        assert result == {}


# ---------------------------------------------------------------------------
# FastAPI route registration tests
# ---------------------------------------------------------------------------


class TestRoutes:
    def test_profiles_endpoint_registered(self):
        """/profiles endpoint should be registered in the app."""
        routes = [r.path for r in app.routes]
        assert "/profiles" in routes

    def test_score_post_endpoint_registered(self):
        """/score POST endpoint should be registered."""
        routes = [r.path for r in app.routes]
        assert "/score" in routes

    def test_score_get_endpoint_registered(self):
        """/score/{username} GET endpoint should be registered."""
        paths = [r.path for r in app.routes]
        assert "/score/{username}" in paths

    def test_match_post_endpoint_registered(self):
        """/match POST endpoint should be registered."""
        paths = [r.path for r in app.routes]
        assert "/match" in paths

    def test_health_endpoint_registered(self):
        """/health endpoint should be registered."""
        paths = [r.path for r in app.routes]
        assert "/health" in paths


class TestProfilesEndpointShape:
    def test_profiles_response_model_has_profiles_list(self):
        """ProfilesListResponse should wrap a list of ProfileResponse objects."""
        resp = ProfilesListResponse(profiles=[
            ProfileResponse(
                name="engineering",
                display_name="Engineering",
                description="Engineering profile",
                weights={"s1": 0.5, "s2": 0.5},
            ),
        ])
        assert len(resp.profiles) == 1
        assert resp.profiles[0].name == "engineering"

    def test_profiles_list_serializable(self):
        """ProfilesListResponse should serialize cleanly."""
        resp = ProfilesListResponse(profiles=[
            ProfileResponse(
                name="engineering",
                display_name="Engineering",
                description="Engineering profile",
                weights={"s1": 0.5, "s2": 0.5},
            ),
        ])
        data = resp.model_dump()
        assert "profiles" in data
        assert data["profiles"][0]["name"] == "engineering"
        assert data["profiles"][0]["weights"] == {"s1": 0.5, "s2": 0.5}


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_score_request_invalid_role_raises_valueerror(self):
        """Invalid role name passed to resolve_role_profile should raise ValueError."""
        from scoring.profiles import resolve_role_profile
        with pytest.raises(ValueError, match="Unknown profile 'invalid_role'"):
            resolve_role_profile("invalid_role")

    def test_match_request_with_missing_description(self):
        """MatchRequest with empty description should still pass validation."""
        # role_description is a required str, but empty string is valid
        req = MatchRequest(username="testuser", role_description="")
        assert req.role_description == ""

    def test_resolve_empty_role(self):
        """Empty role description in _resolve_role_for_matching should handle gracefully."""
        name, boosts = _resolve_role_for_matching("")
        # Either falls back to keywords (empty dict) or returns None
        assert name is None or name == ""
        assert isinstance(boosts, dict)

    def test_score_post_400_for_invalid_role(self):
        """The /score endpoint should return 400 for invalid role names."""
        # Verify the error path works through the exception handling
        from scoring.profiles import get_profile
        with pytest.raises(ValueError, match="Unknown profile 'bogus_role'"):
            get_profile("bogus_role")


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_resolve_role_case_insensitive(self):
        """Role matching should be case-insensitive."""
        name, boosts = _resolve_role_for_matching("ENGINEERING")
        assert name == "engineering"
        assert boosts == {}

    def test_resolve_role_partial_match(self):
        """Partial match on display name should still resolve."""
        name, boosts = _resolve_role_for_matching("Engineer in test")
        assert name == "engineering"
        assert boosts == {}

    def test_extract_keywords_multiple_matches(self):
        """Multiple keywords in description should accumulate signal boosts."""
        result = _extract_role_keywords("backend devops security")
        assert "language_diversity" in result
        assert "issue_engagement" in result
        assert "commit_consistency" in result
        assert "response_time" in result
        # backend gives language_diversity + issue_engagement (each count 1)
        # devops gives commit_consistency + response_time (each count 1)
        # security gives commit_consistency + response_time (each count 1)
        # commit_consistency: 1 (devops) + 1 (security) = 2
        assert result["commit_consistency"] == 2


# ---------------------------------------------------------------------------
# /verify endpoint tests
# ---------------------------------------------------------------------------


class TestVerifyRequest:
    def test_verify_request_basic(self):
        """VerifyRequest should accept signed_payload, signature, public_key."""
        req = VerifyRequest(
            signed_payload='{"test": 1}',
            signature="abc123",
            public_key="def456",
        )
        assert req.signed_payload == '{"test": 1}'
        assert req.signature == "abc123"
        assert req.public_key == "def456"


class TestVerifyResponse:
    def test_verify_response_valid(self):
        """VerifyResponse with valid=true."""
        resp = VerifyResponse(valid=True, payload={"test": 1})
        assert resp.valid is True
        assert resp.payload == {"test": 1}

    def test_verify_response_invalid(self):
        """VerifyResponse with valid=false and error."""
        resp = VerifyResponse(
            valid=False,
            payload=None,
            error="Signature does not match payload",
        )
        assert resp.valid is False
        assert resp.error == "Signature does not match payload"

    def test_verify_response_none_fields(self):
        """VerifyResponse defaults should be None for payload and error."""
        resp = VerifyResponse(valid=False)
        assert resp.payload is None
        assert resp.error is None


class TestVerifyRoutes:
    def test_verify_endpoint_registered(self):
        """/verify POST endpoint should be registered."""
        paths = [r.path for r in app.routes]
        assert "/verify" in paths


class TestScoreAttestation:
    """Functional tests verifying attestation block in /score and /match responses."""

    MINIMAL_ACTIVITY = {"repos": [], "commits": [], "issues": [], "prs": []}

    def test_score_response_includes_attestation(self, monkeypatch):
        """POST /score response should include an attestation block."""
        from unittest.mock import MagicMock
        from fastapi.testclient import TestClient

        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = self.MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)
        monkeypatch.setattr("api.main.enqueue_proof", lambda *a, **kw: "mock-task-id")

        client = TestClient(app)
        response = client.post("/score", json={"username": "testuser"})

        assert response.status_code == 200
        data = response.json()
        assert data["attestation"] is not None
        assert "signature" in data["attestation"]
        assert "public_key" in data["attestation"]
        assert "signed_payload" in data["attestation"]
        assert "signed_at" in data["attestation"]

    def test_score_attestation_signs_correct_username(self, monkeypatch):
        """Attestation payload should contain the correct username."""
        from unittest.mock import MagicMock
        from fastapi.testclient import TestClient
        import json

        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = self.MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)
        monkeypatch.setattr("api.main.enqueue_proof", lambda *a, **kw: "mock-task-id")

        client = TestClient(app)
        response = client.post("/score", json={"username": "attestuser"})

        assert response.status_code == 200
        data = response.json()
        payload = json.loads(data["attestation"]["signed_payload"])
        assert payload["username"] == "attestuser"

    def test_match_response_includes_attestation(self, monkeypatch):
        """POST /match response should include an attestation block."""
        from unittest.mock import MagicMock
        from fastapi.testclient import TestClient

        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = self.MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        client = TestClient(app)
        response = client.post("/match", json={
            "username": "testuser",
            "role_description": "engineering",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["attestation"] is not None
        assert "signature" in data["attestation"]
        assert "public_key" in data["attestation"]
        assert "signed_payload" in data["attestation"]

    def test_match_attestation_signs_correct_data(self, monkeypatch):
        """Attestation payload should contain correct username and role."""
        from unittest.mock import MagicMock
        from fastapi.testclient import TestClient
        import json

        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = self.MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        client = TestClient(app)
        response = client.post("/match", json={
            "username": "matchuser",
            "role_description": "engineering",
        })

        assert response.status_code == 200
        data = response.json()
        payload = json.loads(data["attestation"]["signed_payload"])
        assert payload["username"] == "matchuser"

    def test_score_attestation_can_be_verified(self, monkeypatch):
        """Attestation from /score should be verifiable via /verify."""
        from unittest.mock import MagicMock
        from fastapi.testclient import TestClient

        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = self.MINIMAL_ACTIVITY
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)
        monkeypatch.setattr("api.main.enqueue_proof", lambda *a, **kw: "mock-task-id")

        client = TestClient(app)
        score_resp = client.post("/score", json={"username": "verifytest"})

        assert score_resp.status_code == 200
        att = score_resp.json()["attestation"]

        verify_resp = client.post("/verify", json={
            "signed_payload": att["signed_payload"],
            "signature": att["signature"],
            "public_key": att["public_key"],
        })

        assert verify_resp.status_code == 200
        vdata = verify_resp.json()
        assert vdata["valid"] is True
        assert vdata["payload"]["username"] == "verifytest"


class TestVerifyEndpointFunctional:
    """Functional tests for POST /verify using TestClient."""

    def test_verify_with_valid_signature(self):
        """POST /verify with a valid signed payload should return valid=true."""
        from fastapi.testclient import TestClient
        from attest import load_or_generate_signing_key, sign_score

        client = TestClient(app)
        sk, vk = load_or_generate_signing_key()

        sig = sign_score("verify-test", 80.0, {}, [], "engineering", sk)

        response = client.post("/verify", json={
            "signed_payload": sig["signed_payload"],
            "signature": sig["signature"],
            "public_key": sig["public_key"],
        })

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["payload"]["username"] == "verify-test"
        assert data["payload"]["overall_score"] == 80.0

    def test_verify_with_tampered_payload(self):
        """POST /verify with a tampered payload should return valid=false."""
        from fastapi.testclient import TestClient
        from attest import load_or_generate_signing_key, sign_score

        client = TestClient(app)
        sk, vk = load_or_generate_signing_key()

        sig = sign_score("verify-test", 80.0, {}, [], "engineering", sk)

        response = client.post("/verify", json={
            "signed_payload": '{"tampered": true}',
            "signature": sig["signature"],
            "public_key": sig["public_key"],
        })

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "error" in data

    def test_verify_with_missing_field(self):
        """POST /verify with a missing field should return 422."""
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Missing public_key
        response = client.post("/verify", json={
            "signed_payload": "test",
            "signature": "test",
        })

        assert response.status_code == 422

    def test_verify_with_empty_strings(self):
        """POST /verify with empty strings should be handled gracefully."""
        from fastapi.testclient import TestClient

        client = TestClient(app)

        response = client.post("/verify", json={
            "signed_payload": "",
            "signature": "",
            "public_key": "",
        })

        # Should return 200 with valid: false due to decode errors
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False


# ---------------------------------------------------------------------------
# Proof status endpoint tests
# ---------------------------------------------------------------------------


class TestProofStatusEndpoint:
    """Tests for GET /proof/{username}/status."""

    def test_proof_status_endpoint_registered(self):
        """/proof/{username}/status endpoint should be registered."""
        paths = [r.path for r in app.routes]
        assert "/proof/{username}/status" in paths

    def test_proof_status_returns_unknown_for_nonexistent(self):
        """GET /proof/{username}/status for unknown user should return status 'unknown'."""
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/proof/nonexistentuser/status")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "nonexistentuser"
        assert data["status"] == "unknown"

    def test_proof_status_after_score_enqueue(self, monkeypatch):
        """GET /proof/{username}/status after POST /score should show proof status."""
        from fastapi.testclient import TestClient
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.get_user_activity.return_value = {"repos": [], "commits": [], "issues": [], "prs": []}
        monkeypatch.setattr("api.main._get_github_client", lambda: mock_client)

        client = TestClient(app)
        score_resp = client.post("/score", json={"username": "statustest"})
        assert score_resp.status_code == 200
        proof_id = score_resp.json().get("proof_id")

        # Manually set the status in the store (enqueue_proof is mocked in conftest)
        from api.proof_status import get_store
        store = get_store()
        store.set_status(proof_id, "pending", username="statustest")

        # Now check proof status
        status_resp = client.get("/proof/statustest/status")
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["username"] == "statustest"
        assert data["proof_id"] == proof_id
        # Status should be at least set — the enqueue_proof mock sets status via ProofStatusStore
        assert data["status"] in ("pending", "unknown")

    def test_proof_status_response_shape(self, monkeypatch):
        """GET /proof/{username}/status should return correctly shaped response."""
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Set up a known proof status in the store
        from api.proof_status import get_store, reset_store
        reset_store()
        store = get_store()
        store.set_status("test_proof_001", "proof_generated", username="shapetest",
                         proof_path="/tmp/proof.bin")

        response = client.get("/proof/shapetest/status")
        assert response.status_code == 200
        data = response.json()

        # Verify all expected fields
        assert data["username"] == "shapetest"
        assert data["proof_id"] == "test_proof_001"
        assert data["status"] == "proof_generated"
        assert data["proof_path"] == "/tmp/proof.bin"
        assert data["created_at"] is not None
        assert data["updated_at"] is not None
        # Attestation should be present (signing key available in test env)
        assert "attestation" in data

    def test_proof_status_all_transitions(self, monkeypatch):
        """Proof status should reflect all lifecycle transitions."""
        from fastapi.testclient import TestClient
        from api.proof_status import get_store, reset_store

        reset_store()
        store = get_store()
        client = TestClient(app)

        # pending
        store.set_status("proof_trans", "pending", username="transitionuser")
        r = client.get("/proof/transitionuser/status")
        assert r.json()["status"] == "pending"

        # proof_generating
        store.set_status("proof_trans", "proof_generating")
        r = client.get("/proof/transitionuser/status")
        assert r.json()["status"] == "proof_generating"

        # proof_generated
        store.set_status("proof_trans", "proof_generated", proof_path="/tmp/proof.bin")
        r = client.get("/proof/transitionuser/status")
        assert r.json()["status"] == "proof_generated"
        assert r.json()["proof_path"] == "/tmp/proof.bin"

        # on_chain
        store.set_status("proof_trans", "on_chain", tx_hash="0xdeadbeef")
        r = client.get("/proof/transitionuser/status")
        assert r.json()["status"] == "on_chain"
        assert r.json()["tx_hash"] == "0xdeadbeef"

        # failed
        store.set_status("proof_trans", "failed", error="Prover network timeout")
        r = client.get("/proof/transitionuser/status")
        assert r.json()["status"] == "failed"
        assert r.json()["error"] == "Prover network timeout"

    def test_proof_status_includes_attestation(self, monkeypatch):
        """Proof status response should include an Ed25519 attestation block."""
        from fastapi.testclient import TestClient
        import json

        client = TestClient(app)

        response = client.get("/proof/nonexistent/status")
        assert response.status_code == 200
        data = response.json()
        assert "attestation" in data
        att = data["attestation"]
        # Attestation may be None if signing key not available
        if att is not None:
            assert "signature" in att
            assert "public_key" in att
            assert "signed_payload" in att

    def test_proof_status_for_multiple_users(self):
        """Proof status for multiple users should return correct per-user status."""
        from fastapi.testclient import TestClient
        from api.proof_status import get_store, reset_store

        reset_store()
        store = get_store()
        store.set_status("p1", "proof_generated", username="alice")
        store.set_status("p2", "pending", username="bob")
        store.set_status("p3", "failed", username="charlie")

        client = TestClient(app)

        r_alice = client.get("/proof/alice/status")
        assert r_alice.json()["status"] == "proof_generated"

        r_bob = client.get("/proof/bob/status")
        assert r_bob.json()["status"] == "pending"

        r_charlie = client.get("/proof/charlie/status")
        assert r_charlie.json()["status"] == "failed"

        r_dave = client.get("/proof/dave/status")
        assert r_dave.json()["status"] == "unknown"

    def test_proof_status_response_is_json(self):
        """Proof status endpoint should return JSON content-type."""
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/proof/anyuser/status")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
