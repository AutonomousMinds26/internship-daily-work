import json

from llm import llm
from prompts import AI_SCORE_PROMPT
from scorer import calculate_score


def ai_match_candidate(candidate, job):

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

    response = llm.invoke(prompt)

    content = response.content.strip()

    # Remove markdown if AI returns it
    content = content.replace(
        "```json",
        ""
    )

    content = content.replace(
        "```",
        ""
    )

    content = content.strip()

    try:

        result = json.loads(content)

        # Return fields in desired order
        return {

            "candidate":
                candidate.get(
                    "name",
                    "Not Available"
                ),

            "email":
                candidate.get(
                    "email",
                    "Not Available"
                ),

            "match_percentage":
                result.get(
                    "match_percentage",
                    0
                ),

            "matched_skills":
                result.get(
                    "matched_skills",
                    []
                ),

            "missing_skills":
                result.get(
                    "missing_skills",
                    []
                ),

            "strengths":
                result.get(
                    "strengths",
                    []
                ),

            "weaknesses":
                result.get(
                    "weaknesses",
                    []
                ),

            "recommendation":
                result.get(
                    "recommendation",
                    "No Recommendation"
                )

        }

    except Exception as e:

        print("\nAI Scoring Failed")
        print(e)
        print("Using Python scorer...\n")

        return calculate_score(
            candidate,
            job
        )


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