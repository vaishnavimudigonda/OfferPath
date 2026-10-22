import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, current_app
from app.models import db
from app.models.user import User


def generate_token(user_id: int) -> str:
    """Generate a signed JWT token valid for the configured duration."""
    expiration_hours = current_app.config.get("JWT_EXPIRATION_HOURS", 72)
    secret_key = current_app.config.get("JWT_SECRET_KEY", "offerpath-jwt-secret-key-at-least-32-bytes-long!")
    
    # RFC 7519 specifies 'sub' claim must be a string
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=expiration_hours)
    }
    
    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    secret_key = current_app.config.get("JWT_SECRET_KEY", "offerpath-jwt-secret-key-at-least-32-bytes-long!")
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return {"valid": True, "user_id": int(payload["sub"])}
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token has expired. Please log in again."}
    except jwt.InvalidTokenError:
        return {"valid": False, "error": "Invalid token. Please authenticate."}


def token_required(f):
    """Decorator to enforce JWT authentication on protected routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        token = None

        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
            elif len(parts) == 1:
                token = parts[0]

        if not token:
            token = request.args.get("token")

        if not token:
            return jsonify({
                "success": False,
                "error": "Authentication required. Missing Bearer token."
            }), 401

        decoded = decode_token(token)
        if not decoded.get("valid"):
            return jsonify({
                "success": False,
                "error": decoded.get("error", "Unauthorized access")
            }), 401

        user = db.session.get(User, decoded["user_id"])
        if not user:
            return jsonify({
                "success": False,
                "error": "User account no longer exists."
            }), 401

        # Attach user to request context for the route handler
        request.current_user = user
        return f(*args, **kwargs)

    return decorated
