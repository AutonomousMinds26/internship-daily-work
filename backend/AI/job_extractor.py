import json

from llm import llm
from prompts import JOB_PROMPT


def extract_job_info(job_text):

    prompt = JOB_PROMPT.format(
        text=job_text
    )

    response = llm.invoke(prompt)

    content = response.content.strip()

    # Remove markdown formatting
    content = content.replace(
        "```json",
        ""
    )

    content = content.replace(
        "```",
        ""
    )

    return json.loads(content)


if __name__ == "__main__":

    with open(
        "sample_job.txt",
        "r",
        encoding="utf-8"
    ) as file:

        job_text = file.read()


    job = extract_job_info(job_text)

    print(
        json.dumps(
            job,
            indent=4
        )
    )