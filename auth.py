from flask import Blueprint, request, jsonify
from app.models import db, User
from app.utils.auth_helpers import generate_token, token_required
from app.utils.validators import validate_registration_data, validate_email

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account."""
    data = request.get_json(silent=True)
    is_valid, error_msg = validate_registration_data(data)
    if not is_valid:
        return jsonify({"success": False, "error": error_msg}), 400

    username = data["username"].strip()
    email = data["email"].strip().lower()
    password = data["password"]
    full_name = data.get("full_name", "").strip() or username
    target_role = data.get("target_role", "Software Engineer").strip()

    # Check for duplicate username
    if User.query.filter_by(username=username).first():
        return jsonify({"success": False, "error": "Username is already taken."}), 409

    # Check for duplicate email
    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "error": "An account with this email already exists."}), 409

    try:
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            target_role=target_role
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        token = generate_token(user.id)
        return jsonify({
            "success": True,
            "message": "Registration successful.",
            "token": token,
            "user": user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to register user: {str(e)}"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate a user and return a JWT access token."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Request body must be valid JSON."}), 400

    login_identifier = str(data.get("identifier", data.get("email", ""))).strip().lower()
    password = str(data.get("password", "")).strip()

    if not login_identifier or not password:
        return jsonify({"success": False, "error": "Email/username and password are required."}), 400

    # Lookup by email or username
    user = User.query.filter(
        (User.email == login_identifier) | (User.username.ilike(login_identifier))
    ).first()

    if not user or not user.check_password(password):
        return jsonify({"success": False, "error": "Invalid email/username or password."}), 401

    token = generate_token(user.id)
    return jsonify({
        "success": True,
        "message": "Login successful.",
        "token": token,
        "user": user.to_dict()
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Client-side token disposal acknowledgement."""
    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    }), 200


@auth_bp.route("/me", methods=["GET"])
@token_required
def get_current_user_profile():
    """Return profile of currently logged-in user."""
    return jsonify({
        "success": True,
        "user": request.current_user.to_dict()
    }), 200


@auth_bp.route("/profile", methods=["PUT"])
@token_required
def update_profile():
    """Update user's profile details."""
    user = request.current_user
    data = request.get_json(silent=True) or {}

    if "full_name" in data:
        user.full_name = str(data["full_name"]).strip()
    if "target_role" in data:
        user.target_role = str(data["target_role"]).strip()

    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Profile updated successfully.",
        "user": user.to_dict()
    }), 200
