import time
import statistics
from app.database import SessionLocal
from app.models import Candidate, Job
from app.tasks.recruitment_tasks import process_resume_task, bulk_screening_task
from app.services.sourcing_service import calculate_ats_and_match
from app.services.assessment_integration import CodeSandboxClient
from app.services.bias_detector import calculate_adverse_impact_ratio
from AI.workflow import run_lifecycle_recruitment_graph


def benchmark_suite():
    print("==================================================")
    print("RecruiterAI Track B Empirical Performance Benchmarks")
    print("==================================================")

    # 1. 11-Point Candidate Matching & ATS Calculation
    cand_data = {
        "id": 1,
        "name": "Amit Sharma",
        "email": "amit.sharma@example.com",
        "skills": ["Python", "FastAPI", "SQL", "Docker", "AWS", "Redis"],
        "experience": 4,
        "education": "B.Tech Computer Science (IIT Delhi)",
        "resume_text": "Experienced Python backend engineer specializing in high-throughput APIs."
    }
    job_data = {
        "id": 1,
        "title": "Senior Backend Developer",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "experience": 3,
        "min_salary": 2200000.0,
        "salary_currency": "INR"
    }

    matching_times = []
    for _ in range(100):
        t0 = time.perf_counter()
        res = calculate_ats_and_match(cand_data, job_data)
        matching_times.append((time.perf_counter() - t0) * 1000)

    avg_matching = statistics.mean(matching_times)
    p95_matching = statistics.quantiles(matching_times, n=20)[18]
    throughput_matching = 1000.0 / avg_matching

    print(f"1. Candidate Matching & ATS Scoring (100 iterations):")
    print(f"   - Average Latency: {avg_matching:.2f} ms")
    print(f"   - P95 Latency:     {p95_matching:.2f} ms")
    print(f"   - Throughput:      {throughput_matching:.1f} candidates/sec")

    # 2. Sandboxed Code Evaluation Execution
    sandbox = CodeSandboxClient()
    code = """
def solve(arr):
    return sum(x for x in arr if x % 2 == 0)
"""
    test_cases = [{"input": "[1, 2, 3, 4, 5, 6]", "expected": "12"}] * 5

    sandbox_times = []
    for _ in range(50):
        t0 = time.perf_counter()
        res = sandbox.execute_code("python", code, test_cases)
        sandbox_times.append((time.perf_counter() - t0) * 1000)

    avg_sandbox = statistics.mean(sandbox_times)
    print(f"\n2. Sandboxed Code Evaluation (50 runs, 5 test cases each):")
    print(f"   - Average Latency: {avg_sandbox:.2f} ms")

    # 3. Multi-Stage LangGraph Recruitment Lifecycle
    graph_times = []
    for _ in range(20):
        t0 = time.perf_counter()
        res = run_lifecycle_recruitment_graph(
            candidate_id=1,
            job_id=1,
            candidate_data=cand_data,
            job_data=job_data,
            assessment_provider="HackerRank"
        )
        graph_times.append((time.perf_counter() - t0) * 1000)

    avg_graph = statistics.mean(graph_times)
    p95_graph = statistics.quantiles(graph_times, n=20)[18] if len(graph_times) >= 20 else avg_graph

    print(f"\n3. LangGraph Multi-State Recruitment Pipeline (20 runs):")
    print(f"   - Average Latency: {avg_graph:.2f} ms")
    print(f"   - P95 Latency:     {p95_graph:.2f} ms")

    # 4. Celery Task Execution (Synchronous / Eager benchmark)
    task_times = []
    for _ in range(30):
        t0 = time.perf_counter()
        res = process_resume_task(candidate_id=1, raw_text="Senior Developer Resume Text", filename="resume.txt")
        task_times.append((time.perf_counter() - t0) * 1000)

    avg_task = statistics.mean(task_times)
    print(f"\n4. Celery Task Processing (Resume Ingestion + Vector Indexing, 30 runs):")
    print(f"   - Average Latency: {avg_task:.2f} ms")

    # 5. Bias Detection 4/5ths Rule Math
    bias_times = []
    for _ in range(200):
        t0 = time.perf_counter()
        calculate_adverse_impact_ratio(50, 40, 50, 45)
        bias_times.append((time.perf_counter() - t0) * 1000)

    avg_bias = statistics.mean(bias_times)
    print(f"\n5. Algorithmic Fairness & 4/5ths Rule Disparity Check (200 runs):")
    print(f"   - Average Latency: {avg_bias:.4f} ms")
    print("==================================================")


if __name__ == "__main__":
    benchmark_suite()
