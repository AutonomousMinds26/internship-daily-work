import { api } from './api';
import type {
  ScreeningBatchResult,
  PredictiveAnalyticsResult,
  DiversityInsightsReport
} from '../types';

export const aiService = {
  // GET /ai/score?candidate_id=X&job_id=Y
  async getAIScore(candidateId: number, jobId?: number): Promise<any> {
    const params: any = { candidate_id: candidateId };
    if (jobId) params.job_id = jobId;
    const response = await api.get('/ai/score', { params });
    return response.data;
  },

  // POST /ai/summary
  async getAISummary(candidateId: number): Promise<any> {
    const response = await api.post('/ai/summary', { candidate_id: candidateId });
    return response.data;
  },

  // POST /ai/skill-gap
  async getSkillGap(candidateId: number, jobId?: number): Promise<any> {
    const response = await api.post('/ai/skill-gap', { candidate_id: candidateId, job_id: jobId });
    return response.data;
  },

  // POST /ai/interview-questions
  async getInterviewQuestions(candidateId: number, jobId?: number): Promise<any[]> {
    const response = await api.post('/ai/interview-questions', { candidate_id: candidateId, job_id: jobId });
    return response.data;
  },

  // POST /ai/recommendation
  async getRecommendation(candidateId: number, jobId?: number): Promise<any> {
    const response = await api.post('/ai/recommendation', { candidate_id: candidateId, job_id: jobId });
    return response.data;
  },

  // POST /ai/screening-questionnaire?candidate_id=X&job_id=Y  (uses query params)
  async getScreeningQuestions(candidateId: number, jobId?: number): Promise<any> {
    const params: any = { candidate_id: candidateId };
    if (jobId) params.job_id = jobId;
    const response = await api.post('/ai/screening-questionnaire', null, { params });
    return response.data;
  },

  // POST /ai/evaluate-screening-response  — evaluates ONE Q&A at a time, we iterate
  async evaluateScreeningAnswers(candidateId: number, answers: string[], questions?: string[]): Promise<ScreeningBatchResult> {
    const evaluations: any[] = [];
    const totalQuestions = answers.length;

    for (let i = 0; i < totalQuestions; i++) {
      if (!answers[i] || !answers[i].trim()) continue;
      try {
        const res = await api.post('/ai/evaluate-screening-response', {
          candidate_id: candidateId,
          question: questions?.[i] || `Question ${i + 1}`,
          answer: answers[i]
        });
        evaluations.push({
          score: res.data.score || 7,
          relevance: res.data.relevance || 'Medium',
          concerns: res.data.concerns || [],
          explanation: res.data.explanation || 'Evaluated.',
          question: questions?.[i] || `Question ${i + 1}`,
          answer: answers[i]
        });
      } catch {
        evaluations.push({ score: 6, relevance: 'Medium', concerns: [], explanation: 'Could not evaluate this answer.', question: questions?.[i], answer: answers[i] });
      }
    }

    const avgScore = evaluations.length > 0
      ? Math.round(evaluations.reduce((s, e) => s + e.score, 0) / evaluations.length * 10)
      : 70;

    return {
      screening_score: avgScore,
      average_score_out_of_10: avgScore / 10,
      evaluations,
      concerns: evaluations.flatMap(e => e.concerns || []),
      strengths: evaluations.filter(e => e.score >= 8).map(e => e.question || 'Strong answer'),
      summary: `Candidate answered ${evaluations.length} of ${totalQuestions} questions. Overall screening score: ${avgScore}%.`
    };
  },

  // GET /candidates/{id}/prediction  (actual route from openapi)
  async getPredictiveAnalytics(candidateId: number): Promise<PredictiveAnalyticsResult> {
    const response = await api.get(`/candidates/${candidateId}/prediction`);
    return response.data;
  },

  // GET /analytics/diversity-analytics  (actual route from openapi)
  async getDiversityReport(): Promise<DiversityInsightsReport> {
    const response = await api.get('/analytics/diversity-analytics');
    return response.data;
  },

  // GET /analytics  (hiring funnel + status breakdown)
  async getPipelineReport(): Promise<any> {
    const response = await api.get('/analytics');
    return response.data;
  },

  // Email: use actual backend routes for shortlist/interview/rejection
  async sendEmail(toEmail: string, subject: string, body: string): Promise<any> {
    // Detect template type from subject line for proper routing
    if (subject.toLowerCase().includes('shortlist')) {
      const response = await api.post('/send-shortlist', { to_email: toEmail, subject, body });
      return response.data;
    } else if (subject.toLowerCase().includes('interview') || subject.toLowerCase().includes('invitation')) {
      const response = await api.post('/send-interview', { to_email: toEmail, subject, body });
      return response.data;
    } else if (subject.toLowerCase().includes('application status') || subject.toLowerCase().includes('rejection')) {
      const response = await api.post('/send-rejection', { to_email: toEmail, subject, body });
      return response.data;
    }
    // Generic fallback: try shortlist endpoint
    const response = await api.post('/send-shortlist', { to_email: toEmail, subject, body });
    return response.data;
  }
};
