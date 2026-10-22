import re
from app.models.application import VALID_STATUSES

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email(email: str) -> bool:
    """Validate standard email format."""
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def validate_registration_data(data: dict) -> tuple[bool, str]:
    """Validate user registration payload."""
    if not data:
        return False, "Request body is empty or not JSON."

    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", "")).strip()

    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters long."

    if not email or not validate_email(email):
        return False, "A valid email address is required."

    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."

    return True, ""


def validate_application_data(data: dict) -> tuple[bool, str]:
    """Validate job application creation/updating payload."""
    if not data:
        return False, "Request body is empty or not JSON."

    company_name = str(data.get("company_name", "")).strip()
    job_title = str(data.get("job_title", "")).strip()
    status = data.get("status", "Saved")

    if not company_name:
        return False, "Company name is required."

    if not job_title:
        return False, "Job title is required."

    if status and status not in VALID_STATUSES:
        return False, f"Invalid status '{status}'. Must be one of: {', '.join(VALID_STATUSES)}"

    return True, ""


def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """Check if the uploaded file has an allowed extension."""
    if not allowed_extensions:
        allowed_extensions = {"pdf", "docx", "txt"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions
