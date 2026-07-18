import os
import json

from document_reader import extract_resume_text
from extractor import extract_candidate_info
from jd_parser import extract_job_info
from scorer import calculate_score


def run_pipeline():

    # Load Job Description
    with open("backend/AI/sample_job.txt", "r", encoding="utf-8") as file:
        job_text = file.read()

    job = extract_job_info(job_text)

    print("\n===================================")
    print(" JOB DESCRIPTION")
    print("===================================\n")

    print(json.dumps(job, indent=4))

    results = []

    resume_folder = "sample_resumes"

    for file in os.listdir(resume_folder):

        if file.lower().endswith((".pdf", ".docx")):

            print(f"\nProcessing Resume: {file}")

            resume_path = os.path.join(resume_folder, file)

            resume_text = extract_resume_text(resume_path)

            candidate = extract_candidate_info(resume_text)

            result = calculate_score(candidate, job)

            results.append(result)

    results.sort(
        key=lambda x: x["match_percentage"],
        reverse=True
    )

    print("\n===================================")
    print(" FINAL RANKING")
    print("===================================\n")

    for i, candidate in enumerate(results, start=1):

        print(f"Rank #{i}")

        print(json.dumps(candidate, indent=4))

        print("----------------------------------")


if __name__ == "__main__":
    run_pipeline()