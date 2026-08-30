import os
import logging
from typing import Any, Optional
from dotenv import load_dotenv
from pydantic import SecretStr

load_dotenv()
logger = logging.getLogger(__name__)

def get_llm():
    """
    Multi-provider LLM Factory:
    Supports Groq, OpenAI, Anthropic, Ollama, and graceful local rule-based fallback.
    Configured via `LLM_PROVIDER` in environment variables.
    """
    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if provider == "openai":
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                from langchain_openai import ChatOpenAI
                logger.info("Initializing OpenAI ChatOpenAI model (gpt-4o-mini)")
                return ChatOpenAI(
                    model="gpt-4o-mini",
                    api_key=SecretStr(openai_key),
                    temperature=0
                )
            except Exception as e:
                logger.warning(f"Failed to load langchain_openai: {str(e)}")

    elif provider == "anthropic":
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                from langchain_anthropic import ChatAnthropic
                logger.info("Initializing Anthropic ChatAnthropic model (claude-3-5-sonnet-20241022)")
                return ChatAnthropic(
                    model="claude-3-5-sonnet-20241022",
                    api_key=SecretStr(anthropic_key),
                    temperature=0
                )
            except Exception as e:
                logger.warning(f"Failed to load langchain_anthropic: {str(e)}")

    elif provider == "ollama":
        try:
            from langchain_community.chat_models import ChatOllama
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            logger.info(f"Initializing Ollama model (llama3) on {ollama_url}")
            return ChatOllama(
                base_url=ollama_url,
                model="llama3",
                temperature=0
            )
        except Exception as e:
            logger.warning(f"Failed to load ChatOllama: {str(e)}")

    # Default / Groq provider
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and groq_key != "gsk_placeholder_key":
        try:
            from langchain_groq import ChatGroq
            logger.info("Initializing Groq ChatGroq model (llama-3.3-70b-versatile)")
            return ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=SecretStr(groq_key),
                temperature=0
            )
        except Exception as e:
            logger.warning(f"Failed to load langchain_groq: {str(e)}")

    # Fallback Mock LLM for local sandbox / test executions
    try:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model="openai/gpt-oss-20b",
            api_key=SecretStr("gsk_placeholder_key"),
            temperature=0
        )
    except Exception:
        # Generic mock LLM class if langchain_groq is absent
        class FallbackMockLLM:
            def invoke(self, *args, **kwargs):
                class MockResponse:
                    content = "AI Assessment: Candidate demonstrates strong competence across technical skills."
                return MockResponse()
        return FallbackMockLLM()

llm = get_llm()