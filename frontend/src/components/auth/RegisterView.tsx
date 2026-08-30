import React, { useState } from 'react';
import {
  Sparkles, UserPlus, Eye, EyeOff, User, Lock, Mail,
  ArrowLeft, CheckCircle, AlertCircle, ShieldCheck
} from 'lucide-react';
import { authService } from '../../services/authService';
import type { User as UserType, UserRole } from '../../types';

interface RegisterViewProps {
  onRegisterSuccess: (user: UserType) => void;
  onBackToLogin: () => void;
}

const ROLES: { value: UserRole; label: string; description: string; color: string; bg: string }[] = [
  { value: 'Candidate', label: 'Candidate', description: 'Apply to jobs & track status', color: '#22D3EE', bg: 'rgba(6,182,212,0.15)' },
  { value: 'Recruiter', label: 'Recruiter', description: 'Manage pipeline & AI screening', color: '#818CF8', bg: 'rgba(99,102,241,0.15)' },
  { value: 'Hiring Manager', label: 'Hiring Manager', description: 'Review shortlists & approve', color: '#FBBF24', bg: 'rgba(245,158,11,0.15)' },
  { value: 'Admin', label: 'Admin', description: 'Full system access & control', color: '#34D399', bg: 'rgba(16,185,129,0.15)' },
];

function getPasswordStrength(pwd: string): { score: number; label: string; color: string } {
  if (!pwd) return { score: 0, label: '', color: '#334155' };
  let score = 0;
  if (pwd.length >= 8) score++;
  if (pwd.length >= 12) score++;
  if (/[A-Z]/.test(pwd)) score++;
  if (/[0-9]/.test(pwd)) score++;
  if (/[^A-Za-z0-9]/.test(pwd)) score++;
  if (score <= 1) return { score, label: 'Weak', color: '#EF4444' };
  if (score <= 2) return { score, label: 'Fair', color: '#F59E0B' };
  if (score <= 3) return { score, label: 'Good', color: '#3B82F6' };
  return { score, label: 'Strong', color: '#10B981' };
}

