import os
import json

try:
    from AI.document_reader import extract_resume_text
    from AI.resume_extractor import extract_candidate_info
    from AI.job_extractor import extract_job_info
    from AI.ai_matcher import ai_match_candidate
except ImportError:
    from document_reader import extract_resume_text
    from resume_extractor import extract_candidate_info
    from job_extractor import extract_job_info
    from ai_matcher import ai_match_candidate


def rank_candidates(resume_folder, job_file):

    results = []

    # -----------------------------
    # Read Job Description
    # -----------------------------
    with open(
        job_file,
        "r",
        encoding="utf-8"
    ) as file:

        job_text = file.read()

    print("\nExtracting Job Description...\n")

    job = extract_job_info(
        job_text
    )

    # -----------------------------
    # Process All Resumes
    # -----------------------------
    for filename in os.listdir(resume_folder):

        if filename.lower().endswith(
            (".pdf", ".docx")
        ):

            print(
                f"Processing: {filename}"
            )

            path = os.path.join(
                resume_folder,
                filename
            )

            # Read Resume
            resume_text = extract_resume_text(
                path
            )

            # Extract Candidate Details
            candidate = extract_candidate_info(
                resume_text
            )

            # AI Matching
            result = ai_match_candidate(
                candidate,
                job
            )

            results.append(
                result
            )

    # -----------------------------
    # Sort Candidates
    # -----------------------------
    results.sort(
        key=lambda x: x.get(
            "match_percentage",
            0
        ),
        reverse=True
    )

    return results


if __name__ == "__main__":

    ranking = rank_candidates(
        "sample_resumes",
        "sample_job.txt"
    )

    print(
        "\n========= FINAL RANKING =========\n"
    )

    for index, candidate in enumerate(
        ranking,
        start=1
    ):

        print(
            f"Rank #{index}"
        )

        print(
            json.dumps(
                candidate,
                indent=4
            )
        )

        print("-" * 40)