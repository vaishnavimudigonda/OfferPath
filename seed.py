import os
import sys
from datetime import date, timedelta
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import create_app
from app.models import db, User, Application, Resume, Analysis, InterviewQuestion

app = create_app(os.getenv("FLASK_ENV", "development"))


def seed_database():
    """Populate database with rich sample data for immediate testing."""
    with app.app_context():
        print("[OfferPath Seed] Creating database tables if needed...")
        db.create_all()

        # Check if demo user already exists
        existing_user = User.query.filter_by(email="demo@offerpath.com").first()
        if existing_user:
            print("[OfferPath Seed] Demo user already exists. Cleaning up old demo data...")
            db.session.delete(existing_user)
            db.session.commit()

        print("[OfferPath Seed] Creating primary demo user...")
        demo_user = User(
            username="demouser",
            email="demo@offerpath.com",
            full_name="Alex Rivera",
            target_role="Full Stack Engineer"
        )
        demo_user.set_password("password123")
        db.session.add(demo_user)
        db.session.commit()

        print(f"[OfferPath Seed] Demo user created with ID: {demo_user.id}")

        today = date.today()

        # 1. Seed realistic applications
        sample_applications = [
            {
                "company_name": "Microsoft",
                "job_title": "Full Stack Software Engineer",
                "location": "Redmond, WA (Hybrid)",
                "salary": "$145,000 - $175,000",
                "status": "Offer",
                "application_date": today - timedelta(days=28),
                "job_url": "https://careers.microsoft.com/us/en/job/fullstack",
                "notes": "Offer letter received! Base: $155k, Sign-on: $20k, RSUs: $80k/4yrs. Need to respond by next Friday.",
                "job_description": (
                    "We are looking for a Full Stack Software Engineer to build high-scale Azure cloud portal experiences. "
                    "Responsibilities: Design, implement, and operate modern web interfaces and microservices. "
                    "Requirements: Proficiency with TypeScript, React, Node.js, C#, or Python. Experience with REST APIs, "
                    "Docker, Kubernetes, CI/CD pipelines, and cloud architecture (Azure/AWS). Strong understanding of SQL "
                    "and NoSQL databases, unit testing, and agile methodologies."
                )
            },
            {
                "company_name": "Google",
                "job_title": "Software Engineer III - Cloud & Distributed Systems",
                "location": "Mountain View, CA (Hybrid)",
                "salary": "$160,000 - $190,000",
                "status": "Interview",
                "application_date": today - timedelta(days=21),
                "job_url": "https://careers.google.com/jobs/results/swe3-cloud",
                "notes": "Completed Technical Screening. Virtual Onsite scheduled for Tuesday 10:00 AM (4 rounds: System Design, 2 Coding, Googlyness).",
                "job_description": (
                    "Join Google Cloud Core Infrastructure. Build resilient, scalable storage and compute APIs. "
                    "Requirements: BS/MS in Computer Science or equivalent. 3+ years experience with Python, Go, C++, or Java. "
                    "Deep knowledge of distributed systems, concurrency, gRPC, microservices, Linux internals, and containerization "
                    "with Docker and Kubernetes. Experience with automated testing and continuous integration."
                )
            },
            {
                "company_name": "Stripe",
                "job_title": "Backend Infrastructure Engineer",
                "location": "Remote (US)",
                "salary": "$150,000 - $185,000",
                "status": "Assessment",
                "application_date": today - timedelta(days=14),
                "job_url": "https://stripe.com/jobs/backend-infrastructure",
                "notes": "Completed HackerRank take-home test on distributed rate limiters. Waiting for recruiter feedback.",
                "job_description": (
                    "Stripe's infrastructure powers millions of businesses globally. We are seeking a Backend Engineer to build "
                    "fault-tolerant payment pipelines. You will use Python, Go, Ruby, PostgreSQL, Redis, and Kafka. Experience with "
                    "high availability, zero-downtime database migrations, microservice architecture, and Terraform is preferred."
                )
            },
            {
                "company_name": "Datadog",
                "job_title": "Software Engineer - Observability Platform",
                "location": "New York, NY (Remote friendly)",
                "salary": "$140,000 - $165,000",
                "status": "Applied",
                "application_date": today - timedelta(days=7),
                "job_url": "https://datadog.com/careers/swe-observability",
                "notes": "Applied via referral from former colleague. Resume customized with Prometheus and Grafana experience.",
                "job_description": (
                    "Build next-generation telemetry engines processing billions of events daily. "
                    "Stack includes Python, Go, PostgreSQL, Elasticsearch, Kafka, Docker, and Kubernetes. "
                    "Looking for strong CS fundamentals, performance profiling, and distributed tracing skills."
                )
            },
            {
                "company_name": "Amazon",
                "job_title": "Software Development Engineer II (SDE II)",
                "location": "Seattle, WA",
                "salary": "$155,000 - $180,000",
                "status": "Saved",
                "application_date": today - timedelta(days=2),
                "job_url": "https://amazon.jobs/en/jobs/sde2-aws",
                "notes": "Need to prepare AWS architectural examples and leadership principles stories before applying.",
                "job_description": (
                    "AWS EC2 team is hiring an SDE II to innovate virtualization primitives. "
                    "Requirements: Bachelor's degree in Computer Science, 3+ years software development experience. "
                    "Proficiency in Java, Python, C++, or C#. Experience designing scalable REST APIs and multi-threaded systems. "
                    "Demonstrated leadership and obsession with customer deliverables."
                )
            },
            {
                "company_name": "Meta",
                "job_title": "Product Software Engineer",
                "location": "Menlo Park, CA (Hybrid)",
                "salary": "$165,000 - $195,000",
                "status": "Rejected",
                "application_date": today - timedelta(days=40),
                "job_url": "https://metacareers.com/swe-product",
                "notes": "Passed initial screening, but rejected after phone screen. Feedback: Needed stronger graph algorithm speed. Practice LeetCode Tree/Graph problems.",
                "job_description": (
                    "Build engaging social experiences across Instagram and Facebook. "
                    "Requirements: Deep expertise in React, JavaScript, TypeScript, Python, or Hack/PHP. "
                    "Experience optimizing frontend performance and GraphQL data layers."
                )
            }
        ]

        app_objects = []
        for app_data in sample_applications:
            app_obj = Application(user_id=demo_user.id, **app_data)
            db.session.add(app_obj)
            app_objects.append(app_obj)

        db.session.commit()
        print(f"[OfferPath Seed] Created {len(app_objects)} job applications across all stages.")

        # 2. Seed realistic resume
        sample_resume_text = """
ALEX RIVERA
Full Stack Software Engineer | Seattle, WA | alex.rivera@example.com | github.com/alexrivera | linkedin.com/in/alexrivera

SUMMARY:
Results-driven Full Stack Engineer with 3+ years of experience designing, developing, and operating scalable web applications
and microservices. Proficient in Python, JavaScript/TypeScript, React, Flask, Node.js, and PostgreSQL. Experienced with
cloud infrastructure (AWS, Docker, Kubernetes) and CI/CD automation.

TECHNICAL SKILLS:
* Languages: Python, JavaScript, TypeScript, SQL, HTML5, CSS3, Bash
* Frameworks & Libraries: Flask, Django, React, Node.js, Express, Next.js, Redux, Tailwind CSS
* Databases: PostgreSQL, MySQL, Redis, SQLite, MongoDB
* Cloud & DevOps: AWS (EC2, S3, RDS), Docker, Kubernetes, CI/CD, GitHub Actions, Linux, Nginx
* Architecture & Tools: REST API, Microservices, Git, GitHub, Jira, Unit Testing, Agile, Scrum

PROFESSIONAL EXPERIENCE:
Apex Digital Solutions | Seattle, WA
Software Engineer (June 2023 - Present)
* Architected and deployed 4 production RESTful microservices using Python (Flask/FastAPI) and PostgreSQL, handling 2M+ daily requests.
* Migrated legacy monolithic services to containerized Docker containers managed on AWS ECS, reducing deployment cycle times by 45%.
* Developed interactive administrative dashboards in React, TypeScript, and Tailwind CSS with real-time analytics using Chart.js.
* Optimized database queries, implemented Redis caching layers, improving p95 response latencies from 320ms to 75ms.
* Spearheaded automated testing with pytest and configured GitHub Actions CI/CD pipelines, increasing test coverage from 55% to 88%.

Nova Tech Labs | Austin, TX
Junior Full Stack Developer (August 2021 - May 2023)
* Collaborated in an agile scrum team to develop customer-facing web applications using Python, JavaScript, and MySQL.
* Implemented secure user authentication workflows using JWT and OAuth2 protocols.
* Integrated third-party APIs including Stripe payment webhooks and SendGrid notifications.
* Conducted weekly code reviews, resolved 120+ bug tickets, and maintained comprehensive technical documentation.

EDUCATION:
Bachelor of Science in Computer Science
University of Washington | Graduated Magna Cum Laude (2021)
Relevant Coursework: Data Structures & Algorithms, Database Systems, Cloud Computing, Operating Systems, Machine Learning
"""
        resume_record = Resume(
            user_id=demo_user.id,
            file_name="Alex_Rivera_Software_Engineer_Resume.txt",
            file_path=os.path.join(app.config.get("UPLOAD_FOLDER"), "sample_alex_rivera_resume.txt"),
            file_type="txt",
            file_size=len(sample_resume_text.encode("utf-8")),
            extracted_text=sample_resume_text.strip()
        )
        db.session.add(resume_record)
        db.session.commit()
        print(f"[OfferPath Seed] Created demo resume with ID: {resume_record.id}")

        # 3. Seed an initial ATS analysis record for Microsoft Application
        sample_analysis = Analysis(
            user_id=demo_user.id,
            application_id=app_objects[0].id,
            resume_id=resume_record.id,
            job_title="Full Stack Software Engineer",
            company_name="Microsoft",
            overall_score=84.5,
            keyword_score=81.0,
            skill_score=88.2,
            similarity_score=82.0,
            experience_score=90.0,
            matching_skills=["Python", "JavaScript", "TypeScript", "React", "Node.js", "Docker", "Kubernetes", "REST API", "PostgreSQL", "CI/CD", "Git", "Unit Testing", "Agile"],
            missing_skills=["Azure", "C#", "NoSQL"],
            matching_keywords=["Full Stack", "Software Engineer", "Microservices", "REST APIs", "Docker", "Kubernetes", "Databases", "Unit Testing", "Agile"],
            missing_keywords=["Azure Portal", "C#", "Cloud Architecture"],
            entities={
                "organizations": ["Microsoft", "University of Washington", "Apex Digital Solutions", "Nova Tech Labs", "Amazon", "Stripe"],
                "locations": ["Seattle", "WA", "Austin", "TX", "Redmond"],
                "dates_or_periods": ["2021", "2023", "June 2023", "May 2023"]
            },
            summary={
                "verdict": "Excellent Match",
                "strengths": [
                    "Strong overlap in core required skills: Python, React, TypeScript, Docker, PostgreSQL, REST API.",
                    "Demonstrated experience with scalable microservices and cloud deployment on AWS.",
                    "High contextual and vocabulary alignment with the target job description."
                ],
                "critical_gaps": [
                    "Missing explicit mentions of Microsoft Azure cloud platform (resume highlights AWS).",
                    "C# .NET experience not highlighted in resume."
                ],
                "actionable_recommendations": [
                    "Emphasize transferable cloud knowledge between AWS and Azure architectures.",
                    "Add any experience or familiarity with C# or object-oriented enterprise patterns.",
                    "Highlight cross-functional agile leadership and system design experience in bullets."
                ]
            }
        )
        db.session.add(sample_analysis)

        # 4. Seed interview questions
        sample_interview_questions = [
            {
                "category": "Technical",
                "difficulty": "Hard",
                "job_title": "Full Stack Software Engineer",
                "question": "How would you design a distributed rate limiter for high-traffic microservices using Redis and sliding window counters?",
                "interviewer_rationale": "Evaluates understanding of distributed system bottlenecks, concurrency, race conditions, and caching patterns."
            },
            {
                "category": "Technical",
                "difficulty": "Medium",
                "job_title": "Full Stack Software Engineer",
                "question": "Explain how React's virtual DOM reconciliation works and how you would diagnose an unnecessary re-render loop in a complex dashboard.",
                "interviewer_rationale": "Tests practical frontend performance debugging, React hooks lifecycle knowledge, and profiler usage."
            },
            {
                "category": "Project",
                "difficulty": "Medium",
                "job_title": "Full Stack Software Engineer",
                "question": "Can you walk through your migration of monolithic services to Docker containers on AWS? What was your rollback strategy?",
                "interviewer_rationale": "Verifies authenticity of resume claims, deployment safety measures, and operational maturity."
            },
            {
                "category": "Behavioral",
                "difficulty": "Medium",
                "job_title": "Full Stack Software Engineer",
                "question": "Describe a situation where a production bug occurred on a service you owned. How did you communicate with stakeholders and resolve it?",
                "interviewer_rationale": "Assesses accountability, crisis communication, blameless post-mortem culture, and resilience."
            },
            {
                "category": "Resume-based",
                "difficulty": "Medium",
                "job_title": "Full Stack Software Engineer",
                "question": "You mentioned reducing p95 database query latency from 320ms to 75ms. What profiling tools and indexing strategies did you apply?",
                "interviewer_rationale": "Validates quantified achievements on the resume and deep database tuning competence."
            },
            {
                "category": "Job-description-specific",
                "difficulty": "Medium",
                "job_title": "Full Stack Software Engineer",
                "question": "This position requires building Azure portal tools. How does your experience with AWS translate to Azure cloud architectures?",
                "interviewer_rationale": "Evaluates cloud concept abstraction and adaptability to the employer's specific technology stack."
            }
        ]

        for q in sample_interview_questions:
            rec = InterviewQuestion(
                user_id=demo_user.id,
                application_id=app_objects[0].id,
                **q
            )
            db.session.add(rec)

        db.session.commit()
        print(f"[OfferPath Seed] Seeded {len(sample_interview_questions)} sample interview questions.")

        print("\n" + "=" * 65)
        print(" OFFERPATH DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 65)
        print(" You can now test the platform using the pre-seeded account:")
        print("   Email:    demo@offerpath.com")
        print("   Username: demouser")
        print("   Password: password123")
        print("=" * 65)


if __name__ == "__main__":
    seed_database()
