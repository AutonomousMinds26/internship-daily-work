import os
import json

from parser import extract_resume_text
from extractor import extract_candidate_info
from jd_parser import extract_job_info
from scorer import calculate_score


def rank_candidates(resume_folder, job_file):

    rankings = []

    # Read Job Description
    with open(job_file, "r", encoding="utf-8") as file:
        job_text = file.read()

    job = extract_job_info(job_text)

    # Process all resumes
    for file in os.listdir(resume_folder):

        if file.lower().endswith(".pdf"):

            resume_path = os.path.join(resume_folder, file)

            resume_text = extract_resume_text(resume_path)

            candidate = extract_candidate_info(resume_text)

            result = calculate_score(candidate, job)

            rankings.append(result)

    # Sort by highest score
    rankings.sort(
        key=lambda x: x["match_percentage"],
        reverse=True
    )

    return rankings


if __name__ == "__main__":

    ranked = rank_candidates(
        "sample_resumes",
        "backend/AI/sample_job.txt"
    )

    print("\n=========== FINAL RANKING ===========\n")

    for i, candidate in enumerate(ranked, start=1):

        print(f"Rank #{i}")

        print(json.dumps(candidate, indent=4))

        print("------------------------------------")