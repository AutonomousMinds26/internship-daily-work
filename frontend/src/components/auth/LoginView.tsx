import React, { useState } from 'react';
import { Sparkles, Shield, UserCheck, Briefcase, Lock, ArrowRight, UserPlus } from 'lucide-react';
import { UserRole, User } from '../../types';
import { authService } from '../../services/authService';
import { useToast } from '../layout/Toast';

interface LoginViewProps {
  onLoginSuccess: (user: User) => void;
  onNavigateToRegister?: () => void;
}

export const LoginView: React.FC<LoginViewProps> = ({ onLoginSuccess, onNavigateToRegister }) => {
  const [username, setUsername] = useState('recruiter_user');
  const [password, setPassword] = useState('password123');
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!username.trim()) {
      showToast('Please provide a username', 'error');
      return;
    }

    setLoading(true);
    try {
      const user = await authService.login(username, password);
      showToast(`Welcome back, ${user.username}! (${user.role})`, 'success');
      onLoginSuccess(user);
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Authentication failed. Please check credentials.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRoleQuickSelect = (roleName: UserRole, userHandle: string) => {
    setUsername(userHandle);
    setPassword('password123');
  };

  return (
    <div style={{
      minHeight: '100vh',
      width: '100vw',
      background: 'radial-gradient(ellipse at top, #1E1B4B 0%, #090D16 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px'
    }}>
      <div className="glass-panel animate-fade-in" style={{
        width: '100%',
        maxWidth: '460px',
        padding: '40px 32px',
        textAlign: 'center'
      }}>
        {/* Logo */}
        <div style={{
          width: '56px',
          height: '56px',
          borderRadius: '16px',
          background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 16px auto',
          boxShadow: '0 8px 24px rgba(99, 102, 241, 0.4)'
        }}>
          <Sparkles size={30} color="#FFFFFF" />
        </div>

        <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#F8FAFC' }}>RecruiterAI Portal</h1>
        <p style={{ fontSize: '13px', color: '#94A3B8', marginTop: '6px', marginBottom: '28px' }}>
          Autonomous Talent Intelligence & ATS Platform
        </p>

        {/* 1-Click Role Switcher */}
        <div style={{ marginBottom: '24px', textAlign: 'left' }}>
          <label style={{ fontSize: '12px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Quick Role Demo Switcher:
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '8px' }}>
            <button
              type="button"
              onClick={() => handleRoleQuickSelect('Recruiter', 'recruiter_user')}
              style={{
                padding: '8px',
                borderRadius: '8px',
                border: username === 'recruiter_user' ? '1px solid #6366F1' : '1px solid rgba(51, 65, 85, 0.5)',
                background: username === 'recruiter_user' ? 'rgba(99, 102, 241, 0.2)' : 'rgba(30, 41, 59, 0.6)',
                color: '#F8FAFC',
                fontSize: '12px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <UserCheck size={14} color="#818CF8" />
              <span>Recruiter</span>
            </button>

            <button
              type="button"
              onClick={() => handleRoleQuickSelect('Admin', 'admin_user')}
              style={{
                padding: '8px',
                borderRadius: '8px',
                border: username === 'admin_user' ? '1px solid #10B981' : '1px solid rgba(51, 65, 85, 0.5)',
                background: username === 'admin_user' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(30, 41, 59, 0.6)',
                color: '#F8FAFC',
                fontSize: '12px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Shield size={14} color="#34D399" />
              <span>Admin</span>
            </button>

            <button
              type="button"
              onClick={() => handleRoleQuickSelect('Hiring Manager', 'manager_user')}
              style={{
                padding: '8px',
                borderRadius: '8px',
                border: username === 'manager_user' ? '1px solid #F59E0B' : '1px solid rgba(51, 65, 85, 0.5)',
                background: username === 'manager_user' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(30, 41, 59, 0.6)',
                color: '#F8FAFC',
                fontSize: '12px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Briefcase size={14} color="#FBBF24" />
              <span>Hiring Manager</span>
            </button>

            <button
              type="button"
              onClick={() => handleRoleQuickSelect('Candidate', 'candidate_user')}
              style={{
                padding: '8px',
                borderRadius: '8px',
                border: username === 'candidate_user' ? '1px solid #06B6D4' : '1px solid rgba(51, 65, 85, 0.5)',
                background: username === 'candidate_user' ? 'rgba(6, 182, 212, 0.2)' : 'rgba(30, 41, 59, 0.6)',
                color: '#F8FAFC',
                fontSize: '12px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <UserCheck size={14} color="#22D3EE" />
              <span>Candidate</span>
            </button>
          </div>
        </div>

        {/* Login Form */}
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '16px', textAlign: 'left' }}>
          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px', display: 'block' }}>
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. recruiter_user"
              required
            />
          </div>

          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px', display: 'block' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
              <Lock size={16} color="#64748B" style={{ position: 'absolute', right: '12px', top: '12px' }} />
            </div>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
            style={{ width: '100%', justifyContent: 'center', marginTop: '12px', height: '44px' }}
          >
            {loading ? 'Authenticating...' : 'Sign In to Portal'}
            {!loading && <ArrowRight size={16} />}
          </button>
        </form>

        {/* Divider */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: '20px 0 16px' }}>
          <div style={{ flex: 1, height: '1px', background: 'rgba(51,65,85,0.5)' }} />
          <span style={{ fontSize: '12px', color: '#475569' }}>New to RecruiterAI?</span>
          <div style={{ flex: 1, height: '1px', background: 'rgba(51,65,85,0.5)' }} />
        </div>

        {/* Register link */}
        <button
          type="button"
          onClick={onNavigateToRegister}
          style={{
            width: '100%',
            padding: '12px',
            borderRadius: '10px',
            border: '1px solid rgba(6,182,212,0.3)',
            background: 'rgba(6,182,212,0.08)',
            color: '#22D3EE',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
          }}
        >
          <UserPlus size={16} />
          Create New Account
        </button>

        <p style={{ fontSize: '11px', color: '#64748B', marginTop: '16px' }}>
          Pre-seeded credentials: password123 across all roles.
        </p>
      </div>
    </div>
  );
};
