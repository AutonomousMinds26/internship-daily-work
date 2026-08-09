import json

try:
    from AI.llm import llm
    from AI.prompts import RESUME_PROMPT
except ImportError:
    from llm import llm  # type: ignore
    from prompts import RESUME_PROMPT  # type: ignore


def extract_candidate_info(resume_text):

    prompt = RESUME_PROMPT.format(
        text=resume_text
    )

    response = llm.invoke(prompt)

    content = str(response.content).strip()

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

        return json.loads(content)


    except Exception:

        return {
            "name": "Not Available",
            "email": "Not Available",
            "phone": "Not Available",
            "location": "Not Available",
            "education": "Not Available",
            "experience": "Not Available",
            "skills": [],
            "projects": [],
            "notice_period": "Not Available",
            "expected_ctc": "Not Available"
        }