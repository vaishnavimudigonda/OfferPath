import os
import json
import re
import logging
from typing import Dict, List, Any
import requests

logger = logging.getLogger(__name__)

QUESTION_CATEGORIES = [
    "Technical",
    "Project",
    "Behavioral",
    "Resume-based",
    "Job-description-specific"
]


def generate_interview_questions(
    job_title: str,
    job_description: str,
    resume_text: str = "",
    skills: List[str] = None,
    api_key: str = None
) -> Dict[str, Any]:
    """
    Generate tailored interview questions across 5 core categories using Google Gemini API.
    
    Inputs:
        job_title: The target position (e.g. Senior Backend Engineer)
        job_description: Full job description text
        resume_text: Extracted candidate resume text (optional)
        skills: List of matched or target skills (optional)
        api_key: Google Gemini API Key
        
    Returns:
        Dict with "success": bool, "questions": List[dict], or "error": str
    """
    resolved_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()

    # Validate that an actual user API key has been provided
    if not resolved_key or resolved_key in ("your_gemini_api_key_here", "your_gemini_api_key", "YOUR_GEMINI_API_KEY"):
        return {
            "success": False,
            "error_type": "MISSING_API_KEY",
            "error": (
                "Google Gemini API key is missing or not configured. "
                "Please add your free Gemini API key to the .env file: "
                "GEMINI_API_KEY=your_key_here and restart the backend. "
                "You can get a free key at https://aistudio.google.com/app/apikey"
            ),
            "questions": []
        }

    skills_str = ", ".join(skills) if skills else "Relevant modern software stack"
    resume_summary = (resume_text[:2000] if resume_text else "Not provided. Focus on candidate applying for this role.")
    jd_summary = job_description[:3000] if job_description else "Software engineering position."

    prompt = f"""
You are an expert technical hiring manager and interview coach.
Generate 10 realistic, high-quality interview questions for the following candidate and position:

Job Title: {job_title}
Key Skills: {skills_str}

Job Description:
{jd_summary}

Candidate Resume Summary:
{resume_summary}

Organize the 10 questions evenly across these 5 categories (exactly 2 questions per category):
1. "Technical" - core domain knowledge, language specifics, architectures, edge cases
2. "Project" - architectural decisions, tradeoffs, scalability, past implementation depth
3. "Behavioral" - conflict resolution, ownership, mentorship, agile delivery, communication
4. "Resume-based" - verifying specific tools, projects, and achievements highlighted on the resume
5. "Job-description-specific" - targeting key duties, stack requirements, or challenges mentioned in the JD

For each question, output:
- category: One of ["Technical", "Project", "Behavioral", "Resume-based", "Job-description-specific"]
- difficulty: One of ["Easy", "Medium", "Hard"]
- question: The full question as asked to the candidate
- interviewer_rationale: 1-2 sentences explaining what the interviewer is evaluating and what a strong answer should demonstrate.

RETURN ONLY VALID JSON. Do not include introductory text or markdown commentary.
JSON format must be an array of objects:
[
  {{
    "category": "Technical",
    "difficulty": "Medium",
    "question": "...",
    "interviewer_rationale": "..."
  }}
]
"""

    try:
        raw_text = _call_gemini_api(resolved_key, prompt)
        parsed_questions = _parse_gemini_response(raw_text)

        if not parsed_questions:
            return {
                "success": False,
                "error": "Failed to parse structured JSON from Gemini API response.",
                "raw_response": raw_text[:500],
                "questions": []
            }

        return {
            "success": True,
            "job_title": job_title,
            "total_questions": len(parsed_questions),
            "questions": parsed_questions
        }

    except Exception as e:
        logger.error(f"Gemini API request failed: {str(e)}")
        return {
            "success": False,
            "error_type": "API_ERROR",
            "error": f"Gemini API Error: {str(e)}",
            "questions": []
        }


def _call_gemini_api(api_key: str, prompt: str) -> str:
    """Execute API call using google-genai SDK or direct REST fallback."""
    # 1. Try google-genai SDK first
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        if response and response.text:
            return response.text
    except Exception as sdk_err:
        logger.debug(f"google-genai SDK attempt: {sdk_err}. Trying REST endpoint.")

    # 2. REST API fallback to Gemini 2.5 Flash / 1.5 Flash
    for model_name in ["gemini-2.5-flash", "gemini-1.5-flash"]:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "topP": 0.8,
                "maxOutputTokens": 3000
            }
        }

        resp = requests.post(endpoint, headers=headers, json=payload, timeout=45)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts and "text" in parts[0]:
                    return parts[0]["text"]
        else:
            err_msg = resp.text
            try:
                err_json = resp.json()
                if "error" in err_json and "message" in err_json["error"]:
                    err_msg = err_json["error"]["message"]
            except Exception:
                pass
            if model_name == "gemini-1.5-flash":
                raise RuntimeError(f"Gemini API returned HTTP {resp.status_code}: {err_msg}")

    raise RuntimeError("No candidate responses returned by Gemini API.")


def _parse_gemini_response(response_text: str) -> List[Dict[str, str]]:
    """Clean and parse JSON array from Gemini output."""
    if not response_text:
        return []

    cleaned = response_text.strip()
    # Strip markdown code blocks like ```json ... ```
    if "```json" in cleaned:
        cleaned = re.search(r"```json\s*(.*?)\s*```", cleaned, re.DOTALL).group(1)
    elif "```" in cleaned:
        cleaned = re.search(r"```\s*(.*?)\s*```", cleaned, re.DOTALL).group(1)

    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            # Validate items
            validated = []
            for item in data:
                if isinstance(item, dict) and "question" in item:
                    validated.append({
                        "category": item.get("category", "Technical"),
                        "difficulty": item.get("difficulty", "Medium"),
                        "question": item.get("question", "").strip(),
                        "interviewer_rationale": item.get("interviewer_rationale", "").strip()
                    })
            return validated
    except json.JSONDecodeError as jde:
        logger.error(f"JSON decode failed on Gemini response: {jde}")

    return []
