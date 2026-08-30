import { api } from './api';
import { User, UserRole } from '../types';

export const authService = {
  async login(username: string, password = 'password123'): Promise<User> {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post('/auth/token', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    const { access_token, role } = response.data;
    localStorage.setItem('recruiter_jwt_token', access_token);
    localStorage.setItem('recruiter_user_role', role);
    localStorage.setItem('recruiter_username', username);

    return {
      username,
      role: role as UserRole,
      token: access_token
    };
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch (e) {
      console.warn('Logout API error:', e);
    } finally {
      localStorage.removeItem('recruiter_jwt_token');
      localStorage.removeItem('recruiter_user_role');
      localStorage.removeItem('recruiter_username');
    }
  },

  getCurrentUser(): User | null {
    const token = localStorage.getItem('recruiter_jwt_token');
    const username = localStorage.getItem('recruiter_username');
    const role = localStorage.getItem('recruiter_user_role') as UserRole;

    if (token && username && role) {
      return { username, role, token };
    }
    return null;
  }
};
