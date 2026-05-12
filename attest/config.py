"""
Attestation Configuration
Key loading and management for Ed25519 signing.
"""
import base64
import logging
import os
from typing import Optional, Tuple

from nacl.signing import SigningKey

logger = logging.getLogger(__name__)

ENV_KEY_NAME = "ATTEST_PRIVATE_KEY"


def load_or_generate_signing_key(
    key_path: Optional[str] = None,
) -> Tuple[SigningKey, bytes]:
    """
    Load a signing key from an environment variable or auto-generate one.

    Resolution order:
      1. If key_path is provided, read the raw 32-byte seed from that file.
      2. Otherwise, read ATTEST_PRIVATE_KEY from the environment (base64-encoded
         32-byte Ed25519 seed).
      3. If neither is available, generate a fresh key in-memory (session-only).

    Args:
        key_path: Optional filesystem path to a raw 32-byte seed file.

    Returns:
        Tuple of (SigningKey, verify_key_bytes) where verify_key_bytes is the
        raw 32-byte public key that callers can embed in signed payloads for
        self-contained verification.
    """
    seed: Optional[bytes] = None

    if key_path is not None:
        try:
            with open(key_path, "rb") as f:
                seed = f.read(32)
            logger.info(
                "Loaded signing key from file: %s "
                "(first 4 bytes hex: %s)",
                key_path,
                seed[:4].hex(),
            )
        except (FileNotFoundError, PermissionError, OSError) as exc:
            logger.warning(
                "Could not load signing key from %s: %s. "
                "Falling back to env var or generation.",
                key_path,
                exc,
            )
            seed = None

    if seed is None:
        env_b64 = os.environ.get(ENV_KEY_NAME)
        if env_b64:
            try:
                seed = base64.b64decode(env_b64)
                if len(seed) != 32:
                    raise ValueError(
                        f"Expected 32 bytes, got {len(seed)}"
                    )
                logger.info(
                    "Loaded signing key from env var %s "
                    "(first 4 bytes hex: %s)",
                    ENV_KEY_NAME,
                    seed[:4].hex(),
                )
            except (ValueError, base64.binascii.Error) as exc:
                logger.warning(
                    "Invalid ATTEST_PRIVATE_KEY value: %s. "
                    "Generating fresh key.",
                    exc,
                )
                seed = None

    if seed is None:
        signing_key = SigningKey.generate()
        logger.warning(
            "No signing key configured (env %s not set or invalid). "
            "Generated ephemeral session key. "
            "Attestation will work but signatures will not be reproducible "
            "across restarts.",
            ENV_KEY_NAME,
        )
    else:
        signing_key = SigningKey(seed)

    verify_key_bytes = bytes(signing_key.verify_key)
    logger.info(
        "Signing key ready. Public key (first 8 bytes hex): %s",
        verify_key_bytes[:8].hex(),
    )

    return signing_key, verify_key_bytes
