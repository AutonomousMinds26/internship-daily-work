import React, { useState, useEffect } from 'react';
import {
  ShieldCheck, Users, Sliders, Activity, Server,
  CheckCircle, XCircle, RefreshCw, Key, Search,
  Lock, Eye, AlertCircle, Plus, Sparkles
} from 'lucide-react';
import { adminService } from '../../services/adminService';
import { AdminUser, IntegrationConfigItem, AuditLogItem, SystemStatusItem, UserRole } from '../../types';
import { useToast } from '../layout/Toast';

export const AdminConsole: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'system' | 'users' | 'integrations' | 'audit'>('system');
  const [systemStatus, setSystemStatus] = useState<SystemStatusItem | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [integrations, setIntegrations] = useState<IntegrationConfigItem[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [showCreateUserModal, setShowCreateUserModal] = useState<boolean>(false);
  const [newUsername, setNewUsername] = useState<string>('');
  const [newPassword, setNewPassword] = useState<string>('');
  const [newRole, setNewRole] = useState<UserRole>('Recruiter');
  const [newEmail, setNewEmail] = useState<string>('');
  const { showToast } = useToast();

  const loadData = async () => {
    setLoading(true);
    try {
      const [statusRes, usersRes, intRes, auditRes] = await Promise.all([
        adminService.getSystemStatus().catch(() => null),
        adminService.getUsers().catch(() => []),
        adminService.getIntegrations().catch(() => []),
        adminService.getAuditLogs().catch(() => [])
      ]);
      setSystemStatus(statusRes);
      setUsers(usersRes);
      setIntegrations(intRes);
      setAuditLogs(auditRes);
    } catch (e: any) {
      showToast('Failed to load administrative data.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRoleChange = async (userId: number, newRole: UserRole) => {
    try {
      await adminService.updateUserRole(userId, newRole);
      setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, role: newRole } : u)));
      showToast(`User role updated to ${newRole}`, 'success');
    } catch (e: any) {
      showToast('Failed to update role.', 'error');
    }
  };

  const handleToggleActive = async (user: AdminUser) => {
    try {
      const updated = !user.is_active;
      await adminService.updateUserRole(user.id, user.role, updated);
      setUsers((prev) => prev.map((u) => (u.id === user.id ? { ...u, is_active: updated } : u)));
      showToast(`User ${user.username} ${updated ? 'activated' : 'deactivated'}`, 'info');
    } catch (e: any) {
      showToast('Failed to toggle status.', 'error');
    }
  };

  const handleToggleIntegration = async (provider: IntegrationConfigItem) => {
    try {
      const updated = !provider.is_enabled;
      await adminService.configureIntegration({
        provider_name: provider.provider_name,
        provider_category: provider.provider_category,
        is_enabled: updated
      });
      setIntegrations((prev) =>
        prev.map((i) => (i.id === provider.id ? { ...i, is_enabled: updated } : i))
      );
      showToast(`${provider.provider_name} is now ${updated ? 'Enabled' : 'Disabled'}`, 'success');
    } catch (e: any) {
      showToast('Failed to update integration state.', 'error');
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsername || !newPassword) {
      showToast('Username and password are required.', 'error');
      return;
    }
    try {
      const created = await adminService.createUser({
        username: newUsername,
        password: newPassword,
        role: newRole,
        email: newEmail || undefined
      });
      setUsers((prev) => [created, ...prev]);
      setShowCreateUserModal(false);
      setNewUsername('');
      setNewPassword('');
      setNewEmail('');
      showToast(`User ${created.username} created successfully!`, 'success');
    } catch (e: any) {
      showToast(e.response?.data?.detail || 'Failed to create user.', 'error');
    }
  };

  const filteredLogs = auditLogs.filter(
    (log) =>
      log.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (log.username && log.username.toLowerCase().includes(searchQuery.toLowerCase())) ||
      log.resource_type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.05) 100%)',
        border: '1px solid rgba(99, 102, 241, 0.3)',
        borderRadius: '16px',
        padding: '24px 28px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: '#6366F1',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)'
          }}>
            <ShieldCheck size={26} color="#FFFFFF" />
          </div>
          <div>
            <h1 style={{ fontSize: '20px', fontWeight: 800, color: '#F8FAFC', margin: 0 }}>
              Administration & Platform Control Center
            </h1>
            <p style={{ fontSize: '13px', color: '#94A3B8', margin: '4px 0 0 0' }}>
              Role-Based Access Control, Integration API Keys, Audit Trail, and Celery Queue Health
            </p>
          </div>
        </div>

        <button
          onClick={loadData}
          className="btn-secondary"
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Navigation Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid rgba(51, 65, 85, 0.3)', paddingBottom: '8px' }}>
        {[
          { id: 'system', label: 'System Health & Worker', icon: Server },
          { id: 'users', label: 'User & Role Management', icon: Users },
          { id: 'integrations', label: 'Integrations & ATS', icon: Sliders },
          { id: 'audit', label: 'Security Audit Logs', icon: Activity }
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 18px',
                borderRadius: '10px',
                border: 'none',
                background: isActive ? '#1E293B' : 'transparent',
                color: isActive ? '#818CF8' : '#94A3B8',
                fontWeight: isActive ? 700 : 500,
                fontSize: '14px',
                cursor: 'pointer',
                borderBottom: isActive ? '2px solid #6366F1' : '2px solid transparent'
              }}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: System Health */}
      {activeTab === 'system' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
          <div className="card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
              <Server size={20} color="#6366F1" />
              <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>Core API & Database</h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94A3B8' }}>Overall Status:</span>
                <span className="badge badge-emerald">{systemStatus?.status || 'Healthy'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94A3B8' }}>Database Engine:</span>
                <span style={{ fontWeight: 600, color: '#F1F5F9' }}>{systemStatus?.database?.type || 'SQLite'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94A3B8' }}>Registered Candidates:</span>
                <span style={{ fontWeight: 600, color: '#F1F5F9' }}>{systemStatus?.database?.counts?.candidates || 0}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94A3B8' }}>Open Job Requisitions:</span>
                <span style={{ fontWeight: 600, color: '#F1F5F9' }}>{systemStatus?.database?.counts?.jobs || 0}</span>
              </div>
            </div>
          </div>

          <div className="card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
              <Activity size={20} color="#10B981" />
              <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>Celery & Redis Worker</h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94A3B8' }}>Task Queue Broker:</span>
                <span style={{ fontWeight: 600, color: '#F1F5F9' }}>{systemStatus?.background_worker?.broker || 'Redis'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94A3B8' }}>Worker Execution Mode:</span>
                <span className="badge badge-indigo">{systemStatus?.background_worker?.status || 'Online'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94A3B8' }}>Task Serialization:</span>
                <span style={{ fontWeight: 600, color: '#F1F5F9' }}>JSON (UTC Safe)</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94A3B8' }}>Retry Strategy:</span>
                <span style={{ fontWeight: 600, color: '#F1F5F9' }}>Exponential Backoff (3x)</span>
              </div>
            </div>
          </div>

          <div className="card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
              <Sparkles size={20} color="#F59E0B" />
              <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>AI & Language Models</h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94A3B8' }}>Active LLM Provider:</span>
                <span className="badge badge-amber">{systemStatus?.llm_provider?.active_provider || 'Groq'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94A3B8' }}>Architecture:</span>
                <span style={{ fontWeight: 600, color: '#F1F5F9' }}>Multi-stage LangGraph</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94A3B8' }}>Integrations Mode:</span>
                <span style={{ fontWeight: 600, color: '#F1F5F9' }}>{systemStatus?.integrations_mode || 'Mock / Sandbox'}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Users & Roles */}
      {activeTab === 'users' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>Platform Users & Role Assignments</h3>
            <button
              onClick={() => setShowCreateUserModal(true)}
              className="btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <Plus size={16} />
              <span>Create New User</span>
            </button>
          </div>

          <div className="card" style={{ overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
              <thead>
                <tr style={{ background: '#0F172A', borderBottom: '1px solid rgba(51, 65, 85, 0.4)' }}>
                  <th style={{ padding: '14px 20px', color: '#94A3B8', fontWeight: 600 }}>User ID</th>
                  <th style={{ padding: '14px 20px', color: '#94A3B8', fontWeight: 600 }}>Username</th>
                  <th style={{ padding: '14px 20px', color: '#94A3B8', fontWeight: 600 }}>Role</th>
                  <th style={{ padding: '14px 20px', color: '#94A3B8', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: '14px 20px', color: '#94A3B8', fontWeight: 600 }}>Created Date</th>
                  <th style={{ padding: '14px 20px', color: '#94A3B8', fontWeight: 600, textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} style={{ borderBottom: '1px solid rgba(51, 65, 85, 0.2)' }}>
                    <td style={{ padding: '14px 20px', color: '#64748B' }}>#{user.id}</td>
                    <td style={{ padding: '14px 20px', fontWeight: 600, color: '#F1F5F9' }}>{user.username}</td>
                    <td style={{ padding: '14px 20px' }}>
                      <select
                        value={user.role}
                        onChange={(e) => handleRoleChange(user.id, e.target.value as UserRole)}
                        style={{
                          background: '#1E293B',
                          color: '#F8FAFC',
                          border: '1px solid rgba(51, 65, 85, 0.6)',
                          borderRadius: '6px',
                          padding: '4px 8px',
                          fontSize: '13px',
                          cursor: 'pointer'
                        }}
                      >
                        <option value="Admin">Admin</option>
                        <option value="Recruiter">Recruiter</option>
                        <option value="Hiring Manager">Hiring Manager</option>
                        <option value="Candidate">Candidate</option>
                      </select>
                    </td>
                    <td style={{ padding: '14px 20px' }}>
                      <span className={`badge ${user.is_active ? 'badge-emerald' : 'badge-rose'}`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td style={{ padding: '14px 20px', color: '#94A3B8', fontSize: '13px' }}>
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '14px 20px', textAlign: 'right' }}>
                      <button
                        onClick={() => handleToggleActive(user)}
                        className="btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '12px' }}
                      >
                        {user.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Integrations */}
      {activeTab === 'integrations' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>External Integration Providers</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
            {integrations.map((item) => (
              <div key={item.id} className="card" style={{ padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div>
                    <h4 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>{item.provider_name}</h4>
                    <span className="badge badge-indigo" style={{ marginTop: '4px' }}>{item.provider_category}</span>
                  </div>
                  <button
                    onClick={() => handleToggleIntegration(item)}
                    style={{
                      border: 'none',
                      background: item.is_enabled ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                      color: item.is_enabled ? '#34D399' : '#F87171',
                      padding: '6px 12px',
                      borderRadius: '8px',
                      fontWeight: 700,
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    {item.is_enabled ? 'Active' : 'Disabled'}
                  </button>
                </div>
                <p style={{ fontSize: '13px', color: '#94A3B8', margin: '0 0 12px 0' }}>
                  Configuration: {item.config_data?.status || 'Sandboxed'}
                </p>
                <div style={{ fontSize: '11px', color: '#64748B' }}>
                  Last Synced: {item.last_sync_at ? new Date(item.last_sync_at).toLocaleString() : 'Live Connected'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 4: Audit Logs */}
      {activeTab === 'audit' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>System Activity & Security Audit Trail</h3>
            <div style={{ position: 'relative', width: '280px' }}>
              <Search size={16} color="#64748B" style={{ position: 'absolute', left: '12px', top: '10px' }} />
              <input
                type="text"
                placeholder="Filter by action or user..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input-field"
                style={{ paddingLeft: '36px', height: '36px', fontSize: '13px' }}
              />
            </div>
          </div>

          <div className="card" style={{ overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: '#0F172A', borderBottom: '1px solid rgba(51, 65, 85, 0.4)' }}>
                  <th style={{ padding: '12px 18px', color: '#94A3B8', fontWeight: 600 }}>Timestamp</th>
                  <th style={{ padding: '12px 18px', color: '#94A3B8', fontWeight: 600 }}>User</th>
                  <th style={{ padding: '12px 18px', color: '#94A3B8', fontWeight: 600 }}>Action</th>
                  <th style={{ padding: '12px 18px', color: '#94A3B8', fontWeight: 600 }}>Resource</th>
                  <th style={{ padding: '12px 18px', color: '#94A3B8', fontWeight: 600 }}>Details</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.slice(0, 50).map((log) => (
                  <tr key={log.id} style={{ borderBottom: '1px solid rgba(51, 65, 85, 0.2)' }}>
                    <td style={{ padding: '12px 18px', color: '#94A3B8', whiteSpace: 'nowrap' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td style={{ padding: '12px 18px', fontWeight: 600, color: '#F1F5F9' }}>
                      {log.username || 'System'}
                    </td>
                    <td style={{ padding: '12px 18px' }}>
                      <span className="badge badge-indigo">{log.action}</span>
                    </td>
                    <td style={{ padding: '12px 18px', color: '#CBD5E1' }}>
                      {log.resource_type} {log.resource_id ? `#${log.resource_id}` : ''}
                    </td>
                    <td style={{ padding: '12px 18px', color: '#64748B', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {JSON.stringify(log.details || {})}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateUserModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.75)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100
        }}>
          <div className="card" style={{ width: '440px', padding: '24px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 700, margin: '0 0 16px 0' }}>Create Platform User</h3>
            <form onSubmit={handleCreateUser} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '4px', display: 'block' }}>Username</label>
                <input
                  type="text"
                  required
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  className="input-field"
                  placeholder="e.g. rahul.recruiter"
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '4px', display: 'block' }}>Email (Optional)</label>
                <input
                  type="email"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="input-field"
                  placeholder="user@example.com"
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '4px', display: 'block' }}>Password</label>
                <input
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="input-field"
                  placeholder="Min 6 characters"
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '4px', display: 'block' }}>Assigned Role</label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value as UserRole)}
                  className="input-field"
                >
                  <option value="Recruiter">Recruiter</option>
                  <option value="Hiring Manager">Hiring Manager</option>
                  <option value="Admin">Admin</option>
                  <option value="Candidate">Candidate</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
                <button type="button" onClick={() => setShowCreateUserModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
