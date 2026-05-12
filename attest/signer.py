"""
Attestation Signer
Ed25519 signing and verification for score attestations.
"""
import base64
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

logger = logging.getLogger(__name__)

SIGNED_AT_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _build_canonical_payload(
    username: str,
    overall_score: float,
    signal_scores: Dict[str, Any],
    risk_flags: List[str],
    profile_name: str,
    signed_at: str,
) -> str:
    """
    Build a deterministic JSON payload with sorted keys.

    signal_scores keys are sorted alphabetically; risk_flags are sorted
    lexicographically. This ensures that the same semantic data always
    produces the same serialized string regardless of insertion order.
    """
    # Normalise signal_scores: if values are dicts (not SignalResult objects
    # or other rich types), sort their keys too.
    normalised_signals: Dict[str, Any] = {}
    for name in sorted(signal_scores.keys()):
        val = signal_scores[name]
        if isinstance(val, dict):
            normalised_signals[name] = dict(sorted(val.items()))
        else:
            # For SignalResult or other objects, convert to dict if possible
            # and sort keys.
            if hasattr(val, "__dataclass_fields__"):
                normalised_signals[name] = dict(
                    sorted(
                        {
                            k: getattr(val, k)
                            for k in val.__dataclass_fields__
                        }.items()
                    )
                )
            else:
                normalised_signals[name] = val

    payload: Dict[str, Any] = {
        "username": username,
        "overall_score": overall_score,
        "signal_scores": normalised_signals,
        "risk_flags": sorted(risk_flags),
        "profile_name": profile_name,
        "signed_at": signed_at,
    }

    # Serialise with sorted keys, no extra whitespace, ensure_ascii for
    # maximum cross-platform reproducibility.
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def sign_score(
    username: str,
    overall_score: float,
    signal_scores: Dict[str, Any],
    risk_flags: List[str],
    profile_name: str,
    private_key: SigningKey,
) -> Dict[str, str]:
    """
    Sign a score payload with an Ed25519 signing key.

    Args:
        username: The GitHub username being scored.
        overall_score: The overall score (float in [0, 100]).
        signal_scores: Dict of signal name -> signal value (dict or
                       SignalResult-like object).
        risk_flags: List of risk flag strings.
        profile_name: The role profile used (e.g. 'engineering').
        private_key: A nacl.signing.SigningKey instance.

    Returns:
        Dict with keys:
          - signature (base64-encoded Ed25519 signature)
          - public_key (base64-encoded 32-byte verify key)
          - signed_payload (canonical JSON string)
          - signed_at (ISO 8601 UTC timestamp)
    """
    signed_at = datetime.now(timezone.utc).strftime(SIGNED_AT_FORMAT)

    payload_str = _build_canonical_payload(
        username=username,
        overall_score=overall_score,
        signal_scores=signal_scores,
        risk_flags=risk_flags,
        profile_name=profile_name,
        signed_at=signed_at,
    )

    payload_bytes = payload_str.encode("utf-8")
    signed = private_key.sign(payload_bytes)
    signature_b64 = base64.b64encode(bytes(signed.signature)).decode("ascii")
    public_key_b64 = base64.b64encode(
        bytes(private_key.verify_key)
    ).decode("ascii")

    logger.info(
        "Signed score for user=%s overall=%.1f profile=%s "
        "signature_prefix=%s public_key_prefix=%s",
        username,
        overall_score,
        profile_name,
        signature_b64[:12],
        public_key_b64[:12],
    )

    return {
        "signature": signature_b64,
        "public_key": public_key_b64,
        "signed_payload": payload_str,
        "signed_at": signed_at,
    }


def _decode_key(data: Union[str, bytes]) -> bytes:
    """Decode a key or signature from base64 or pass through raw bytes."""
    if isinstance(data, bytes):
        return data
    try:
        return base64.b64decode(data)
    except (ValueError, base64.binascii.Error):
        # Not valid base64 — caller passed raw bytes as a str repr
        raise


def verify_attestation(
    signed_payload: str,
    signature: Union[str, bytes],
    public_key: Union[str, bytes],
) -> Dict[str, Any]:
    """
    Verify an Ed25519 attestation signature.

    Args:
        signed_payload: The canonical JSON string that was signed.
        signature: Base64-encoded Ed25519 signature (str or raw bytes).
        public_key: Base64-encoded 32-byte Ed25519 verify key
                    (str or raw bytes).

    Returns:
        Dict with keys:
          - valid (bool): True if the signature is valid.
          - payload (dict): Parsed payload dict (on success or failure).
          - error (str, optional): Error message if verification fails.
    """
    try:
        vk_bytes = _decode_key(public_key)
        sig_bytes = _decode_key(signature)
        payload_bytes = signed_payload.encode("utf-8")

        verify_key = VerifyKey(vk_bytes)
        verify_key.verify(payload_bytes, sig_bytes)

        parsed = json.loads(signed_payload)

        logger.info(
            "Attestation VERIFIED for user=%s overall=%.1f",
            parsed.get("username", "?"),
            parsed.get("overall_score", -1),
        )

        return {"valid": True, "payload": parsed}

    except BadSignatureError:
        logger.warning("Attestation signature INVALID")
        parsed = _try_parse_payload(signed_payload)
        return {
            "valid": False,
            "payload": parsed,
            "error": "Signature does not match payload",
        }
    except (ValueError, json.JSONDecodeError, base64.binascii.Error) as exc:
        logger.warning("Attestation verification failed: %s", exc)
        parsed = _try_parse_payload(signed_payload)
        return {
            "valid": False,
            "payload": parsed,
            "error": f"Verification error: {exc}",
        }


def _try_parse_payload(signed_payload: str) -> Any:
    """Best-effort JSON parse; returns None on failure."""
    try:
        return json.loads(signed_payload)
    except json.JSONDecodeError:
        return None
