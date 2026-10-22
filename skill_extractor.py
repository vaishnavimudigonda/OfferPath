import re
from typing import Dict, List, Set, Tuple

# Comprehensive, categorized skill taxonomy
SKILL_TAXONOMY: Dict[str, List[str]] = {
    "Programming Languages": [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "C", "Go", "Golang",
        "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Dart", "Scala", "R", "SQL",
        "Bash", "Shell", "PowerShell", "Perl", "Haskell", "Elixir", "Lua", "Solidity"
    ],
    "Frontend Development": [
        "React", "React.js", "Angular", "Vue", "Vue.js", "Next.js", "Nuxt.js", "Svelte",
        "HTML", "HTML5", "CSS", "CSS3", "Sass", "SCSS", "Tailwind CSS", "Bootstrap",
        "Redux", "Redux Toolkit", "Webpack", "Vite", "jQuery", "Material UI", "Chakra UI"
    ],
    "Backend & Frameworks": [
        "Flask", "Django", "FastAPI", "Node.js", "Express", "Express.js", "Spring Boot",
        "Spring", "ASP.NET", ".NET", ".NET Core", "Ruby on Rails", "Nest.js",
        "Laravel", "Koa", "Gin", "Echo", "Rocket", "Tornado"
    ],
    "Databases & Caching": [
        "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
        "DynamoDB", "Oracle", "Microsoft SQL Server", "CouchDB", "Neo4j", "Firebase",
        "Supabase", "Snowflake", "BigQuery", "MariaDB", "Prisma", "SQLAlchemy", "Hibernate"
    ],
    "Cloud & Infrastructure": [
        "AWS", "Amazon Web Services", "Azure", "Google Cloud", "GCP", "Docker", "Kubernetes",
        "Terraform", "Ansible", "Linux", "Unix", "Serverless", "AWS Lambda", "EC2", "S3",
        "Cloudflare", "Heroku", "Vercel", "DigitalOcean", "Helm"
    ],
    "DevOps & CI/CD": [
        "CI/CD", "GitHub Actions", "GitLab CI", "Jenkins", "CircleCI", "ArgoCD",
        "Prometheus", "Grafana", "ELK Stack", "Datadog", "Nginx", "Apache"
    ],
    "AI, ML & Data Science": [
        "Machine Learning", "Deep Learning", "Artificial Intelligence", "NLP",
        "Natural Language Processing", "Computer Vision", "Scikit-Learn", "TensorFlow",
        "PyTorch", "Keras", "Pandas", "NumPy", "SciPy", "spaCy", "NLTK", "Hugging Face",
        "Transformers", "OpenCV", "LLM", "Large Language Models", "LangChain", "RAG",
        "Data Analysis", "Data Visualization", "Matplotlib", "Seaborn", "Tableau", "Power BI"
    ],
    "Architecture & Methodologies": [
        "REST API", "RESTful API", "GraphQL", "gRPC", "Microservices", "System Design",
        "Design Patterns", "Object-Oriented Programming", "OOP", "Agile", "Scrum",
        "Kanban", "Test-Driven Development", "TDD", "Unit Testing", "Integration Testing",
        "Clean Code", "SOLID Principles", "Event-Driven Architecture", "MVC"
    ],
    "Tools & Platforms": [
        "Git", "GitHub", "GitLab", "Bitbucket", "Jira", "Confluence", "Postman",
        "Swagger", "OpenAPI", "VS Code", "IntelliJ IDEA", "Linux CLI", "Figma"
    ],
    "Soft & Professional Skills": [
        "Problem Solving", "Critical Thinking", "Communication", "Team Leadership",
        "Project Management", "Time Management", "Collaboration", "Code Review",
        "Mentorship", "Adaptability", "Troubleshooting"
    ]
}

