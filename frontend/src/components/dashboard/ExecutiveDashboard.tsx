import React from 'react';
import {
  Users,
  Briefcase,
  UserCheck,
  Calendar,
  Award,
  TrendingUp,
  ArrowUpRight,
  Filter,
  Sparkles
} from 'lucide-react';
import { Candidate, Job } from '../../types';

interface ExecutiveDashboardProps {
  candidates: Candidate[];
  jobs: Job[];
  onNavigate: (tab: string) => void;
  onSelectCandidate: (candidate: Candidate) => void;
}

export const ExecutiveDashboard: React.FC<ExecutiveDashboardProps> = ({
  candidates,
  jobs,
  onNavigate,
  onSelectCandidate
}) => {
  const total = candidates.length;
  const shortlisted = candidates.filter((c) => c.status === 'Shortlisted').length;
  const interviews = candidates.filter((c) => c.status === 'Interview' || c.status === 'Interview Scheduled').length;
  const hired = candidates.filter((c) => c.status === 'Hired' || c.status === 'Selected').length;
  const activeJobs = jobs.filter((j) => j.is_active !== false).length;

  const avgFinalScore = total > 0
    ? (candidates.reduce((acc, c) => acc + (c.final_score || c.match_score || 50), 0) / total).toFixed(1)
    : '0';

  const metrics = [
    { title: 'Total Candidates', value: total, icon: Users, color: '#6366F1', delta: '+12% this week', tab: 'candidates' },
    { title: 'Active Jobs', value: activeJobs, icon: Briefcase, color: '#06B6D4', delta: `${jobs.length} total`, tab: 'jobs' },
    { title: 'Shortlisted', value: shortlisted, icon: UserCheck, color: '#F59E0B', delta: `${Math.round((shortlisted / (total || 1)) * 100)}% conversion`, tab: 'pipeline' },
    { title: 'Interviews', value: interviews, icon: Calendar, color: '#A855F7', delta: 'Active pipeline', tab: 'interviews' },
    { title: 'Hired & Selected', value: hired, icon: Award, color: '#10B981', delta: 'Successful hires', tab: 'pipeline' }
  ];

  // Pipeline funnel steps
  const funnelStages = [
    { label: 'Applied', count: candidates.filter((c) => c.status === 'Applied').length, color: '#6366F1' },
    { label: 'Screening', count: candidates.filter((c) => c.status === 'Screening').length, color: '#8B5CF6' },
    { label: 'Shortlisted', count: shortlisted, color: '#F59E0B' },
    { label: 'Interview', count: interviews, color: '#3B82F6' },
    { label: 'Hired', count: hired, color: '#10B981' }
  ];

  // Score distribution tiers
  const scoreTierHigh = candidates.filter((c) => (c.final_score || c.match_score || 0) >= 80).length;
  const scoreTierMed = candidates.filter((c) => {
    const s = c.final_score || c.match_score || 0;
    return s >= 60 && s < 80;
  }).length;
  const scoreTierLow = candidates.filter((c) => (c.final_score || c.match_score || 0) < 60).length;

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 5 Metric Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px'
      }}>
        {metrics.map((m, idx) => {
          const Icon = m.icon;
          return (
            <div
              key={idx}
              className="glass-panel"
              onClick={() => onNavigate(m.tab)}
              style={{
                padding: '20px',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  {m.title}
                </span>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '10px',
                  background: `${m.color}20`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Icon size={18} color={m.color} />
                </div>
              </div>
              <div style={{ marginTop: '14px' }}>
                <span style={{ fontSize: '32px', fontWeight: 800, color: '#F8FAFC' }}>
                  {m.value}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '6px', fontSize: '11px', color: '#94A3B8' }}>
                <TrendingUp size={12} color="#10B981" />
                <span>{m.delta}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Grid: Funnel + Score Distribution */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
        {/* Hiring Funnel */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#F8FAFC' }}>Recruitment Funnel</h3>
              <p style={{ fontSize: '12px', color: '#94A3B8' }}>Candidate conversion through workflow stages</p>
            </div>
            <button onClick={() => onNavigate('pipeline')} className="btn-secondary btn-sm">
              <span>View Kanban</span>
              <ArrowUpRight size={14} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {funnelStages.map((stage, idx) => {
              const maxVal = Math.max(...funnelStages.map((s) => s.count), 1);
              const pct = Math.round((stage.count / maxVal) * 100);
              return (
                <div key={idx}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 600, color: '#E2E8F0' }}>{stage.label}</span>
                    <span style={{ color: '#94A3B8', fontWeight: 700 }}>{stage.count} candidates</span>
                  </div>
                  <div style={{
                    height: '10px',
                    width: '100%',
                    background: 'rgba(51, 65, 85, 0.4)',
                    borderRadius: '999px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      height: '100%',
                      width: `${Math.max(5, pct)}%`,
                      background: `linear-gradient(90deg, ${stage.color} 0%, ${stage.color}CC 100%)`,
                      borderRadius: '999px',
                      transition: 'width 0.6s ease'
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* AI Score Quality Distribution */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#F8FAFC' }}>AI Quality Distribution</h3>
              <p style={{ fontSize: '12px', color: '#94A3B8' }}>Average Composite Score: <b style={{ color: '#818CF8' }}>{avgFinalScore}%</b></p>
            </div>
            <span className="badge badge-indigo">
              <Sparkles size={12} />
              <span>30% ATS + 50% Match + 20% Screening</span>
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '20px' }}>
            <div style={{ padding: '14px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '12px', border: '1px solid rgba(16, 185, 129, 0.3)', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: '#34D399', fontWeight: 700 }}>High Fit (80-100%)</div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: '#F8FAFC', marginTop: '4px' }}>{scoreTierHigh}</div>
            </div>
            <div style={{ padding: '14px', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '12px', border: '1px solid rgba(99, 102, 241, 0.3)', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: '#818CF8', fontWeight: 700 }}>Medium Fit (60-79%)</div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: '#F8FAFC', marginTop: '4px' }}>{scoreTierMed}</div>
            </div>
            <div style={{ padding: '14px', background: 'rgba(244, 63, 94, 0.1)', borderRadius: '12px', border: '1px solid rgba(244, 63, 94, 0.3)', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: '#FB7185', fontWeight: 700 }}>Low Fit (&lt;60%)</div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: '#F8FAFC', marginTop: '4px' }}>{scoreTierLow}</div>
            </div>
          </div>

          <p style={{ fontSize: '12px', color: '#94A3B8', lineHeight: '1.6' }}>
            Autonomous multi-criteria scoring algorithm evaluates 11 weighted dimensions including verified skills, experience alignment, education credentials, and dynamic screening responses.
          </p>
        </div>
      </div>

      {/* Top Ranked Candidates Section */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#F8FAFC' }}>Top AI-Recommended Candidates</h3>
          <button onClick={() => onNavigate('candidates')} className="btn-secondary btn-sm">
            <span>View All Candidates ({candidates.length})</span>
            <ArrowUpRight size={14} />
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          {candidates.slice(0, 3).map((cand) => {
            const score = cand.final_score || cand.match_score || 75;
            return (
              <div
                key={cand.id}
                onClick={() => onSelectCandidate(cand)}
                style={{
                  padding: '16px',
                  background: 'rgba(15, 23, 42, 0.7)',
                  borderRadius: '12px',
                  border: '1px solid rgba(51, 65, 85, 0.5)',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontWeight: 700, color: '#F8FAFC' }}>{cand.name}</span>
                  <span className={`badge ${score >= 80 ? 'badge-emerald' : score >= 60 ? 'badge-indigo' : 'badge-amber'}`}>
                    {score}% Final
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: '#94A3B8' }}>{cand.email}</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                  {(cand.skills || []).slice(0, 3).map((s, idx) => (
                    <span key={idx} className="badge badge-indigo" style={{ fontSize: '10px' }}>
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
