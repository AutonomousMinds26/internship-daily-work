import { api } from './api';
import {
  ScreeningBatchResult,
  PredictiveAnalyticsResult,
  DiversityInsightsReport
} from '../types';

export const aiService = {
  async getAIScore(candidateId: number, jobId?: number): Promise<any> {
    const response = await api.post('/ai/score', { candidate_id: candidateId, job_id: jobId });
    return response.data;
  },

  async getAISummary(candidateId: number): Promise<any> {
    const response = await api.post('/ai/summary', { candidate_id: candidateId });
    return response.data;
  },

  async getSkillGap(candidateId: number, jobId?: number): Promise<any> {
    const response = await api.post('/ai/skill-gap', { candidate_id: candidateId, job_id: jobId });
    return response.data;
  },

  async getInterviewQuestions(candidateId: number, jobId?: number): Promise<any[]> {
    const response = await api.post('/ai/interview-questions', { candidate_id: candidateId, job_id: jobId });
    return response.data;
  },

  async getRecommendation(candidateId: number, jobId?: number): Promise<any> {
    const response = await api.post('/ai/recommendation', { candidate_id: candidateId, job_id: jobId });
    return response.data;
  },

  async getScreeningQuestions(candidateId: number, jobId?: number): Promise<any> {
    const response = await api.post('/ai/screening/questions', { candidate_id: candidateId, job_id: jobId });
    return response.data;
  },

  async evaluateScreeningAnswers(candidateId: number, answers: string[]): Promise<ScreeningBatchResult> {
    const response = await api.post('/ai/screening/evaluate', {
      candidate_id: candidateId,
      answers
    });
    return response.data;
  },

  async getPredictiveAnalytics(candidateId: number): Promise<PredictiveAnalyticsResult> {
    const response = await api.get(`/ai/predictions/${candidateId}`);
    return response.data;
  },

  async getDiversityReport(): Promise<DiversityInsightsReport> {
    const response = await api.get('/reports/diversity');
    return response.data;
  },

  async getPipelineReport(): Promise<any> {
    const response = await api.get('/reports/pipeline');
    return response.data;
  },

  async sendEmail(toEmail: string, subject: string, body: string): Promise<any> {
    const response = await api.post('/email/send', {
      to_email: toEmail,
      subject,
      body
    });
    return response.data;
  }
};
