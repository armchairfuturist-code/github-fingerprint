"""
Privy Wallet Provider — REST API wrapper for Privy wallet creation.

Uses the Privy REST API (https://api.privy.io/v1/wallets) to create Ethereum
wallets on demand. Each wallet is owned by an authorization key (server-side),
not tied to a user session.

Credentials are loaded from environment variables:
    PRIVY_APP_ID — Privy application ID
    PRIVY_APP_SECRET — Privy application secret

When credentials are unavailable or the API call fails, the provider returns
None and logs a warning — the caller is expected to handle graceful
degradation.
"""
import base64
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

PRIVY_API_BASE = "https://api.privy.io"
WALLET_CREATE_URL = f"{PRIVY_API_BASE}/v1/wallets"
WALLET_GET_URL = f"{PRIVY_API_BASE}/v1/wallets/{{wallet_id}}"
DEFAULT_CHAIN_TYPE = "ethereum"


def _get_credentials() -> Optional[Dict[str, str]]:
    """Return Privy app credentials or None if not configured."""
    app_id = os.getenv("PRIVY_APP_ID")
    app_secret = os.getenv("PRIVY_APP_SECRET")
    if not app_id or not app_secret:
        logger.debug("PRIVY_APP_ID or PRIVY_APP_SECRET not set — wallet creation disabled")
        return None
    return {"app_id": app_id, "app_secret": app_secret}


def _build_auth_header(app_id: str, app_secret: str) -> str:
    """Build the Basic Auth header value for Privy API."""
    raw = f"{app_id}:{app_secret}"
    encoded = base64.b64encode(raw.encode()).decode()
    return f"Basic {encoded}"


def create_wallet(
    username: str,
    chain_type: str = DEFAULT_CHAIN_TYPE,
) -> Optional[Dict[str, Any]]:
    """Create a Privy wallet for the given username.

    The wallet is owned by the application's authorization key (server-side),
    not tied to a specific user session. The ``external_id`` field is set to
    the GitHub username for cross-referencing.

    Args:
        username: GitHub username (used as external_id).
        chain_type: Blockchain type (default: "ethereum").

    Returns:
        Dict with keys ``wallet_id``, ``address``, ``chain_type``,
        ``created_at`` (ISO string), or None on failure.
    """
    creds = _get_credentials()
    if creds is None:
        logger.info(
            "Privy credentials not configured — skipping wallet creation for user=%s",
            username,
        )
        return None

    headers = {
        "Authorization": _build_auth_header(creds["app_id"], creds["app_secret"]),
        "privy-app-id": creds["app_id"],
        "Content-Type": "application/json",
    }

    payload = {
        "chain_type": chain_type,
        "external_id": username,
    }

    try:
        resp = requests.post(
            WALLET_CREATE_URL,
            headers=headers,
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        created_at_ms = data.get("created_at", 0)
        if created_at_ms:
            created_at_iso = datetime.fromtimestamp(
                created_at_ms / 1000, tz=timezone.utc
            ).isoformat()
        else:
            created_at_iso = datetime.now(timezone.utc).isoformat()

        wallet_data = {
            "wallet_id": data["id"],
            "address": data["address"],
            "chain_type": data.get("chain_type", chain_type),
            "created_at": created_at_iso,
        }

        logger.info(
            "wallet_created: user=%s wallet_id=%s address=%s",
            username,
            wallet_data["wallet_id"],
            wallet_data["address"][:10],
        )
        return wallet_data

    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 0
        detail = exc.response.text if exc.response is not None else str(exc)
        if status == 401:
            logger.error("Privy API authentication failed (401) — check PRIVY_APP_ID / PRIVY_APP_SECRET")
        elif status == 409:
            logger.warning("Privy wallet already exists for user=%s — attempting to use existing", username)
            # 409 typically means a wallet with this external_id already exists
            # Fall through to return None; caller treats as non-fatal
            return None
        else:
            logger.error(
                "Privy API error creating wallet: user=%s status=%d detail=%s",
                username, status, detail[:200],
            )
        return None

    except requests.exceptions.RequestException as exc:
        logger.error(
            "Privy network error creating wallet: user=%s error=%s",
            username, exc,
        )
        return None


def get_wallet(wallet_id: str) -> Optional[Dict[str, Any]]:
    """Get wallet details from Privy by wallet ID.

    Args:
        wallet_id: Privy wallet ID.

    Returns:
        Dict with wallet details, or None on failure.
    """
    creds = _get_credentials()
    if creds is None:
        return None

    headers = {
        "Authorization": _build_auth_header(creds["app_id"], creds["app_secret"]),
        "privy-app-id": creds["app_id"],
        "Content-Type": "application/json",
    }

    try:
        resp = requests.get(
            WALLET_GET_URL.format(wallet_id=wallet_id),
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as exc:
        logger.error("Failed to get wallet %s: %s", wallet_id, exc)
        return None


def is_available() -> bool:
    """Return True when Privy credentials are configured."""
    return _get_credentials() is not None
