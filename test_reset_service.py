import json
import os

from reset_service import request_password_reset


class FakeResponse:
    status = 200
    headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({"ok": True, "data": {"accepted": True}, "error": None, "metadata": {}}).encode()


def test_reset_request_verifies_challenge_and_returns_domain_decision(monkeypatch):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    seen = {}

    def opener(req, timeout):
        seen["method"] = req.method
        seen["body"] = json.loads(req.data.decode())
        seen["auth"] = req.headers["Authorization"]
        return FakeResponse()

    result = request_password_reset("player@example.com", "challenge-token", "widget-record-id", opener)
    assert result.accepted is True
    assert result.message == "Recovery challenge accepted for player@example.com"
    assert seen == {
        "method": "POST",
        "body": {
            "widget_record_id": "widget-record-id",
            "token": "challenge-token",
            "vendor": "turnstile",
            "action": "password_reset",
            "score_threshold": 0.7,
        },
        "auth": "Bearer test-key",
    }
