"""Server-driven Google Sign-In (OAuth 2.0 authorization-code flow).

Deliberately NOT the embedded-WebView "One Tap"/Credential Manager flow:
Google's own terms block sign-in inside an embedded WebView (the exact
component the Android app's WebView-based shell uses to render everything
else) — see docs/10-STROMEX-AUTH-FEATURE.md for why. Instead, "Continue with
Google" opens the *system* browser to `authorize_url()`, Google redirects
back to `google_redirect_uri` (a backend route) with a one-time code, and
`exchange_code()`/`verify_id_token()` here turn that into a verified Google
identity — the standard native-app OAuth pattern, and one that needs no
Play Services/AndroidX dependency at all on the Android side.
"""
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import get_settings

_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"


class GoogleOAuthNotConfigured(Exception):
    """Raised when google_client_id/secret/redirect_uri aren't set — i.e.
    nobody has created the Google Cloud OAuth Client this feature needs
    yet. See docs/10-STROMEX-AUTH-FEATURE.md for the setup steps."""


@dataclass(frozen=True, slots=True)
class GoogleIdentity:
    sub: str
    email: str
    email_verified: bool
    name: str | None


def _require_configured() -> None:
    settings = get_settings()
    if not (settings.google_client_id and settings.google_client_secret and settings.google_redirect_uri):
        raise GoogleOAuthNotConfigured(
            "GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / GOOGLE_REDIRECT_URI are not all set"
        )


def authorize_url(state: str) -> str:
    """Builds the URL to send the user's system browser to."""
    _require_configured()
    settings = get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    }
    return f"{_AUTH_ENDPOINT}?{urlencode(params)}"


def verify_id_token(raw_id_token: str) -> GoogleIdentity:
    """Verifies an ID token's signature against Google's own published keys
    (fetched live from https://www.googleapis.com/oauth2/v3/certs by
    google-auth) and that it was issued for this app's client id, before
    trusting anything in it. Raises on any failure — an invalid, expired, or
    wrong-audience token is not distinguished further; callers treat any
    exception here as "not a valid Google identity right now"."""
    _require_configured()
    settings = get_settings()
    claims = google_id_token.verify_oauth2_token(
        raw_id_token, google_requests.Request(), settings.google_client_id
    )
    return GoogleIdentity(
        sub=claims["sub"],
        email=claims["email"],
        email_verified=bool(claims.get("email_verified", False)),
        name=claims.get("name"),
    )


def exchange_code(code: str) -> GoogleIdentity:
    """Exchanges a one-time authorization code for tokens, then verifies the
    returned ID token before trusting anything in it."""
    _require_configured()
    settings = get_settings()

    response = httpx.post(
        _TOKEN_ENDPOINT,
        data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=10.0,
    )
    response.raise_for_status()
    token_response = response.json()
    return verify_id_token(token_response["id_token"])
