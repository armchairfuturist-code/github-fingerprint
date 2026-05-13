import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock


class TestWalletStore:
    @pytest.fixture
    def store_path(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        yield path
        if os.path.isfile(path):
            os.remove(path)

    @pytest.fixture
    def store(self, store_path):
        from wallet.store import WalletStore
        return WalletStore(path=store_path)

    def test_set_and_get(self, store):
        d = {"wallet_id": "t1", "address": "0xabc"}
        store.set_wallet("u", d)
        assert store.get_by_username("u")["wallet_id"] == "t1"

    def test_unknown(self, store):
        assert store.get_by_username("x") is None

    def test_add_hash(self, store):
        store.add_attestation_hash("u", "h1")
        assert "h1" in store.get_by_username("u")["attestation_hashes"]

    def test_dedup(self, store):
        store.add_attestation_hash("u", "h1")
        store.add_attestation_hash("u", "h1")
        assert len(store.get_by_username("u")["attestation_hashes"]) == 1

    def test_multiple(self, store):
        store.add_attestation_hash("u", "h1")
        store.add_attestation_hash("u", "h2")
        assert len(store.get_by_username("u")["attestation_hashes"]) == 2

    def test_persistence(self, store_path):
        from wallet.store import WalletStore
        WalletStore(path=store_path).set_wallet("u", {"id": "w1"})
        r = WalletStore(path=store_path).get_by_username("u")
        assert r["id"] == "w1"

    def test_all_users(self, store):
        store.set_wallet("a", {"id": "1"})
        store.set_wallet("b", {"id": "2"})
        assert len(store.all_usernames()) == 2


class TestWalletProvider:
    @pytest.fixture(autouse=True)
    def clear_env(self):
        old_id = os.environ.pop("PRIVY_APP_ID", None)
        old_secret = os.environ.pop("PRIVY_APP_SECRET", None)
        yield
        if old_id: os.environ["PRIVY_APP_ID"] = old_id
        if old_secret: os.environ["PRIVY_APP_SECRET"] = old_secret

    def test_unavailable_without_creds(self):
        from wallet.provider import is_available
        assert is_available() is False

    def test_available_with_creds(self):
        from wallet.provider import is_available
        os.environ["PRIVY_APP_ID"] = "id"
        os.environ["PRIVY_APP_SECRET"] = "secret"
        assert is_available() is True

    def test_create_none_without_creds(self):
        from wallet.provider import create_wallet
        assert create_wallet("u") is None

    def test_create_success(self):
        import requests
        from wallet.provider import create_wallet
        os.environ["PRIVY_APP_ID"] = "id"
        os.environ["PRIVY_APP_SECRET"] = "secret"
        mock = MagicMock()
        mock.json.return_value = {"id": "w123", "address": "0xabc", "chain_type": "ethereum", "created_at": 1741834854578}
        mock.raise_for_status.return_value = None
        with patch("wallet.provider.requests.post", return_value=mock) as mp:
            r = create_wallet("u")
        assert r["wallet_id"] == "w123"
        assert r["address"] == "0xabc"
        assert mp.call_args[1]["json"]["external_id"] == "u"

    def test_create_http_error(self):
        import requests
        from wallet.provider import create_wallet
        os.environ["PRIVY_APP_ID"] = "id"
        os.environ["PRIVY_APP_SECRET"] = "secret"
        mock = MagicMock(status_code=401, text="Unauthorized")
        mock.raise_for_status.side_effect = requests.exceptions.HTTPError("401", response=mock)
        with patch("wallet.provider.requests.post", return_value=mock):
            assert create_wallet("u") is None

    def test_create_409(self):
        import requests
        from wallet.provider import create_wallet
        os.environ["PRIVY_APP_ID"] = "id"
        os.environ["PRIVY_APP_SECRET"] = "secret"
        mock = MagicMock(status_code=409, text="exists")
        mock.raise_for_status.side_effect = requests.exceptions.HTTPError("409", response=mock)
        with patch("wallet.provider.requests.post", return_value=mock):
            assert create_wallet("u") is None


class TestWalletAPI:
    @pytest.fixture(autouse=True)
    def setup(self):
        from fastapi.testclient import TestClient
        from wallet.store import WalletStore, _store_lock
        import wallet.store as ws
        self.saved = ws._store_instance
        self.tmp = tempfile.mktemp(suffix=".json")
        self.ts = WalletStore(path=self.tmp)
        with _store_lock:
            ws._store_instance = self.ts
        from api.main import app
        self.client = TestClient(app)
        yield
        with _store_lock:
            ws._store_instance = self.saved
        if os.path.isfile(self.tmp):
            os.remove(self.tmp)

    def test_not_found(self):
        r = self.client.get("/wallet/x/status")
        assert r.status_code == 200
        assert r.json()["status"] == "not_found"

    def test_exists(self):
        self.ts.set_wallet("u", {"wallet_id": "w1", "address": "0xa", "chain_type": "eth", "created_at": "2026-01-01", "attestation_hashes": ["h1"]})
        r = self.client.get("/wallet/u/status")
        assert r.json()["status"] == "exists"
        assert r.json()["wallet_id"] == "w1"


class TestWalletScoreFlow:
    @pytest.fixture(autouse=True)
    def setup(self):
        from wallet.store import _store_lock, WalletStore
        import wallet.store as ws
        self.saved = ws._store_instance
        self.tmp = tempfile.mktemp(suffix=".json")
        self.ts = WalletStore(path=self.tmp)
        with _store_lock:
            ws._store_instance = self.ts
        yield
        with _store_lock:
            ws._store_instance = self.saved
        if os.path.isfile(self.tmp):
            os.remove(self.tmp)

    @patch("wallet.create_wallet", return_value={"wallet_id": "w1", "address": "0x1"})
    def test_creates_and_stores(self, mc):
        from api.main import _create_wallet_for_user
        _create_wallet_for_user("u")
        assert self.ts.get_by_username("u")["wallet_id"] == "w1"

    @patch("wallet.create_wallet", return_value=None)
    def test_handles_failure(self, mc):
        from api.main import _create_wallet_for_user
        _create_wallet_for_user("u")
        assert self.ts.get_by_username("u") is None

    @patch("wallet.create_wallet", return_value={"wallet_id": "w1", "address": "0x1"})
    def test_with_attestation(self, mc):
        from api.main import _create_wallet_for_user
        _create_wallet_for_user("u", {"signature": "sig_abc"})
        assert len(self.ts.get_by_username("u")["attestation_hashes"]) == 1

    @patch("wallet.create_wallet")
    def test_idempotent(self, mc):
        from api.main import _create_wallet_for_user
        self.ts.set_wallet("u", {"wallet_id": "w_existing"})
        _create_wallet_for_user("u")
        mc.assert_not_called()
