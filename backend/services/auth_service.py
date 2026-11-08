"""
Google sign-in: verify a Google ID token, check the e-mail against the allow-list,
and issue / read a signed session cookie.

Env (loaded from Aiprojects/env/.env locally, /opt/env/.env on the server):
  GOOGLE_OAUTH_CLIENT_ID   - the shared Google OAuth web client
  NEWAVE_SESSION_SECRET    - signs the session cookie
  NEWAVE_ALLOWED_EMAILS    - comma-separated e-mails allowed in
"""
import os
from typing import Optional

from dotenv import load_dotenv
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'env', '.env')
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)

COOKIE_NAME = 'newave_session'
SESSION_MAX_AGE = 30 * 24 * 3600  # 30 days

_google_request = google_requests.Request()


class AuthError(Exception):
    """Sign-in rejected; the message is safe to show the user."""


def client_id() -> str:
    return os.getenv('GOOGLE_OAUTH_CLIENT_ID', '')


def allowed_emails() -> set:
    raw = os.getenv('NEWAVE_ALLOWED_EMAILS', '')
    return {e.strip().lower() for e in raw.split(',') if e.strip()}


def _serializer() -> URLSafeTimedSerializer:
    secret = os.getenv('NEWAVE_SESSION_SECRET', '')
    if not secret:
        raise RuntimeError('NEWAVE_SESSION_SECRET is not set')
    return URLSafeTimedSerializer(secret, salt='newave-session')


def verify_google_credential(credential: str) -> dict:
    """Validate a Google ID token and return the user, or raise AuthError."""
    cid = client_id()
    if not cid:
        raise RuntimeError('GOOGLE_OAUTH_CLIENT_ID is not set')
    try:
        info = id_token.verify_oauth2_token(credential, _google_request, cid)
    except ValueError:
        raise AuthError('ההתחברות עם גוגל נכשלה')

    email = (info.get('email') or '').lower()
    if not email or not info.get('email_verified'):
        raise AuthError('חשבון הגוגל אינו מאומת')
    if email not in allowed_emails():
        raise AuthError(f'לחשבון {email} אין הרשאה למערכת')

    return {
        'email': email,
        'name': info.get('name') or email,
        'picture': info.get('picture') or '',
    }


def make_session(user: dict) -> str:
    return _serializer().dumps(user)


def read_session(token: Optional[str]) -> Optional[dict]:
    """Return the user in a valid session cookie, or None.

    Re-checks the allow-list, so removing an e-mail locks that user out
    without waiting for the cookie to expire.
    """
    if not token:
        return None
    try:
        user = _serializer().loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    if (user.get('email') or '').lower() not in allowed_emails():
        return None
    return user
