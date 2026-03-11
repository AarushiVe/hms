from datetime import datetime
from functools import wraps

from flask import current_app, g, request

from .extensions import db
from .models import AuthToken, UserRole


def _extract_bearer_token():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header.split(" ", 1)[1].strip()
    return None


def auth_required(roles=None):
    roles = roles or []

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            token_value = _extract_bearer_token()
            if not token_value:
                return {"error": "Missing auth token"}, 401

            token = AuthToken.query.filter_by(token=token_value).first()
            if not token or token.expires_at < datetime.utcnow():
                return {"error": "Invalid or expired token"}, 401

            user = token.user
            if not user or not user.is_active:
                return {"error": "User is inactive"}, 403

            if roles and user.role not in roles:
                return {"error": "Forbidden"}, 403

            g.current_user = user
            g.current_token = token
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def issue_token(user):
    token = AuthToken.create_for_user(
        user_id=user.id,
        ttl_hours=current_app.config["TOKEN_TTL_HOURS"],
    )
    db.session.add(token)
    db.session.commit()
    return token


def revoke_token(token):
    db.session.delete(token)
    db.session.commit()
