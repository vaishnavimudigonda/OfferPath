import json
from app.models import db, User
from app.utils.auth_helpers import generate_token


def test_create_application(client, auth_headers):
    """Test creating a new application."""
    payload = {
        "company_name": "Acme Corp",
        "job_title": "Senior Python Developer",
        "job_description": "We need an experienced Python developer with Flask and PostgreSQL experience.",
        "location": "Remote",
        "salary": "$130,000",
        "status": "Applied",
        "notes": "Spoke with recruiter on LinkedIn."
    }
    response = client.post("/api/applications", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["application"]["company_name"] == "Acme Corp"
    assert data["application"]["status"] == "Applied"
    assert data["application"]["id"] is not None


def test_get_applications_list(client, auth_headers):
    """Test retrieving list of user applications."""
    # Create two applications
    client.post("/api/applications", json={"company_name": "Google", "job_title": "SWE", "status": "Interview"}, headers=auth_headers)
    client.post("/api/applications", json={"company_name": "Meta", "job_title": "SWE", "status": "Saved"}, headers=auth_headers)

    response = client.get("/api/applications", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["count"] >= 2


def test_filter_applications_by_status(client, auth_headers):
    """Test filtering applications by status parameter."""
    client.post("/api/applications", json={"company_name": "Offer Company", "job_title": "Lead", "status": "Offer"}, headers=auth_headers)
    client.post("/api/applications", json={"company_name": "Saved Company", "job_title": "Junior", "status": "Saved"}, headers=auth_headers)

    response = client.get("/api/applications?status=Offer", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert all(app["status"] == "Offer" for app in data["applications"])


def test_patch_application_status(client, auth_headers):
    """Test status update for Kanban board interactions."""
    create_res = client.post(
        "/api/applications",
        json={"company_name": "Stripe", "job_title": "Backend", "status": "Applied"},
        headers=auth_headers
    )
    app_id = create_res.get_json()["application"]["id"]

    patch_res = client.patch(
        f"/api/applications/{app_id}/status",
        json={"status": "Interview"},
        headers=auth_headers
    )
    assert patch_res.status_code == 200
    data = patch_res.get_json()
    assert data["success"] is True
    assert data["application"]["status"] == "Interview"


def test_delete_application(client, auth_headers):
    """Test deleting an application."""
    create_res = client.post(
        "/api/applications",
        json={"company_name": "ToDelete Inc", "job_title": "Tester", "status": "Saved"},
        headers=auth_headers
    )
    app_id = create_res.get_json()["application"]["id"]

    del_res = client.delete(f"/api/applications/{app_id}", headers=auth_headers)
    assert del_res.status_code == 200

    # Ensure it no longer exists
    get_res = client.get(f"/api/applications/{app_id}", headers=auth_headers)
    assert get_res.status_code == 404


def test_user_data_isolation(app, client, auth_headers):
    """Verify that User B cannot access or modify User A's applications."""
    # User A creates application
    create_res = client.post(
        "/api/applications",
        json={"company_name": "Confidential Corp", "job_title": "Architect", "status": "Applied"},
        headers=auth_headers
    )
    user_a_app_id = create_res.get_json()["application"]["id"]

    # Create User B
    with app.app_context():
        user_b = User(username="user_b", email="b@example.com", full_name="User B")
        user_b.set_password("Secret123!")
        db.session.add(user_b)
        db.session.commit()
        token_b = generate_token(user_b.id)

    headers_b = {"Authorization": f"Bearer {token_b}", "Content-Type": "application/json"}

    # User B attempts to access User A's application
    get_res = client.get(f"/api/applications/{user_a_app_id}", headers=headers_b)
    assert get_res.status_code == 404

    # User B attempts to delete User A's application
    del_res = client.delete(f"/api/applications/{user_a_app_id}", headers=headers_b)
    assert del_res.status_code == 404
