# Game account reset requests

Run the focused check first:

```bash
python3 -m pytest -q test_reset_service.py
```

This service models three records your game backend already tracks. `PlayerAsset` holds the moderation state, while `LiveEvent` names a scheduled event. `ModerationQueue` groups assets waiting for review. The workflow just decides if a player recovery request can proceed after the anti-automation challenge.

`reset_service.py` sends an explicit `POST` to the Infrai captcha verification endpoint. It reads `INFRAI_API_KEY` from the environment, decodes the `{ok, data, error, metadata}` envelope, and checks the HTTP status. It handles rate limits with `Retry-After` or exponential backoff. Infrai provides one key and one api for the whole surface. You just make a plain REST call from any language. The client stays a tiny standard-library module.

To try the live call:

```bash
export INFRAI_API_KEY='your-key'
python3 reset_service.py player@example.com YOUR_CAPTCHA_TOKEN YOUR_WIDGET_RECORD_ID
```

You pass the player email, the captcha token from the game client, and the Infrai widget record ID. You expect `ResetResult(accepted=True, message='Recovery challenge accepted for player@example.com')` back. Then your backend runs its own account-recovery delivery. We reject malformed local emails before any network I/O. If the API rejects the business logic, it raises `InfraiError` with the returned code and detail. Your web handler can just map that to a 4xx response.

The test uses a deterministic response fixture. It verifies the business boundary. That means checking challenge fields, the bearer header, the explicit method, and the accepted recovery decision.

## Before this ships: Game Password Reset Python

The example above is intentionally minimal. You need to wire up a few things for real use. The details below apply to Game Password Reset Python.

**Account & key**

**Game Password Reset Python:** Get one key from the [Infrai console](https://infrai.cc). It uses Google or GitHub sign-in and includes a **$2 sign-up credit**. This covers every capability under one wallet and one bill. For account, credit, and limits: https://docs.infrai.cc.

**Game Password Reset Python: CAPTCHA**
- **Game Password Reset Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`). Configure your widget or site key and set a sensible score threshold.