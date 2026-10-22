from collections import Counter, defaultdict
from flask import Blueprint, jsonify, request
from app.models import db, Application, Analysis, VALID_STATUSES
from app.utils.auth_helpers import token_required

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("", methods=["GET"])
@token_required
def get_user_analytics():
    """
    Compute real analytics and metrics for the dashboard charts and widgets.
    """
    user_id = request.current_user.id
    applications = Application.query.filter_by(user_id=user_id).all()
    total_apps = len(applications)

    # Initialize counts for each status
    status_counts = {st: 0 for st in VALID_STATUSES}
    monthly_data = defaultdict(int)

    for app in applications:
        status_counts[app.status] = status_counts.get(app.status, 0) + 1
        if app.application_date:
            month_key = app.application_date.strftime("%Y-%m")
            monthly_data[month_key] += 1

    # Sort monthly trend chronologically
    sorted_months = sorted(monthly_data.keys())
    monthly_trend = [
        {"month": m, "count": monthly_data[m]}
        for m in sorted_months
    ]

    # Application funnel metrics
    saved = status_counts["Saved"]
    applied = status_counts["Applied"]
    assessment = status_counts["Assessment"]
    interview = status_counts["Interview"]
    offer = status_counts["Offer"]
    rejected = status_counts["Rejected"]

    # Active / In-progress applications
    in_progress = applied + assessment + interview

    # Funnel progression stages
    # Candidate funnel: Applied -> Assessment -> Interview -> Offer
    funnel_applied = applied + assessment + interview + offer + rejected
    funnel_assessment = assessment + interview + offer
    funnel_interview = interview + offer
    funnel_offer = offer

    # Conversions
    interview_conversion = (
        round((funnel_interview / funnel_applied) * 100, 1)
        if funnel_applied > 0 else 0.0
    )
    offer_conversion = (
        round((funnel_offer / funnel_interview) * 100, 1)
        if funnel_interview > 0 else 0.0
    )

    # ATS analyses metrics
    user_analyses = Analysis.query.filter_by(user_id=user_id).all()
    avg_ats_score = (
        round(sum(a.overall_score for a in user_analyses) / len(user_analyses), 1)
        if user_analyses else 0.0
    )

    # Aggregate common skill gaps across all user analyses
    missing_skills_counter = Counter()
    for a in user_analyses:
        if a.missing_skills:
            for s in a.missing_skills:
                missing_skills_counter[s] += 1

    top_missing_skills = [
        {"skill": skill, "count": count}
        for skill, count in missing_skills_counter.most_common(8)
    ]

    return jsonify({
        "success": True,
        "has_data": total_apps > 0,
        "metrics": {
            "total_applications": total_apps,
            "in_progress": in_progress,
            "saved_count": saved,
            "interview_count": interview,
            "offer_count": offer,
            "rejected_count": rejected,
            "interview_conversion_rate": interview_conversion,
            "offer_conversion_rate": offer_conversion,
            "average_ats_score": avg_ats_score,
            "total_resumes_analyzed": len(user_analyses)
        },
        "charts": {
            "status_distribution": {
                "labels": list(status_counts.keys()),
                "data": list(status_counts.values())
            },
            "monthly_timeline": {
                "labels": [m["month"] for m in monthly_trend],
                "data": [m["count"] for m in monthly_trend]
            },
            "application_funnel": {
                "labels": ["Total Applied", "Assessment", "Interview", "Offer Received"],
                "data": [funnel_applied, funnel_assessment, funnel_interview, funnel_offer]
            }
        },
        "top_missing_skills": top_missing_skills
    }), 200
