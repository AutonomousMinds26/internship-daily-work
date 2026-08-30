import { api } from './api';
import { Interview, InterviewSlot } from '../types';

export const interviewService = {
  async getInterviews(): Promise<Interview[]> {
    const response = await api.get('/interviews');
    return response.data;
  },

  async createInterview(data: Partial<Interview>): Promise<Interview> {
    const response = await api.post('/interviews', data);
    return response.data;
  },

  async updateInterview(id: number, data: Partial<Interview>): Promise<Interview> {
    const response = await api.put(`/interviews/${id}`, data);
    return response.data;
  },

  async updateStatus(id: number, status: string): Promise<Interview> {
    const response = await api.patch(`/interviews/${id}/status`, { status });
    return response.data;
  },

  async deleteInterview(id: number): Promise<void> {
    await api.delete(`/interviews/${id}`);
  },

  async getAvailableSlots(): Promise<InterviewSlot[]> {
    const response = await api.get('/interviews/slots');
    return response.data;
  },

  async createSlot(data: { interviewer_name: string; interviewer_email: string; start_time: string; end_time: string }): Promise<InterviewSlot> {
    const response = await api.post('/interviews/slots', data);
    return response.data;
  },

  async bookSlot(slotId: number, candidateId: number, jobId: number): Promise<Interview> {
    const response = await api.post(`/interviews/slots/${slotId}/book`, {
      candidate_id: candidateId,
      job_id: jobId
    });
    return response.data;
  },

  getInviteDownloadUrl(interviewId: number): string {
    const baseURL = api.defaults.baseURL || 'http://localhost:8000';
    return `${baseURL}/interviews/${interviewId}/invite`;
  }
};
