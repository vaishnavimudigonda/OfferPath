from flask import Blueprint, request, jsonify
from app.models import db, Analysis, Resume, Application
from app.utils.auth_helpers import token_required
from app.services.nlp_analyzer import analyze_resume_against_job

analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.route("", methods=["POST"])
@token_required
def perform_analysis():
    """
    Perform complete NLP ATS analysis between resume and job description.
    Supports either direct text payload or database references (resume_id, application_id).
    """
    data = request.get_json(silent=True) or {}
    user_id = request.current_user.id

    resume_text = data.get("resume_text", "").strip()
    job_description = data.get("job_description", "").strip()
    job_title = data.get("job_title", "Target Position").strip()
    company_name = data.get("company_name", "").strip()

    resume_id = data.get("resume_id")
    application_id = data.get("application_id")

    # If resume_id is provided, retrieve resume text from database
    if resume_id and not resume_text:
        resume_record = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
        if resume_record:
            resume_text = resume_record.extracted_text

    # If application_id is provided, retrieve JD from database
    if application_id and not job_description:
        app_record = Application.query.filter_by(id=application_id, user_id=user_id).first()
        if app_record:
            job_description = app_record.job_description or ""
            if not company_name:
                company_name = app_record.company_name
            if job_title == "Target Position":
                job_title = app_record.job_title

    if not resume_text:
        return jsonify({
            "success": False,
            "error": "Resume text is required. Please upload or paste a resume."
        }), 400

    if not job_description:
        return jsonify({
            "success": False,
            "error": "Job description is required. Please paste the job description."
        }), 400

    try:
        results = analyze_resume_against_job(
            resume_text=resume_text,
            job_description=job_description,
            job_title=job_title
        )

        # Store in database
        analysis_record = Analysis(
            user_id=user_id,
            application_id=application_id,
            resume_id=resume_id,
            job_title=job_title,
            company_name=company_name,
            overall_score=results["overall_score"],
            keyword_score=results["keyword_score"],
            skill_score=results["skill_score"],
            similarity_score=results["similarity_score"],
            experience_score=results["experience_score"],
            matching_keywords=results["matching_keywords"],
            missing_keywords=results["missing_keywords"],
            matching_skills=results["matching_skills"],
            missing_skills=results["missing_skills"],
            entities=results["entities"],
            summary=results["summary"]
        )

        db.session.add(analysis_record)
        db.session.commit()

        response_data = analysis_record.to_dict()
        response_data["scoring_formula_explanation"] = results.get("scoring_formula_explanation")
        response_data["spacy_status"] = results.get("spacy_status")

        return jsonify({
            "success": True,
            "message": "Resume analysis completed successfully.",
            "analysis": response_data
        }), 201

    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Analysis failed: {str(e)}"}), 500


@analysis_bp.route("/history", methods=["GET"])
@token_required
def get_analysis_history():
    """Retrieve history of previous ATS analyses for the current user."""
    analyses = Analysis.query.filter_by(user_id=request.current_user.id).order_by(Analysis.created_at.desc()).limit(20).all()
    return jsonify({
        "success": True,
        "count": len(analyses),
        "history": [a.to_dict() for a in analyses]
    }), 200


@analysis_bp.route("/<int:analysis_id>", methods=["GET"])
@token_required
def get_analysis_details(analysis_id: int):
    """Retrieve details of a specific past analysis."""
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=request.current_user.id).first()
    if not analysis:
        return jsonify({"success": False, "error": "Analysis record not found."}), 404

    return jsonify({
        "success": True,
        "analysis": analysis.to_dict()
    }), 200
