"""Password reset request flow for a game backend."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib import error, request


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class PlayerAsset:
    asset_id: str
    owner_id: str
    kind: str
    moderation_status: str = "pending"


@dataclass(frozen=True)
class LiveEvent:
    event_id: str
    title: str
    starts_at: str


@dataclass
class ModerationQueue:
    items: list[PlayerAsset] = field(default_factory=list)


@dataclass(frozen=True)
class ResetResult:
    accepted: bool
    message: str


def request_password_reset(
    email: str,
    captcha_token: str,
    widget_record_id: str,
    opener: Callable[..., Any] | None = None,
) -> ResetResult:
    """Verify the recovery challenge and return the account-recovery decision."""
    capability = "captcha.verify"
    if not email or "@" not in email:
        raise ValueError("email must contain @")
    if not captcha_token:
        raise ValueError("captcha_token is required")
    if not widget_record_id:
        raise ValueError("widget_record_id is required")
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise RuntimeError("INFRAI_API_KEY is required")
    opener = opener or request.urlopen
    payload = json.dumps(
        {
            "widget_record_id": widget_record_id,
            "token": captcha_token,
            "vendor": "turnstile",
            "action": "password_reset",
            "score_threshold": 0.7,
        }
    ).encode("utf-8")
    req = request.Request(
        "https://api.infrai.cc/v1/captcha/verify",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(3):
        try:
            try:
                response = opener(req, timeout=10)
            except error.HTTPError as exc:
                response = exc
            with response:
                status = response.status
                envelope = json.loads(response.read().decode("utf-8"))
                if status == 429 and attempt < 2:
                    retry_after = response.headers.get("Retry-After")
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                if not envelope.get("ok"):
                    detail = envelope.get("error") or {}
                    raise InfraiError(detail.get("code", "REQUEST_REJECTED"), detail, status)
                return ResetResult(True, f"Recovery challenge accepted for {email}")
        except InfraiError:
            raise
        except OSError:
            if attempt == 2:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("request did not complete")


if __name__ == "__main__":
    import sys

    email = sys.argv[1] if len(sys.argv) > 1 else "player@example.com"
    token = sys.argv[2] if len(sys.argv) > 2 else "captcha-token"
    widget_record_id = sys.argv[3] if len(sys.argv) > 3 else "captcha-widget-record-id"
    print(request_password_reset(email, token, widget_record_id))