export const RegisterView: React.FC<RegisterViewProps> = ({ onRegisterSuccess, onBackToLogin }) => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<UserRole>('Candidate');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const strength = getPasswordStrength(password);
  const passwordsMatch = password === confirmPassword && confirmPassword.length > 0;

  const validate = () => {
    if (!username.trim() || username.length < 3) return 'Username must be at least 3 characters.';
    if (!/^[a-zA-Z0-9._@-]+$/.test(username)) return 'Username can only contain letters, numbers, . _ @ -';
    if (!password || password.length < 6) return 'Password must be at least 6 characters.';
    if (password !== confirmPassword) return 'Passwords do not match.';
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    const validationError = validate();
    if (validationError) { setError(validationError); return; }

    setLoading(true);
    try {
      const user = await authService.register({
        username: username.trim(),
        password,
        role,
        full_name: fullName.trim() || undefined,
        email: email.trim() || undefined,
      });
      setSuccess('Account created! Redirecting to your dashboard...');
      setTimeout(() => onRegisterSuccess(user), 1200);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const inputBase: React.CSSProperties = {
    width: '100%',
    padding: '12px 16px 12px 42px',
    borderRadius: '10px',
    border: '1px solid rgba(51, 65, 85, 0.6)',
    background: 'rgba(15, 23, 42, 0.7)',
    color: '#F8FAFC',
    fontSize: '14px',
    outline: 'none',
    boxSizing: 'border-box',
  };

  const iconWrap: React.CSSProperties = {
    position: 'absolute',
    left: '14px',
    top: '50%',
    transform: 'translateY(-50%)',
    pointerEvents: 'none',
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(99,102,241,0.18) 0%, transparent 60%), #060D1A',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px 16px',
    }}>
      <div style={{ position: 'fixed', top: '-120px', left: '-80px', width: '400px', height: '400px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)', pointerEvents: 'none' }} />
      <div style={{ position: 'fixed', bottom: '-100px', right: '-60px', width: '350px', height: '350px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(6,182,212,0.10) 0%, transparent 70%)', pointerEvents: 'none' }} />

      <div style={{ width: '100%', maxWidth: '520px', position: 'relative', zIndex: 1 }}>
        <div style={{
          background: 'rgba(13, 22, 40, 0.85)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(99, 102, 241, 0.2)',
          borderRadius: '20px',
          padding: '40px 36px',
          boxShadow: '0 25px 60px rgba(0,0,0,0.5)',
        }}>
          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: '28px' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '16px', background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', boxShadow: '0 8px 24px rgba(99,102,241,0.4)' }}>
              <UserPlus size={26} color="#FFFFFF" />
            </div>
            <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#F8FAFC', margin: '0 0 6px', letterSpacing: '-0.03em' }}>Create Your Account</h1>
            <p style={{ fontSize: '14px', color: '#94A3B8', margin: 0 }}>Join RecruiterAI — the autonomous talent intelligence platform</p>
          </div>

          {success && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px 16px', borderRadius: '10px', background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)', marginBottom: '20px' }}>
              <CheckCircle size={18} color="#34D399" />
              <span style={{ color: '#34D399', fontSize: '14px', fontWeight: 600 }}>{success}</span>
            </div>
          )}

          {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px 16px', borderRadius: '10px', background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', marginBottom: '20px' }}>
              <AlertCircle size={18} color="#F87171" />
              <span style={{ color: '#F87171', fontSize: '14px' }}>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Role selector */}
            <div style={{ marginBottom: '22px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '10px' }}>Select Your Role</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                {ROLES.map(r => (
                  <button key={r.value} type="button" onClick={() => setRole(r.value)} style={{ padding: '10px 12px', borderRadius: '10px', border: role === r.value ? `1.5px solid ${r.color}` : '1.5px solid rgba(51,65,85,0.5)', background: role === r.value ? r.bg : 'rgba(15,23,42,0.5)', cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s', boxShadow: role === r.value ? `0 0 12px ${r.color}25` : 'none' }}>
                    <div style={{ fontSize: '13px', fontWeight: 700, color: role === r.value ? r.color : '#CBD5E1' }}>{r.label}</div>
                    <div style={{ fontSize: '11px', color: '#64748B', marginTop: '2px', lineHeight: 1.3 }}>{r.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Full Name */}
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#94A3B8', marginBottom: '6px' }}>Full Name <span style={{ color: '#64748B' }}>(optional)</span></label>
              <div style={{ position: 'relative' }}>
                <span style={iconWrap}><User size={15} color="#64748B" /></span>
                <input type="text" placeholder="e.g. Rahul Sharma" value={fullName} onChange={e => setFullName(e.target.value)} style={inputBase} />
              </div>
            </div>

            {/* Email */}
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#94A3B8', marginBottom: '6px' }}>Email Address <span style={{ color: '#64748B' }}>(optional)</span></label>
              <div style={{ position: 'relative' }}>
                <span style={iconWrap}><Mail size={15} color="#64748B" /></span>
                <input type="email" placeholder="you@company.com" value={email} onChange={e => setEmail(e.target.value)} style={inputBase} />
              </div>
            </div>

            {/* Username */}
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#94A3B8', marginBottom: '6px' }}>Username <span style={{ color: '#EF4444' }}>*</span></label>
              <div style={{ position: 'relative' }}>
                <span style={iconWrap}><ShieldCheck size={15} color="#64748B" /></span>
                <input type="text" placeholder="e.g. john_recruiter" value={username} onChange={e => setUsername(e.target.value.toLowerCase().replace(/\s+/g, '_'))} required style={{ ...inputBase, borderColor: username.length > 0 && username.length < 3 ? 'rgba(239,68,68,0.5)' : undefined }} />
              </div>
              {username.length > 0 && username.length < 3 && <p style={{ margin: '4px 0 0 4px', fontSize: '11px', color: '#EF4444' }}>At least 3 characters required</p>}
            </div>

            {/* Password */}
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#94A3B8', marginBottom: '6px' }}>Password <span style={{ color: '#EF4444' }}>*</span></label>
              <div style={{ position: 'relative' }}>
                <span style={iconWrap}><Lock size={15} color="#64748B" /></span>
                <input type={showPassword ? 'text' : 'password'} placeholder="Min. 6 characters" value={password} onChange={e => setPassword(e.target.value)} required style={{ ...inputBase, paddingRight: '42px' }} />
                <button type="button" onClick={() => setShowPassword(!showPassword)} style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
                  {showPassword ? <EyeOff size={16} color="#64748B" /> : <Eye size={16} color="#64748B" />}
                </button>
              </div>
              {password.length > 0 && (
                <div style={{ marginTop: '8px' }}>
                  <div style={{ display: 'flex', gap: '4px', marginBottom: '4px' }}>
                    {[1,2,3,4,5].map(i => <div key={i} style={{ flex: 1, height: '3px', borderRadius: '2px', background: i <= strength.score ? strength.color : '#1E293B', transition: 'background 0.3s' }} />)}
                  </div>
                  <p style={{ margin: 0, fontSize: '11px', color: strength.color, fontWeight: 600 }}>{strength.label}</p>
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#94A3B8', marginBottom: '6px' }}>Confirm Password <span style={{ color: '#EF4444' }}>*</span></label>
              <div style={{ position: 'relative' }}>
                <span style={iconWrap}><Lock size={15} color="#64748B" /></span>
                <input type={showConfirm ? 'text' : 'password'} placeholder="Re-enter password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required style={{ ...inputBase, paddingRight: '42px', borderColor: confirmPassword.length > 0 ? (passwordsMatch ? 'rgba(16,185,129,0.5)' : 'rgba(239,68,68,0.5)') : undefined }} />
                <button type="button" onClick={() => setShowConfirm(!showConfirm)} style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
                  {showConfirm ? <EyeOff size={16} color="#64748B" /> : <Eye size={16} color="#64748B" />}
                </button>
              </div>
              {confirmPassword.length > 0 && !passwordsMatch && <p style={{ margin: '4px 0 0 4px', fontSize: '11px', color: '#EF4444' }}>Passwords do not match</p>}
              {confirmPassword.length > 0 && passwordsMatch && <p style={{ margin: '4px 0 0 4px', fontSize: '11px', color: '#10B981', display: 'flex', alignItems: 'center', gap: '4px' }}><CheckCircle size={11} /> Passwords match</p>}
            </div>

            {/* Submit */}
            <button type="submit" disabled={loading || !!success} style={{ width: '100%', padding: '14px', borderRadius: '12px', border: 'none', background: loading || success ? 'rgba(99,102,241,0.4)' : 'linear-gradient(135deg, #6366F1 0%, #4F46E5 50%, #4338CA 100%)', color: '#FFFFFF', fontSize: '15px', fontWeight: 700, cursor: loading || success ? 'not-allowed' : 'pointer', letterSpacing: '0.02em', boxShadow: loading || success ? 'none' : '0 4px 20px rgba(99,102,241,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
              {loading ? (
                <><div style={{ width: '18px', height: '18px', border: '2px solid rgba(255,255,255,0.3)', borderTop: '2px solid white', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />Creating Account...</>
              ) : success ? (
                <><CheckCircle size={18} />Account Created!</>
              ) : (
                <><UserPlus size={18} />Create Account</>
              )}
            </button>

            <p style={{ textAlign: 'center', fontSize: '11px', color: '#475569', marginTop: '14px', lineHeight: 1.5 }}>
              By registering, you agree to RecruiterAI usage policies.<br />All AI decisions are merit-based and bias-free.
            </p>
          </form>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: '20px 0' }}>
            <div style={{ flex: 1, height: '1px', background: 'rgba(51,65,85,0.5)' }} />
            <span style={{ fontSize: '12px', color: '#475569' }}>Already have an account?</span>
            <div style={{ flex: 1, height: '1px', background: 'rgba(51,65,85,0.5)' }} />
          </div>

          <button type="button" onClick={onBackToLogin} style={{ width: '100%', padding: '12px', borderRadius: '10px', border: '1px solid rgba(99,102,241,0.3)', background: 'rgba(99,102,241,0.08)', color: '#818CF8', fontSize: '14px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            <ArrowLeft size={16} />Back to Sign In
          </button>
        </div>

        <div style={{ textAlign: 'center', marginTop: '20px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
          <Sparkles size={14} color="#6366F1" />
          <span style={{ fontSize: '12px', color: '#475569', fontWeight: 600 }}>RecruiterAI Portal v2.0 — Powered by LangGraph & Gemini</span>
        </div>
      </div>

      <style>{`
        @keyframes spin { 0%{transform:rotate(0deg)} 100%{transform:rotate(360deg)} }
        input:focus { border-color: rgba(99,102,241,0.6) !important; box-shadow: 0 0 0 3px rgba(99,102,241,0.1); }
      `}</style>
    </div>
  );
};
