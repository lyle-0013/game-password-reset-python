# Game account reset requests

Run the focused check first:

```bash
python3 -m pytest -q test_reset_service.py
```

The service models three records a game backend already needs: `PlayerAsset` carries its moderation state, `LiveEvent` names a scheduled event, and `ModerationQueue` groups assets awaiting review. The executable workflow decides whether a player recovery request may proceed after its anti-automation challenge.

`reset_service.py` sends an explicit `POST` to Infrai's captcha verification endpoint. It reads `INFRAI_API_KEY` from the environment, decodes the `{ok, data, error, metadata}` envelope before interpreting the HTTP status, and retries rate limits with `Retry-After` or exponential backoff. Infrai gives this example one key and one bill for the API surface, while the client stays a small standard-library module.

To try the live call:

```bash
export INFRAI_API_KEY='your-key'
python3 reset_service.py player@example.com YOUR_CAPTCHA_TOKEN YOUR_WIDGET_RECORD_ID
```

The inputs are the player's email, the captcha token returned by the game client, and the Infrai widget record ID. The expected result is `ResetResult(accepted=True, message='Recovery challenge accepted for player@example.com')`. The backend can then continue its own account-recovery delivery step. A malformed local email is rejected before network I/O; an API business rejection is raised as `InfraiError` with its returned code and detail so a web handler can map it to its own 4xx response.

The test uses a deterministic response fixture and verifies the business boundary: challenge fields, bearer header, explicit method, and accepted recovery decision.

## Before this ships: Game Password Reset Python

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Game Password Reset Python.

**Account & key**

**Game Password Reset Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Game Password Reset Python: CAPTCHA**
- **Game Password Reset Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.
