import { api } from './api';
import { AdminUser, IntegrationConfigItem, AuditLogItem, SystemStatusItem } from '../types';

export const adminService = {
  getUsers: async (): Promise<AdminUser[]> => {
    const res = await api.get<AdminUser[]>('/admin/users');
    return res.data;
  },

  createUser: async (user: Partial<AdminUser> & { password?: string }): Promise<AdminUser> => {
    const res = await api.post<AdminUser>('/admin/users', user);
    return res.data;
  },

  updateUserRole: async (id: number, role: string, isActive?: boolean): Promise<AdminUser> => {
    const res = await api.put<AdminUser>(`/admin/users/${id}/role`, { role, is_active: isActive });
    return res.data;
  },

  getIntegrations: async (): Promise<IntegrationConfigItem[]> => {
    const res = await api.get<IntegrationConfigItem[]>('/admin/integrations');
    return res.data;
  },

  configureIntegration: async (config: Partial<IntegrationConfigItem>): Promise<IntegrationConfigItem> => {
    const res = await api.post<IntegrationConfigItem>('/admin/integrations', config);
    return res.data;
  },

  getAuditLogs: async (action?: string): Promise<AuditLogItem[]> => {
    const query = action ? `?action=${encodeURIComponent(action)}` : '';
    const res = await api.get<AuditLogItem[]>(`/admin/audit-logs${query}`);
    return res.data;
  },

  getSystemStatus: async (): Promise<SystemStatusItem> => {
    const res = await api.get<SystemStatusItem>('/admin/system-status');
    return res.data;
  }
};
