import os
import fitz
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# ----------------------------
# Load Environment Variables
# ----------------------------
load_dotenv()

# ----------------------------
# Load Groq API
# ----------------------------
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)
# ----------------------------
# Read Resume PDF
# ----------------------------
def extract_resume_text(file_path):

    document = fitz.open(file_path)

    text = ""

    for page in document:
        text += page.get_text()

    document.close()

    return text


# ----------------------------
# Prompt
# ----------------------------
RESUME_PROMPT = """
You are an AI Resume Parser.

Extract the following information from the resume.

Return ONLY valid JSON.

{{
"name":"",
"email":"",
"phone":"",
"skills":[],
"education":"",
"experience":"",
"location":""
}}

Resume:

{text}
"""


# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":

    resume = extract_resume_text("sample_resumes/sample1.pdf")

    prompt = RESUME_PROMPT.format(text=resume)

    response = llm.invoke(prompt)

    print(response.content)