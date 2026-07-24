import json
import hashlib
import logging

from llm import llm
from prompts import AI_SCORE_PROMPT
from scorer import calculate_score

ai_logger = logging.getLogger("ai_processing")

def ai_match_candidate(candidate, job):
    # Check cache for LLM response
    cand_str = json.dumps(candidate, sort_keys=True)
    job_str = json.dumps(job, sort_keys=True)
    prompt_key = hashlib.sha256(f"{cand_str}:{job_str}".encode('utf-8')).hexdigest()

    try:
        from app.services.redis_cache import get_cached_llm_response, cache_llm_response
        cached_res = get_cached_llm_response(prompt_key)
        if cached_res:
            ai_logger.info(f"AI Matcher LLM response retrieved from Redis cache for key {prompt_key[:10]}")
            return cached_res
    except Exception as e:
        ai_logger.warning(f"Could not check Redis cache for LLM response: {str(e)}")

    prompt = AI_SCORE_PROMPT.format(
        candidate=json.dumps(
            candidate,
            indent=4
        ),
        job=json.dumps(
            job,
            indent=4
        )
    )

    ai_logger.info(f"Invoking LLM for candidate '{candidate.get('name')}' matching")
    response = llm.invoke(prompt)

    content = response.content.strip()

    # Remove markdown if AI returns it
    content = content.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(content)

        final_res = {
            "candidate": candidate.get("name", "Not Available"),
            "email": candidate.get("email", "Not Available"),
            "match_percentage": result.get("match_percentage", 0),
            "matched_skills": result.get("matched_skills", []),
            "missing_skills": result.get("missing_skills", []),
            "strengths": result.get("strengths", []),
            "weaknesses": result.get("weaknesses", []),
            "recommendation": result.get("recommendation", "No Recommendation")
        }

        try:
            from app.services.redis_cache import cache_llm_response
            cache_llm_response(prompt_key, final_res)
        except Exception:
            pass

        ai_logger.info(f"AI Matcher successfully completed for candidate '{candidate.get('name')}'")
        return final_res

    except Exception as e:
        ai_logger.error(f"AI Scoring Failed: {str(e)}. Falling back to Python scorer.")
        return calculate_score(candidate, job)



# -----------------------------
# Testing
# -----------------------------
if __name__ == "__main__":

    from document_reader import extract_resume_text
    from resume_extractor import extract_candidate_info
    from job_extractor import extract_job_info

    resume_text = extract_resume_text(
        "sample_resumes/sample1.pdf"
    )

    candidate = extract_candidate_info(
        resume_text
    )

    with open(
        "sample_job.txt",
        "r",
        encoding="utf-8"
    ) as file:

        job_text = file.read()

    job = extract_job_info(
        job_text
    )

    result = ai_match_candidate(
        candidate,
        job
    )

    print(
        json.dumps(
            result,
            indent=4
        )
    )