import hashlib
import hmac
import time

from fastapi import HTTPException

from .config import get_settings

settings = get_settings()


def sign_payload(secret: str, timestamp: str, body: bytes) -> str:
    digest = hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_internal(timestamp: str | None, signature: str | None, body: bytes) -> None:
    if not timestamp or not signature:
        raise HTTPException(401, "Missing webhook signature")
    try:
        stamp = int(timestamp)
    except ValueError as exc:
        raise HTTPException(401, "Invalid webhook timestamp") from exc
    if abs(time.time() - stamp) > 300:
        raise HTTPException(401, "Webhook timestamp outside replay window")
    expected = sign_payload(settings.nido_webhook_secret, timestamp, body)
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(401, "Invalid webhook signature")
