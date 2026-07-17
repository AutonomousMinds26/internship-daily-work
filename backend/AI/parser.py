import fitz
import os
import json
from extractor import extract_candidate_info

def extract_resume_text(file_path):
    """
    Extract text from resume PDF
    """

    document = fitz.open(file_path)

    text = ""

    for page in document:
        text += page.get_text()

    document.close()

    return text



def process_all_resumes(folder_path):

    resumes = []

    print("Files found:", os.listdir(folder_path))

    for file in os.listdir(folder_path):

        print("Checking:", file)

        if file.lower().endswith(".pdf"):

            print("Processing:", file)

            path = os.path.join(folder_path, file)

            text = extract_resume_text(path)

            resumes.append({
                "file_name": file,
                "content": text
            })

    return resumes



if __name__ == "__main__":

    folder = "sample_resumes"

    all_resumes = process_all_resumes(folder)

    for resume in all_resumes:

        print("\n====================")
        print("Resume:", resume["file_name"])
        print("====================")

        candidate = extract_candidate_info(resume["content"])

        print(json.dumps(candidate, indent=4))