# Inverted mapping: lowercase canonical skill to display name & category
SKILL_MAP: Dict[str, Tuple[str, str]] = {}
for category, skills in SKILL_TAXONOMY.items():
    for skill in skills:
        SKILL_MAP[skill.lower()] = (skill, category)


def _build_skill_regex(skill_name: str) -> re.Pattern:
    """Build a regex pattern that respects symbols in names like C++, C#, .NET."""
    escaped = re.escape(skill_name)
    # If the skill starts/ends with alphanumeric characters, apply word boundary
    prefix = r"(?<![\w#+])" if skill_name[0].isalnum() else ""
    suffix = r"(?![\w#+])" if skill_name[-1].isalnum() else ""
    pattern = rf"{prefix}{escaped}{suffix}"
    return re.compile(pattern, re.IGNORECASE)


# Precompile search patterns for all skills
COMPILED_PATTERNS = [
    (display_name, category, _build_skill_regex(display_name))
    for lower_key, (display_name, category) in SKILL_MAP.items()
]


def extract_skills(text: str) -> List[Dict[str, str]]:
    """
    Extract recognized skills from arbitrary text (resume or job description).
    
    Returns:
        List of dicts: [{"name": "Python", "category": "Programming Languages"}, ...]
    """
    if not text:
        return []

    found_skills = {}
    for display_name, category, pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            found_skills[display_name] = category

    # Also detect common variants (e.g. 'JS' -> JavaScript if not found)
    if re.search(r"\bJS\b", text) and "JavaScript" not in found_skills:
        found_skills["JavaScript"] = "Programming Languages"
    if re.search(r"\bTS\b", text) and "TypeScript" not in found_skills:
        found_skills["TypeScript"] = "Programming Languages"
    if re.search(r"\bK8s\b", text, re.IGNORECASE) and "Kubernetes" not in found_skills:
        found_skills["Kubernetes"] = "Cloud & Infrastructure"

    # Return structured list sorted by category and name
    results = [
        {"name": name, "category": cat}
        for name, cat in sorted(found_skills.items(), key=lambda x: (x[1], x[0]))
    ]
    return results


def find_skill_gaps(
    resume_text: str,
    job_description_text: str
) -> Dict[str, any]:
    """
    Analyze skill overlap between resume and job description.
    
    Returns:
        Dict with:
          - 'matched_skills': list of skill names present in both
          - 'missing_skills': list of skill names present in JD but missing in resume
          - 'extra_skills': skills in resume not explicitly in JD
          - 'job_skills_count': total skills requested in JD
          - 'matched_count': number of matched skills
          - 'skill_match_percentage': float percentage (0.0 to 100.0)
    """
    resume_skills_list = extract_skills(resume_text)
    job_skills_list = extract_skills(job_description_text)

    resume_skill_set = {s["name"].lower(): s for s in resume_skills_list}
    job_skill_set = {s["name"].lower(): s for s in job_skills_list}

    matched = []
    missing = []
    extra = []

    for name_lower, skill_obj in job_skill_set.items():
        if name_lower in resume_skill_set:
            matched.append(skill_obj)
        else:
            missing.append(skill_obj)

    for name_lower, skill_obj in resume_skill_set.items():
        if name_lower not in job_skill_set:
            extra.append(skill_obj)

    total_job_skills = len(job_skill_set)
    matched_count = len(matched)
    
    if total_job_skills > 0:
        match_percentage = round((matched_count / total_job_skills) * 100, 1)
    else:
        # If no specific skills in taxonomy found in JD, look at extra skills found in resume
        match_percentage = 80.0 if len(resume_skills_list) > 0 else 50.0

    return {
        "matched_skills": [s["name"] for s in matched],
        "missing_skills": [s["name"] for s in missing],
        "extra_skills": [s["name"] for s in extra],
        "matched_skills_detailed": matched,
        "missing_skills_detailed": missing,
        "job_skills_count": total_job_skills,
        "matched_count": matched_count,
        "skill_match_percentage": match_percentage
    }
