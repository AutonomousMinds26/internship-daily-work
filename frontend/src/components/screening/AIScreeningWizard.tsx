import React, { useState } from 'react';
import { Bot, Sparkles, CheckCircle2, AlertTriangle, ArrowRight, Loader2, RefreshCw } from 'lucide-react';
import { Candidate, Job, ScreeningBatchResult } from '../../types';
import { aiService } from '../../services/aiService';
import { useToast } from '../layout/Toast';

interface AIScreeningWizardProps {
  candidates: Candidate[];
  jobs: Job[];
}

export const AIScreeningWizard: React.FC<AIScreeningWizardProps> = ({
  candidates,
  jobs
}) => {
  const [selectedCandId, setSelectedCandId] = useState<number>(candidates[0]?.id || 1);
  const [selectedJobId, setSelectedJobId] = useState<number>(jobs[0]?.id || 1);
  const [step, setStep] = useState<'select' | 'questions' | 'results'>('select');
  const [questions, setQuestions] = useState<string[]>([]);
  const [answers, setAnswers] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState<ScreeningBatchResult | null>(null);
  const { showToast } = useToast();

  const selectedCand = candidates.find((c) => c.id === selectedCandId) || candidates[0];
  const selectedJob = jobs.find((j) => j.id === selectedJobId) || jobs[0];

  const handleGenerateQuestions = async () => {
    setLoading(true);
    try {
      const res = await aiService.getScreeningQuestions(selectedCandId, selectedJobId);
      // API returns categorized: { technical_questions, experience_questions, availability_questions, ... }
      const allQ: string[] = [
        ...(res.technical_questions || []),
        ...(res.experience_questions || []),
        ...(res.availability_questions || []),
        ...(res.salary_questions || []),
        ...(res.location_questions || []),
        ...(res.all_questions || [])
      ].filter((q: string, i: number, arr: string[]) => arr.indexOf(q) === i); // dedupe

      const qList = allQ.length > 0 ? allQ : [
        `Can you describe your hands-on experience working with ${selectedCand?.skills?.[0] || 'Python'}?`,
        `How many years of professional backend engineering experience do you possess?`,
        `What is your official notice period and earliest joining date?`,
        `What are your fixed and variable CTC salary expectations?`,
        `Are you comfortable working from ${selectedJob?.location || 'Pune'}?`
      ];
      setQuestions(qList);
      setAnswers(new Array(qList.length).fill(''));
      setStep('questions');
      showToast('AI screening questions generated successfully!', 'success');
    } catch (e: any) {
      showToast('Generated fallback screening questionnaire.', 'info');
      const fallbackQs = [
        `Can you describe your hands-on experience working with ${selectedCand?.skills?.[0] || 'Python'}?`,
        `How many years of professional backend engineering experience do you possess?`,
        `What is your official notice period and earliest joining date?`,
        `What are your fixed and variable CTC salary expectations?`,
        `Are you comfortable working from ${selectedJob?.location || 'Pune'}?`
      ];
      setQuestions(fallbackQs);
      setAnswers(new Array(fallbackQs.length).fill(''));
      setStep('questions');
    } finally {
      setLoading(false);
    }
  };

  const handlePrefillDemoAnswers = () => {
    const demoAnswers = [
      `I have 4+ years building high-throughput microservices using ${selectedCand?.skills?.slice(0, 2).join(' and ') || 'Python and FastAPI'}, integrating PostgreSQL and Redis caching.`,
      `I have ${selectedCand?.experience || 4} years of experience designing and deploying cloud-native REST APIs.`,
      `My official notice period is 30 days, but I am serving notice and can join within 15 days.`,
      `My expected compensation is ${selectedCand?.expected_ctc || '18 LPA'}, open to discussion based on role.`,
      `Yes, I am completely comfortable relocating and working from ${selectedJob?.location || 'Pune'}.`
    ];
    setAnswers(demoAnswers);
    showToast('Pre-filled realistic candidate responses for demo!', 'info');
  };

  const handleEvaluateAnswers = async () => {
    setLoading(true);
    try {
      const result = await aiService.evaluateScreeningAnswers(selectedCandId, answers, questions);
      setEvaluationResult(result);
      setStep('results');
      showToast(`Evaluation completed! Score: ${result.screening_score}%`, 'success');
    } catch (e: any) {
      showToast('Failed to evaluate screening answers.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ maxWidth: '850px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Bot size={22} color="#FFFFFF" />
          </div>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#F8FAFC' }}>AI Screening Questionnaire & Evaluation</h2>
            <p style={{ fontSize: '12px', color: '#94A3B8' }}>Automate pre-interview qualification, technical verification, and logistical alignment</p>
          </div>
        </div>
      </div>

      {/* STEP 1: SELECT CANDIDATE & JOB */}
      {step === 'select' && (
        <div className="glass-panel animate-fade-in" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#F8FAFC' }}>Step 1: Select Candidate & Requisition</h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px', display: 'block' }}>
                Select Candidate:
              </label>
              <select
                value={selectedCandId}
                onChange={(e) => setSelectedCandId(Number(e.target.value))}
                style={{ height: '42px', background: '#0F172A' }}
              >
                {candidates.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.email}) — {c.experience || 0} yrs exp
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px', display: 'block' }}>
                Select Target Job Requisition:
              </label>
              <select
                value={selectedJobId}
                onChange={(e) => setSelectedJobId(Number(e.target.value))}
                style={{ height: '42px', background: '#0F172A' }}
              >
                {jobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.title} ({j.location || 'Pune'})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            onClick={handleGenerateQuestions}
            className="btn-primary"
            disabled={loading}
            style={{ width: '100%', justifyContent: 'center', height: '44px', marginTop: '10px' }}
          >
            {loading ? <Loader2 size={18} className="spin" /> : <Sparkles size={18} />}
            <span>{loading ? 'Generating Questionnaire...' : 'Generate Dynamic Screening Questions'}</span>
          </button>
        </div>
      )}

      {/* STEP 2: ANSWER QUESTIONS */}
      {step === 'questions' && (
        <div className="glass-panel animate-fade-in" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#F8FAFC' }}>
                Step 2: Candidate Responses for {selectedCand?.name}
              </h3>
              <p style={{ fontSize: '12px', color: '#94A3B8' }}>Enter responses or pre-fill for fast demonstration</p>
            </div>
            <button
              onClick={handlePrefillDemoAnswers}
              className="btn-secondary btn-sm"
              style={{ borderColor: '#6366F1', color: '#818CF8' }}
            >
              <Sparkles size={14} />
              <span>Pre-fill Demo Answers</span>
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {questions.map((q, idx) => (
              <div key={idx} style={{
                background: 'rgba(15, 23, 42, 0.7)',
                padding: '16px',
                borderRadius: '12px',
                border: '1px solid rgba(51, 65, 85, 0.5)'
              }}>
                <div style={{ fontWeight: 700, fontSize: '13px', color: '#F8FAFC', marginBottom: '8px' }}>
                  Q{idx + 1}: {q}
                </div>
                <textarea
                  rows={2}
                  value={answers[idx] || ''}
                  onChange={(e) => {
                    const newAns = [...answers];
                    newAns[idx] = e.target.value;
                    setAnswers(newAns);
                  }}
                  placeholder="Enter candidate's answer..."
                />
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: '12px', marginTop: '10px' }}>
            <button onClick={() => setStep('select')} className="btn-secondary" style={{ flex: 1, justifyContent: 'center' }}>
              Back
            </button>
            <button
              onClick={handleEvaluateAnswers}
              className="btn-primary"
              disabled={loading}
              style={{ flex: 2, justifyContent: 'center', height: '44px' }}
            >
              {loading ? <Loader2 size={18} className="spin" /> : <CheckCircle2 size={18} />}
              <span>{loading ? 'Evaluating Answers...' : 'Run AI Evaluation & Score'}</span>
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: EVALUATION RESULTS */}
      {step === 'results' && evaluationResult && (
        <div className="glass-panel animate-fade-in" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#F8FAFC' }}>
                AI Screening Evaluation Outcome
              </h3>
              <p style={{ fontSize: '12px', color: '#94A3B8' }}>{selectedCand?.name} • {selectedJob?.title}</p>
            </div>
            <button onClick={() => setStep('select')} className="btn-secondary btn-sm">
              <RefreshCw size={14} />
              <span>Screen Another Candidate</span>
            </button>
          </div>

          {/* Score Header Card */}
          <div style={{
            padding: '20px',
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(16, 185, 129, 0.15) 100%)',
            border: '1px solid rgba(99, 102, 241, 0.4)',
            borderRadius: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase' }}>Overall Screening Score</div>
              <div style={{ fontSize: '36px', fontWeight: 800, color: '#F8FAFC', marginTop: '4px' }}>
                {evaluationResult.screening_score}%
              </div>
              <div style={{ fontSize: '13px', color: '#34D399', fontWeight: 600, marginTop: '2px' }}>
                Recommendation: {evaluationResult.screening_score >= 80 ? 'Strong Candidate' : 'Qualified Candidate'}
              </div>
            </div>

            <div style={{ textAlign: 'right', maxWidth: '380px' }}>
              <p style={{ fontSize: '13px', color: '#CBD5E1', lineHeight: '1.5' }}>
                {evaluationResult.summary}
              </p>
            </div>
          </div>

          {/* Question-by-Question Score Table */}
          <div>
            <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#F8FAFC', marginBottom: '12px' }}>
              Detailed Question Assessment Breakdown
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {evaluationResult.evaluations.map((ev, idx) => (
                <div key={idx} style={{
                  padding: '14px 18px',
                  background: 'rgba(15, 23, 42, 0.7)',
                  borderRadius: '12px',
                  border: '1px solid rgba(51, 65, 85, 0.5)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, fontSize: '13px', color: '#F8FAFC' }}>
                      Q{idx + 1}: {ev.question || questions[idx]}
                    </span>
                    <span className={`badge ${ev.score >= 8 ? 'badge-emerald' : ev.score >= 5 ? 'badge-indigo' : 'badge-amber'}`}>
                      Score: {ev.score}/10 ({ev.relevance})
                    </span>
                  </div>
                  <div style={{ fontSize: '12px', color: '#94A3B8' }}>
                    <b>Answer:</b> {ev.answer || answers[idx] || 'N/A'}
                  </div>
                  <div style={{ fontSize: '12px', color: '#A5B4FC', marginTop: '2px' }}>
                    <b>AI Feedback:</b> {ev.explanation}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
