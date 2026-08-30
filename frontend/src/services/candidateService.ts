import { api } from './api';
import { Candidate, CandidateHistoryItem, CandidateStatus } from '../types';

export const candidateService = {
  async getCandidates(params?: { skip?: number; limit?: number; status?: string; search?: string }): Promise<Candidate[]> {
    const response = await api.get('/candidates', { params });
    return Array.isArray(response.data) ? response.data : [response.data];
  },

  async getCandidatesWithDetails(): Promise<any[]> {
    const response = await api.get('/candidates-with-details');
    return response.data;
  },

  async getCandidate(id: number): Promise<Candidate> {
    const response = await api.get(`/candidates`, { params: { id } });
    return response.data;
  },

  async createCandidate(candidateData: Partial<Candidate>): Promise<Candidate> {
    const response = await api.post('/candidates', candidateData);
    return response.data;
  },

  async updateStatus(id: number, status: CandidateStatus): Promise<Candidate> {
    const response = await api.patch(`/candidates/${id}/status`, { status });
    return response.data;
  },

  async updateFeedback(id: number, feedback: string): Promise<Candidate> {
    const response = await api.patch(`/candidates/${id}/feedback`, { feedback });
    return response.data;
  },

  async uploadResume(file: File, jobId?: number, extractionMode = 'Standard'): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (jobId) {
      formData.append('job_id', jobId.toString());
    }
    formData.append('extraction_mode', extractionMode);

    const response = await api.post('/upload_resume', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async getCandidateHistory(id: number): Promise<CandidateHistoryItem[]> {
    const response = await api.get(`/candidates/${id}/history`);
    return response.data;
  },

  async compareCandidates(candidateIds: number[]): Promise<any[]> {
    const response = await api.get('/candidates/compare', {
      params: { candidate_ids: candidateIds.join(',') }
    });
    return response.data;
  }
};
