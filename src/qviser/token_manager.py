"""Automatic renewal of the Dhan access token (GET /v2/RenewToken).

Dhan Web tokens are valid for 24 hours and can only be renewed while still
active. Renewing expires the current token and returns a new one valid for
another 24 hours, so the new token is written back to the .env file.
"""

import base64
import json
import logging
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dhanhq.auth import DhanLogin

from qviser.config import Settings
from qviser.config.settings import ENV_FILE

logger = logging.getLogger(__name__)

ENV_KEY = "DHAN_ACCESS_TOKEN"

# If the new token can't be found in the renewal response, the raw response is
# saved here (owner-only permissions, gitignored) so the token is not lost.
UNPARSED_RESPONSE_FILE = Path(".dhan_renew_response.json")

_JWT_RE = re.compile(r"^[\w-]+\.[\w-]+\.[\w-]+$")


class TokenRenewalError(RuntimeError):
    """Raised when the access token can't be renewed or saved."""


def token_expiry(token: str) -> datetime:
    """Return the expiry time (UTC) from the JWT's `exp` claim; no signature check."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload))
        return datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
    except (IndexError, KeyError, ValueError, TypeError) as exc:
        raise TokenRenewalError("Access token is not a JWT with an 'exp' claim") from exc


def ensure_fresh_token(settings: Settings) -> str:
    """Return a usable access token, renewing it first if it expires soon."""
    token = settings.dhan_access_token.get_secret_value()
    expires_at = token_expiry(token)
    remaining = expires_at - datetime.now(timezone.utc)
    renew_window = timedelta(hours=settings.dhan_token_renew_before_hours)

    if remaining <= timedelta(0):
        raise TokenRenewalError(
            f"Access token expired at {expires_at:%Y-%m-%d %H:%M %Z}; expired tokens can't be "
            f"renewed. Generate a new one on Dhan Web and update {ENV_KEY} in {ENV_FILE}."
        )
    if not settings.dhan_token_auto_renew or remaining > renew_window:
        logger.info("Access token valid until %s", expires_at.astimezone())
        return token

    logger.info(
        "Access token expires in %s (renewal window %s); renewing",
        _format_duration(remaining),
        _format_duration(renew_window),
    )
    new_token = _renew(settings.dhan_client_id, token, expires_at)
    _save_token(new_token)
    logger.info("Access token renewed; valid until %s", token_expiry(new_token).astimezone())
    return new_token


def _renew(client_id: str, token: str, old_expiry: datetime) -> str:
    try:
        response = DhanLogin(client_id).renew_token(token)
    except Exception as exc:
        raise TokenRenewalError(f"Dhan RenewToken call failed: {exc}") from exc

    new_token = _find_new_token(response, old_expiry)
    if new_token is None:
        _save_unparsed_response(response)
        raise TokenRenewalError(
            "Could not find a new access token in the RenewToken response. The old token may "
            f"now be expired; the raw response was saved to {UNPARSED_RESPONSE_FILE}."
        )
    return new_token


def _find_new_token(response: object, old_expiry: datetime) -> str | None:
    """Find a JWT in the response that expires later than the old token.

    Dhan doesn't document the response shape, so search every string value.
    """
    for value in _iter_strings(response):
        if _JWT_RE.match(value):
            try:
                if token_expiry(value) > old_expiry:
                    return value
            except TokenRenewalError:
                continue
    return None


def _iter_strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _iter_strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _iter_strings(v)


def _save_token(token: str, env_file: Path = Path(ENV_FILE)) -> None:
    """Replace DHAN_ACCESS_TOKEN in the .env file, keeping all other lines."""
    lines = env_file.read_text().splitlines() if env_file.exists() else []
    new_line = f"{ENV_KEY}={token}"
    replaced = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{ENV_KEY}="):
            lines[i] = new_line
            replaced = True
    if not replaced:
        lines.append(new_line)

    # Write to a temp file then rename, so a crash can't leave a half-written .env.
    fd, tmp_path = tempfile.mkstemp(dir=env_file.parent or ".", prefix=".env.tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write("\n".join(lines) + "\n")
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, env_file)
    except OSError as exc:
        Path(tmp_path).unlink(missing_ok=True)
        _save_unparsed_response({"token": token})
        raise TokenRenewalError(
            f"Renewed token could not be written to {env_file}: {exc}. "
            f"It was saved to {UNPARSED_RESPONSE_FILE} instead."
        ) from exc

    if os.environ.get(ENV_KEY):
        logger.warning(
            "%s is set in the shell environment, which overrides %s; "
            "update or unset it to use the renewed token next time.",
            ENV_KEY,
            env_file,
        )


def _save_unparsed_response(response: object) -> None:
    fd = os.open(UNPARSED_RESPONSE_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(response, f, indent=2, default=str)


def _format_duration(delta: timedelta) -> str:
    minutes = int(delta.total_seconds() // 60)
    return f"{minutes // 60}h {minutes % 60:02d}m"
