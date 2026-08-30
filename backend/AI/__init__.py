import os
import sys

# Ensure backend and AI directories are in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ai_dir = os.path.abspath(os.path.dirname(__file__))
for p in [backend_dir, ai_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from AI.screening import (
    generate_questions,
    generate_screening_questionnaire,
    evaluate_answer,
    evaluate_answers,
    calculate_final_score
)
from AI.predictive import predict_hiring_outcome, get_sample_frontend_output
from AI.explainability import generate_candidate_explainability
from AI.scorer import calculate_enhanced_score, calculate_score, extract_years
from AI.ats_analyzer import analyze_ats
from AI.ai_matcher import ai_match_candidate
from AI.feedback_analyzer import analyze_feedback
from AI.document_reader import extract_resume_text
from AI.resume_extractor import extract_candidate_info
from AI.job_extractor import extract_job_info
from AI.diversity import generate_diversity_and_aggregate_insights
from AI.voice_screening import transcribe_and_evaluate_voice_answer
