import time

import pytest
from fastapi import HTTPException

from app.security import sign_payload, verify_internal


def test_hmac_roundtrip(monkeypatch):
    from app import security
    monkeypatch.setattr(security.settings, "nido_webhook_secret", "abc123")
    body = b"{}"
    ts = str(int(time.time()))
    verify_internal(ts, sign_payload("abc123", ts, body), body)


def test_hmac_rejects_bad_signature(monkeypatch):
    from app import security
    monkeypatch.setattr(security.settings, "nido_webhook_secret", "abc123")
    with pytest.raises(HTTPException):
        verify_internal(str(int(time.time())), "sha256=bad", b"{}")
