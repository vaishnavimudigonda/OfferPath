from datetime import datetime, date
from flask import Blueprint, request, jsonify
from app.models import db, Application, VALID_STATUSES
from app.utils.auth_helpers import token_required
from app.utils.validators import validate_application_data

applications_bp = Blueprint("applications", __name__)


@applications_bp.route("", methods=["GET"])
@token_required
def get_applications():
    """Retrieve all applications for current user with optional filtering."""
    user_id = request.current_user.id
    status_filter = request.args.get("status")
    search_query = request.args.get("search")

    query = Application.query.filter_by(user_id=user_id)

    if status_filter and status_filter in VALID_STATUSES:
        query = query.filter_by(status=status_filter)

    if search_query:
        search = f"%{search_query.strip()}%"
        query = query.filter(
            (Application.company_name.ilike(search)) |
            (Application.job_title.ilike(search)) |
            (Application.location.ilike(search))
        )

    # Order newest application first
    applications = query.order_by(Application.application_date.desc(), Application.created_at.desc()).all()

    return jsonify({
        "success": True,
        "count": len(applications),
        "applications": [app.to_dict() for app in applications]
    }), 200


@applications_bp.route("", methods=["POST"])
@token_required
def create_application():
    """Create a new job application record."""
    data = request.get_json(silent=True)
    is_valid, error_msg = validate_application_data(data)
    if not is_valid:
        return jsonify({"success": False, "error": error_msg}), 400

    app_date = date.today()
    if data.get("application_date"):
        try:
            app_date = datetime.strptime(data["application_date"].split("T")[0], "%Y-%m-%d").date()
        except ValueError:
            pass

    try:
        new_app = Application(
            user_id=request.current_user.id,
            company_name=data["company_name"].strip(),
            job_title=data["job_title"].strip(),
            job_description=data.get("job_description", "").strip(),
            application_date=app_date,
            job_url=data.get("job_url", "").strip(),
            location=data.get("location", "Remote").strip(),
            salary=data.get("salary", "").strip(),
            notes=data.get("notes", "").strip(),
            status=data.get("status", "Saved")
        )

        db.session.add(new_app)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Job application tracked successfully.",
            "application": new_app.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to create application: {str(e)}"}), 500


@applications_bp.route("/<int:app_id>", methods=["GET"])
@token_required
def get_application(app_id: int):
    """Retrieve details of a specific application."""
    application = Application.query.filter_by(id=app_id, user_id=request.current_user.id).first()
    if not application:
        return jsonify({"success": False, "error": "Application not found."}), 404

    return jsonify({
        "success": True,
        "application": application.to_dict()
    }), 200


@applications_bp.route("/<int:app_id>", methods=["PUT"])
@token_required
def update_application(app_id: int):
    """Update details of an existing application."""
    application = Application.query.filter_by(id=app_id, user_id=request.current_user.id).first()
    if not application:
        return jsonify({"success": False, "error": "Application not found."}), 404

    data = request.get_json(silent=True) or {}
    is_valid, error_msg = validate_application_data(data)
    if not is_valid:
        return jsonify({"success": False, "error": error_msg}), 400

    try:
        application.company_name = data.get("company_name", application.company_name).strip()
        application.job_title = data.get("job_title", application.job_title).strip()
        application.job_description = data.get("job_description", application.job_description)
        application.job_url = data.get("job_url", application.job_url)
        application.location = data.get("location", application.location)
        application.salary = data.get("salary", application.salary)
        application.notes = data.get("notes", application.notes)
        
        if "status" in data and data["status"] in VALID_STATUSES:
            application.status = data["status"]

        if data.get("application_date"):
            try:
                application.application_date = datetime.strptime(
                    data["application_date"].split("T")[0], "%Y-%m-%d"
                ).date()
            except ValueError:
                pass

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Application updated successfully.",
            "application": application.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to update application: {str(e)}"}), 500


@applications_bp.route("/<int:app_id>/status", methods=["PATCH"])
@token_required
def update_application_status(app_id: int):
    """Quickly update application status (for Kanban drag & drop or dropdown)."""
    application = Application.query.filter_by(id=app_id, user_id=request.current_user.id).first()
    if not application:
        return jsonify({"success": False, "error": "Application not found."}), 404

    data = request.get_json(silent=True) or {}
    new_status = data.get("status")

    if not new_status or new_status not in VALID_STATUSES:
        return jsonify({
            "success": False,
            "error": f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"
        }), 400

    application.status = new_status
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Status updated to {new_status}.",
        "application": application.to_dict()
    }), 200


@applications_bp.route("/<int:app_id>", methods=["DELETE"])
@token_required
def delete_application(app_id: int):
    """Delete an application record."""
    application = Application.query.filter_by(id=app_id, user_id=request.current_user.id).first()
    if not application:
        return jsonify({"success": False, "error": "Application not found."}), 404

    try:
        db.session.delete(application)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Application deleted successfully."
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to delete application: {str(e)}"}), 500
