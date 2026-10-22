import re
import logging
from typing import Dict, List, Tuple, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.skill_extractor import find_skill_gaps

logger = logging.getLogger(__name__)

# Try to load spaCy model once at module initialization
_spacy_nlp = None
_spacy_load_error = None

try:
    import spacy
    try:
        _spacy_nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        _spacy_load_error = (
            "spaCy model 'en_core_web_sm' is not loaded. "
            "Install it via: python -m spacy download en_core_web_sm"
        )
        logger.warning(_spacy_load_error)
except ImportError:
    _spacy_load_error = (
        "spaCy package is not installed. Install via pip install spacy"
    )
    logger.warning(_spacy_load_error)


def analyze_resume_against_job(
    resume_text: str,
    job_description: str,
    job_title: str = "Target Position"
) -> Dict[str, Any]:
    """
    Perform complete NLP analysis of resume against job description.
    
    Calculates:
      - ATS Match Score and breakdown (skills, keywords, cosine similarity, experience)
      - TF-IDF extracted matching and missing keywords
      - Matched and missing technical/soft skills
      - spaCy Named Entity Recognition (organizations, locations, dates, etc.)
      - Executive summary with strengths, gaps, and actionable tailoring advice.
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")
    if not job_description or not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    # 1. Skill Gap Analysis
    skill_results = find_skill_gaps(resume_text, job_description)
    skill_match_score = skill_results["skill_match_percentage"]

    # 2. TF-IDF Vectorization & Cosine Similarity
    similarity_score = _calculate_cosine_similarity(resume_text, job_description)

    # 3. TF-IDF Keyword Extraction & Categorization
    keyword_results = _extract_keywords_and_gaps(resume_text, job_description)
    keyword_match_score = keyword_results["keyword_match_percentage"]

    # 4. Experience & Role Relevance Score
    experience_score = _calculate_experience_relevance(resume_text, job_description, job_title)

    # 5. Composite Transparent ATS Scoring Formula:
    # 35% Skill Match + 30% Semantic Similarity + 20% Keyword Match + 15% Experience Relevance
    overall_score = round(
        (0.35 * skill_match_score) +
        (0.30 * similarity_score) +
        (0.20 * keyword_match_score) +
        (0.15 * experience_score),
        1
    )
    # Ensure score stays in realistic range [5.0, 99.0]
    overall_score = max(5.0, min(99.0, overall_score))

    # 6. Extract Named Entities (spaCy or fallback)
    entities = _extract_named_entities(resume_text, job_description)

    # 7. Generate Executive Summary and Tailoring Recommendations
    summary = _generate_analysis_summary(
        overall_score=overall_score,
        matched_skills=skill_results["matched_skills"],
        missing_skills=skill_results["missing_skills"],
        missing_keywords=keyword_results["missing_keywords"],
        similarity_score=similarity_score
    )

    return {
        "overall_score": overall_score,
        "keyword_score": keyword_match_score,
        "skill_score": skill_match_score,
        "similarity_score": similarity_score,
        "experience_score": experience_score,
        "matching_keywords": keyword_results["matching_keywords"],
        "missing_keywords": keyword_results["missing_keywords"],
        "matching_skills": skill_results["matched_skills"],
        "missing_skills": skill_results["missing_skills"],
        "extra_skills": skill_results.get("extra_skills", []),
        "entities": entities,
        "summary": summary,
        "scoring_formula_explanation": (
            "ATS Score = (35% Skill Match) + (30% TF-IDF Cosine Similarity) + "
            "(20% Keyword Match) + (15% Experience/Role Relevance). Note: This is an "
            "explainable ATS-style metric designed for feedback and tailoring."
        ),
        "spacy_status": "loaded" if _spacy_nlp else f"fallback (Note: {_spacy_load_error})"
    }


def _calculate_cosine_similarity(text1: str, text2: str) -> float:
    """Compute TF-IDF cosine similarity between two text documents."""
    try:
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True,
            max_features=5000
        )
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        # Cosine similarity in text typically ranges between 0.1 and 0.85
        # Scale smoothly to a 0-100 percentage
        scaled_sim = min(100.0, sim * 125.0)
        return round(float(scaled_sim), 1)
    except Exception as e:
        logger.error(f"Cosine similarity calculation error: {e}")
        return 50.0


def _extract_keywords_and_gaps(resume_text: str, job_description: str) -> Dict[str, Any]:
    """
    Extract top salient keywords from the job description using TF-IDF and
    check presence in the resume.
    """
    # Custom stop words specific to recruitment noise
    recruitment_stops = {
        "job", "description", "requirements", "responsibilities", "candidate", "role",
        "company", "team", "work", "experience", "years", "skills", "ability", "working",
        "opportunity", "ideal", "qualification", "qualifications", "must", "plus",
        "benefits", "salary", "full", "time", "looking", "apply", "join", "help",
        "equal", "opportunity", "employer", "include", "including", "related", "field"
    }

    try:
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            max_df=0.95,
            min_df=1,
            max_features=60
        )
        # Fit on job description to get top job keywords
        tfidf_matrix = vectorizer.fit_transform([job_description])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]

        # Sort terms by TF-IDF weight in job description
        sorted_indices = np.argsort(scores)[::-1]
        top_terms = []
        for idx in sorted_indices:
            term = feature_names[idx].strip()
            # Filter noise and short terms
            if len(term) <= 2:
                continue
            if term.lower() in recruitment_stops:
                continue
            # Filter pure numbers
            if term.replace(".", "").isdigit():
                continue
            top_terms.append(term)
            if len(top_terms) >= 30:
                break

    except Exception:
        # Fallback to simple frequency extraction if TF-IDF fails
        words = re.findall(r"\b[a-zA-Z]{3,}\b", job_description.lower())
        top_terms = [w for w in set(words) if w not in recruitment_stops][:25]

    resume_lower = resume_text.lower()
    matching_keywords = []
    missing_keywords = []

    for term in top_terms:
        # Check whole word boundary match in resume
        term_escaped = re.escape(term.lower())
        if re.search(rf"\b{term_escaped}\b", resume_lower):
            matching_keywords.append(term.title())
        else:
            missing_keywords.append(term.title())

    total = len(matching_keywords) + len(missing_keywords)
    match_pct = round((len(matching_keywords) / max(total, 1)) * 100, 1) if total > 0 else 50.0

    return {
        "matching_keywords": matching_keywords[:20],
        "missing_keywords": missing_keywords[:20],
        "keyword_match_percentage": match_pct
    }


def _calculate_experience_relevance(
    resume_text: str,
    job_description: str,
    job_title: str
) -> float:
    """Estimate experience and seniority alignment based on heuristics."""
    score = 60.0
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()

    # 1. Check title alignment
    title_words = [w for w in re.findall(r"\b\w+\b", job_title.lower()) if len(w) > 3]
    if title_words:
        matches = sum(1 for w in title_words if w in resume_lower)
        score += (matches / len(title_words)) * 20.0

    # 2. Check seniority keywords (Junior, Mid, Senior, Lead, Staff, Principal, Intern)
    seniority_levels = ["intern", "entry", "junior", "mid", "senior", "lead", "staff", "principal"]
    jd_seniority = next((lvl for lvl in seniority_levels if lvl in jd_lower), None)
    if jd_seniority and jd_seniority in resume_lower:
        score += 10.0

    # 3. Check education degrees (Bachelor, Master, PhD, B.S., M.S., B.Tech, Computer Science)
    degree_keywords = ["bachelor", "master", "phd", "degree", "b.s", "m.s", "computer science", "engineering"]
    if any(dk in resume_lower for dk in degree_keywords):
        score += 10.0

    return round(min(100.0, max(20.0, score)), 1)


def _extract_named_entities(resume_text: str, job_description: str) -> Dict[str, List[str]]:
    """
    Extract Named Entities using spaCy or fallback rule-based extractor.
    """
    entities = {
        "organizations": [],
        "locations": [],
        "degrees_or_roles": [],
        "dates_or_periods": []
    }

    if _spacy_nlp:
        try:
            # Process resume with spaCy (first 10,000 characters to ensure fast inference)
            doc = _spacy_nlp(resume_text[:10000])
            orgs = set()
            locs = set()
            dates = set()

            for ent in doc.ents:
                clean_ent = ent.text.strip().replace("\n", " ")
                if len(clean_ent) < 2 or clean_ent.isdigit():
                    continue

                if ent.label_ == "ORG" and len(clean_ent) > 2:
                    orgs.add(clean_ent)
                elif ent.label_ in ("GPE", "LOC") and len(clean_ent) > 2:
                    locs.add(clean_ent)
                elif ent.label_ == "DATE":
                    dates.add(clean_ent)

            entities["organizations"] = sorted(list(orgs))[:10]
            entities["locations"] = sorted(list(locs))[:8]
            entities["dates_or_periods"] = sorted(list(dates))[:8]
        except Exception as e:
            logger.warning(f"spaCy NER inference issue: {e}")

    # Fallback or supplementary extraction for dates and degrees
    if not entities["dates_or_periods"]:
        year_matches = set(re.findall(r"\b(20\d\d|19\d\d)\b", resume_text))
        entities["dates_or_periods"] = sorted(list(year_matches))[:8]

    if not entities["organizations"]:
        # Simple heuristic for common academic / company patterns
        companies = set(re.findall(r"\b([A-Z][a-zA-Z0-9]+(?:\s+(?:Inc|LLC|Corp|Technologies|Solutions|Labs|University|College|Institute)))\b", resume_text))
        entities["organizations"] = sorted(list(companies))[:10]

    return entities


def _generate_analysis_summary(
    overall_score: float,
    matched_skills: List[str],
    missing_skills: List[str],
    missing_keywords: List[str],
    similarity_score: float
) -> Dict[str, Any]:
    """Generate high-impact executive feedback points and actionable recommendations."""
    strengths = []
    gaps = []
    recommendations = []

    # Strengths
    if matched_skills:
        strengths.append(f"Strong overlap in core required skills: {', '.join(matched_skills[:5])}.")
    if similarity_score >= 60.0:
        strengths.append("High contextual and vocabulary alignment with the target job description.")
    elif similarity_score >= 40.0:
        strengths.append("Moderate topical alignment with the domain and responsibilities.")

    # Gaps
    if missing_skills:
        gaps.append(f"Missing key expected technical skills: {', '.join(missing_skills[:5])}.")
    if missing_keywords:
        gaps.append(f"Important job keywords absent from resume: {', '.join(missing_keywords[:6])}.")

    # Recommendations
    if missing_skills:
        recommendations.append(
            f"Incorporate project or coursework evidence demonstrating experience with: {', '.join(missing_skills[:4])}."
        )
    if missing_keywords:
        recommendations.append(
            f"Tailor your bullet points using action verbs and industry phrases such as: {', '.join(missing_keywords[:4])}."
        )
    recommendations.append(
        "Quantify your accomplishments (e.g., 'improved query speed by 35%', 'reduced build time by 20 mins')."
    )

    verdict = "Excellent Match" if overall_score >= 75 else (
        "Good Match - Needs Tailoring" if overall_score >= 55 else
        "Moderate Match - Significant Gaps" if overall_score >= 40 else
        "Low Match - Extensive Revision Recommended"
    )

    return {
        "verdict": verdict,
        "strengths": strengths or ["Resume displays relevant foundational experience."],
        "critical_gaps": gaps or ["No major skill gaps detected."],
        "actionable_recommendations": recommendations
    }
