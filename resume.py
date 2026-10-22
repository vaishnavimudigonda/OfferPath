import os
import time
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.models import db, Resume
from app.utils.auth_helpers import token_required
from app.utils.validators import allowed_file
from app.services.text_extractor import extract_text_from_file

resume_bp = Blueprint("resume", __name__)


@resume_bp.route("/upload", methods=["POST"])
@token_required
def upload_resume():
    """
    Upload and automatically parse a PDF, DOCX, or TXT resume.
    """
    if "resume" not in request.files and "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded. Key 'resume' or 'file' expected."}), 400

    file = request.files.get("resume") or request.files.get("file")

    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected."}), 400

    if not allowed_file(file.filename, current_app.config.get("ALLOWED_EXTENSIONS")):
        return jsonify({
            "success": False,
            "error": "Invalid file format. Allowed formats: PDF (.pdf), Word (.docx), Plain Text (.txt)"
        }), 400

    filename = secure_filename(file.filename)
    extension = filename.rsplit(".", 1)[1].lower()
    timestamp = int(time.time())
    unique_filename = f"user_{request.current_user.id}_{timestamp}_{filename}"

    upload_folder = current_app.config.get("UPLOAD_FOLDER")
    save_path = os.path.join(upload_folder, unique_filename)

    try:
        file.save(save_path)
        file_size = os.path.getsize(save_path)

        # Enforce max file size check (5MB)
        max_size = current_app.config.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024)
        if file_size > max_size:
            os.remove(save_path)
            return jsonify({"success": False, "error": "File size exceeds 5MB limit."}), 400

        # Extract text from the saved file
        extracted_text = extract_text_from_file(save_path)

        # Create Resume database record
        resume_record = Resume(
            user_id=request.current_user.id,
            file_name=filename,
            file_path=save_path,
            file_type=extension,
            file_size=file_size,
            extracted_text=extracted_text
        )

        db.session.add(resume_record)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Resume uploaded and extracted successfully.",
            "resume": resume_record.to_dict(include_text=True)
        }), 201

    except ValueError as ve:
        if os.path.exists(save_path):
            os.remove(save_path)
        return jsonify({"success": False, "error": str(ve)}), 400

    except Exception as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to process resume: {str(e)}"}), 500


@resume_bp.route("/my-resumes", methods=["GET"])
@token_required
def get_my_resumes():
    """Retrieve list of user's uploaded resumes."""
    resumes = Resume.query.filter_by(user_id=request.current_user.id).order_by(Resume.uploaded_at.desc()).all()
    return jsonify({
        "success": True,
        "count": len(resumes),
        "resumes": [r.to_dict(include_text=False) for r in resumes]
    }), 200


@resume_bp.route("/<int:resume_id>", methods=["GET"])
@token_required
def get_resume(resume_id: int):
    """Retrieve details and full text of a specific resume."""
    resume = Resume.query.filter_by(id=resume_id, user_id=request.current_user.id).first()
    if not resume:
        return jsonify({"success": False, "error": "Resume not found."}), 404

    return jsonify({
        "success": True,
        "resume": resume.to_dict(include_text=True)
    }), 200


@resume_bp.route("/<int:resume_id>", methods=["DELETE"])
@token_required
def delete_resume(resume_id: int):
    """Delete a resume and remove its file from disk."""
    resume = Resume.query.filter_by(id=resume_id, user_id=request.current_user.id).first()
    if not resume:
        return jsonify({"success": False, "error": "Resume not found."}), 404

    try:
        # Delete file from disk if it exists
        if os.path.exists(resume.file_path):
            os.remove(resume.file_path)

        db.session.delete(resume)
        db.session.commit()
        return jsonify({"success": True, "message": "Resume deleted successfully."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to delete resume: {str(e)}"}), 500
