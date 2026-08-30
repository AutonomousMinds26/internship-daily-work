import { api } from './api';
import { Job, Candidate } from '../types';

export const jobService = {
  async getJobs(): Promise<Job[]> {
    const response = await api.get('/jobs');
    return response.data;
  },

  async getJob(id: number): Promise<Job> {
    const response = await api.get(`/jobs/${id}`);
    return response.data;
  },

  async createJob(jobData: Partial<Job>): Promise<Job> {
    const response = await api.post('/jobs', jobData);
    return response.data;
  },

  async getJobCandidates(id: number): Promise<Candidate[]> {
    const response = await api.get(`/jobs/${id}/candidates`);
    return response.data;
  }
};
