import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


load_dotenv()


api_key = os.getenv("GROQ_API_KEY") or "gsk_placeholder_key"

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=api_key,
    temperature=0
)