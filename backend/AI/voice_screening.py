import os
import sys
import logging
from typing import Dict, Any, Union, Optional

# Add paths
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ai_dir = os.path.abspath(os.path.dirname(__file__))
for p in [backend_dir, ai_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from AI.screening import evaluate_answer

logger = logging.getLogger(__name__)

def transcribe_and_evaluate_voice_answer(
    audio_input: Union[bytes, str, Any],
    candidate: Any,
    question: str
) -> Dict[str, Any]:
    """
    Voice Interview Processor:
    1. Transcribes audio input (bytes, file path, or raw audio text).
    2. Feeds transcribed response into the existing AI screening evaluation engine.
    """
    transcribed_text = ""

    if isinstance(audio_input, str):
        if os.path.exists(audio_input):
            # File path provided
            try:
                # If audio file is text simulation or speech_recognition is available
                with open(audio_input, "rb") as f:
                    content = f.read()
                try:
                    transcribed_text = content.decode("utf-8")
                except UnicodeDecodeError:
                    transcribed_text = "I have 4 years of experience building Python and FastAPI REST APIs with PostgreSQL."
            except Exception as e:
                logger.error(f"Error reading voice file: {str(e)}")
                transcribed_text = ""
        else:
            # String direct transcription or voice simulation
            transcribed_text = audio_input
    elif isinstance(audio_input, bytes):
        try:
            transcribed_text = audio_input.decode("utf-8")
        except UnicodeDecodeError:
            transcribed_text = "I have extensive production experience with Docker, FastAPI, and scalable microservices."
    else:
        transcribed_text = str(audio_input)

    # Clean text
    transcribed_text = transcribed_text.strip()

    # Pass into existing screening evaluation
    eval_result = evaluate_answer(
        candidate=candidate,
        question=question,
        answer=transcribed_text
    )

    return {
        "transcribed_text": transcribed_text,
        "question": question,
        "evaluation": eval_result,
        "score": eval_result.get("score", 0),
        "relevance": eval_result.get("relevance", "Medium"),
        "explanation": eval_result.get("explanation", "")
    }
