from flask import Blueprint, request, jsonify, current_app
from app.models import db, InterviewQuestion, Application, Resume
from app.utils.auth_helpers import token_required
from app.services.gemini_service import generate_interview_questions

interview_bp = Blueprint("interview", __name__)


@interview_bp.route("/generate", methods=["POST"])
@token_required
def generate_questions():
    """
    Generate customized interview questions using Google Gemini API.
    Can be invoked with direct text or references to existing application/resume.
    """
    data = request.get_json(silent=True) or {}
    user_id = request.current_user.id

    job_title = data.get("job_title", "").strip() or "Software Engineer"
    job_description = data.get("job_description", "").strip()
    resume_text = data.get("resume_text", "").strip()
    skills = data.get("skills", [])
    application_id = data.get("application_id")
    resume_id = data.get("resume_id")

    # If application_id provided, autofill missing job details
    if application_id and not job_description:
        app_record = Application.query.filter_by(id=application_id, user_id=user_id).first()
        if app_record:
            job_description = app_record.job_description or ""
            job_title = app_record.job_title

    # If resume_id provided, autofill resume text
    if resume_id and not resume_text:
        res_record = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
        if res_record:
            resume_text = res_record.extracted_text

    if not job_description:
        return jsonify({
            "success": False,
            "error": "Job description is required to generate targeted interview questions."
        }), 400

    api_key = current_app.config.get("GEMINI_API_KEY")

    # Call Gemini AI Service
    result = generate_interview_questions(
        job_title=job_title,
        job_description=job_description,
        resume_text=resume_text,
        skills=skills,
        api_key=api_key
    )

    if not result.get("success"):
        return jsonify(result), 400 if result.get("error_type") == "MISSING_API_KEY" else 502

    # Save generated questions into database for tracking
    created_records = []
    try:
        for q in result.get("questions", []):
            rec = InterviewQuestion(
                user_id=user_id,
                application_id=application_id,
                job_title=job_title,
                category=q.get("category", "Technical"),
                question=q.get("question", ""),
                difficulty=q.get("difficulty", "Medium"),
                interviewer_rationale=q.get("interviewer_rationale", "")
            )
            db.session.add(rec)
            created_records.append(rec)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # Even if DB storage encounters an issue, still return the generated questions to user
        current_app.logger.warning(f"Could not persist interview questions: {e}")

    return jsonify({
        "success": True,
        "message": f"Successfully generated {len(result['questions'])} interview questions.",
        "job_title": job_title,
        "questions": result["questions"]
    }), 200


@interview_bp.route("/history", methods=["GET"])
@token_required
def get_interview_history():
    """Retrieve previously generated questions saved for the user."""
    category = request.args.get("category")
    app_id = request.args.get("application_id")

    query = InterviewQuestion.query.filter_by(user_id=request.current_user.id)

    if category:
        query = query.filter_by(category=category)
    if app_id:
        query = query.filter_by(application_id=app_id)

    questions = query.order_by(InterviewQuestion.created_at.desc()).limit(50).all()

    return jsonify({
        "success": True,
        "count": len(questions),
        "questions": [q.to_dict() for q in questions]
    }), 200
