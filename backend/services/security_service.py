import hmac
import secrets
from functools import wraps

from flask import (
    abort,
    g,
    jsonify,
    redirect,
    request,
    session,
    url_for,
)

from config import config


PUBLIC_ENDPOINTS = {"auth.login", "auth.logout", "healthz"}
PUBLIC_PATH_PREFIXES = ("/static/",)
WEBHOOK_PATHS = {"/finance/bank/webhook"}
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def configure_security(app):
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=config.SESSION_COOKIE_SECURE and config.ENVIRONMENT == "production",
    )

    @app.before_request
    def enforce_security():
        g.csrf_token = get_csrf_token()

        if is_public_request():
            return None

        if request.path in WEBHOOK_PATHS:
            return validate_webhook_secret()

        if not config.LIFE_OS_ADMIN_PASSWORD:
            if config.ENVIRONMENT == "production":
                return jsonify(
                    {
                        "error": "LIFE_OS_ADMIN_PASSWORD nao configurado. Acesso privado bloqueado por seguranca."
                    }
                ), 503
            session["authenticated"] = True

        if not session.get("authenticated"):
            if wants_json():
                return jsonify({"error": "authentication required"}), 401
            return redirect(url_for("auth.login", next=request.full_path))

        if request.method in MUTATING_METHODS:
            sent_token = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
            expected_token = session.get("csrf_token")
            if not expected_token or not sent_token or not hmac.compare_digest(sent_token, expected_token):
                return jsonify({"error": "csrf validation failed"}), 403

        return None

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if config.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.context_processor
    def inject_security_context():
        return {
            "csrf_token": get_csrf_token(),
            "authenticated": bool(session.get("authenticated")),
        }


def require_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authenticated"):
            abort(401)
        return view(*args, **kwargs)

    return wrapped


def authenticate(password: str) -> bool:
    expected = config.LIFE_OS_ADMIN_PASSWORD
    if not expected:
        return config.ENVIRONMENT != "production"
    return hmac.compare_digest(str(password or ""), expected)


def login_user():
    session.clear()
    session["authenticated"] = True
    session["csrf_token"] = secrets.token_urlsafe(32)


def logout_user():
    session.clear()


def get_csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def validate_webhook_secret():
    expected = config.PLUGGY_WEBHOOK_SECRET
    if not expected:
        return jsonify({"error": "PLUGGY_WEBHOOK_SECRET nao configurado"}), 403
    provided = (
        request.headers.get("X-LifeOS-Webhook-Secret")
        or request.headers.get("X-Webhook-Secret")
        or request.args.get("secret")
    )
    if not provided or not hmac.compare_digest(str(provided), expected):
        return jsonify({"error": "invalid webhook secret"}), 403
    return None


def is_public_request() -> bool:
    if request.endpoint in PUBLIC_ENDPOINTS:
        return True
    return any(request.path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES)


def wants_json() -> bool:
    return (
        request.path.startswith("/api/")
        or request.accept_mimetypes.best == "application/json"
        or request.is_json
    )
