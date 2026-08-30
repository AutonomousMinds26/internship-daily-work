import pytest
from AI.voice_screening import transcribe_and_evaluate_voice_answer

def test_voice_screening_evaluation():
    cand = {"name": "Audio Candidate", "skills": ["Python", "FastAPI"]}
    q = "Describe your Python and API development background."
    audio_sim = "I have spent four years architecting backend systems with Python and FastAPI."
    
    res = transcribe_and_evaluate_voice_answer(
        audio_input=audio_sim,
        candidate=cand,
        question=q
    )
    assert isinstance(res, dict)
    assert res["transcribed_text"] == audio_sim
    assert res["score"] >= 6
    assert res["relevance"] in ["High", "Medium"]
