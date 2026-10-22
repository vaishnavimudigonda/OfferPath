from app.services.skill_extractor import extract_skills, find_skill_gaps
from app.services.nlp_analyzer import analyze_resume_against_job, _calculate_cosine_similarity


def test_skill_extraction():
    """Test extracting technical skills from arbitrary text."""
    sample_text = "Proficient in Python, Flask, React, Docker, and PostgreSQL with experience in Git."
    skills = extract_skills(sample_text)
    skill_names = [s["name"] for s in skills]

    assert "Python" in skill_names
    assert "Flask" in skill_names
    assert "React" in skill_names
    assert "Docker" in skill_names
    assert "PostgreSQL" in skill_names
    assert "Git" in skill_names


def test_skill_gap_analysis():
    """
    Test identifying matched vs missing skills.
    Job requires: Python, SQL, AWS, Docker, Machine Learning, Git
    Resume contains: Python, SQL, Machine Learning, Git
    Expected:
      Matched: Python, SQL, Machine Learning, Git
      Skill gaps: AWS, Docker
    """
    resume = "Candidate with skills in Python, SQL, Machine Learning, and Git."
    jd = "Requirements: Python, SQL, AWS, Docker, Machine Learning, Git."

    gaps = find_skill_gaps(resume, jd)
    matched = gaps["matched_skills"]
    missing = gaps["missing_skills"]

    assert "Python" in matched
    assert "SQL" in matched
    assert "Machine Learning" in matched
    assert "Git" in matched

    assert "AWS" in missing
    assert "Docker" in missing

    assert gaps["job_skills_count"] == 6
    assert gaps["matched_count"] == 4
    assert 60.0 <= gaps["skill_match_percentage"] <= 70.0


def test_cosine_similarity():
    """Test TF-IDF cosine similarity behaves deterministically."""
    doc1 = "Python developer experienced in building web applications with Flask, SQL and Docker."
    doc2 = "Looking for a Python developer to build web services using Flask and Docker."
    doc3 = "Veterinarian caring for domestic dogs, cats, reptiles and equine animals."

    sim_high = _calculate_cosine_similarity(doc1, doc2)
    sim_low = _calculate_cosine_similarity(doc1, doc3)

    assert sim_high > sim_low
    assert sim_high >= 20.0
    assert sim_low == 0.0


def test_analyze_resume_against_job_full():
    """Test end-to-end NLP analysis function."""
    resume_text = """
    Jane Doe - Software Engineer
    Seattle, WA | jane@example.com
    Experience with Python, Django, PostgreSQL, Docker, AWS, Git, and Unit Testing.
    3 years of full stack software engineering experience building scalable APIs.
    """
    jd_text = """
    We are hiring a Software Engineer.
    Requirements:
    - 3+ years experience with Python and Django
    - PostgreSQL database design and query optimization
    - Docker containerization and AWS cloud deployments
    - Git, CI/CD, and automated unit testing
    - Kubernetes is a plus
    """

    result = analyze_resume_against_job(resume_text, jd_text, "Software Engineer")

    assert "overall_score" in result
    assert "keyword_score" in result
    assert "skill_score" in result
    assert "similarity_score" in result
    assert "experience_score" in result
    assert "matching_skills" in result
    assert "missing_skills" in result
    assert "summary" in result

    # Scores should be in valid percentage range
    assert 0.0 <= result["overall_score"] <= 100.0
    assert 0.0 <= result["skill_score"] <= 100.0
    assert 0.0 <= result["similarity_score"] <= 100.0

    # Kubernetes should be identified as missing skill
    assert "Kubernetes" in result["missing_skills"]
    # Python and Docker should be in matching skills
    assert "Python" in result["matching_skills"]
    assert "Docker" in result["matching_skills"]


def test_analyze_api_endpoint(client, auth_headers):
    """Test the POST /api/analyze REST API endpoint."""
    payload = {
        "job_title": "Full Stack Engineer",
        "resume_text": "Experienced Python, React, and PostgreSQL developer with Git.",
        "job_description": "We need a Full Stack Engineer with Python, React, PostgreSQL, Docker, and AWS."
    }

    response = client.post("/api/analyze", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.get_json()

    assert data["success"] is True
    assert "analysis" in data
    assert "scores" in data["analysis"]
    assert data["analysis"]["scores"]["overall"] > 0
    assert len(data["analysis"]["matching_skills"]) > 0
