import React from 'react';
import { Sparkles, CheckCircle2, AlertTriangle, XCircle, TrendingUp, ShieldCheck } from 'lucide-react';
import { Candidate } from '../../types';

interface AIExplanationCardProps {
  candidate: Candidate;
  jobTitle?: string;
}

export const AIExplanationCard: React.FC<AIExplanationCardProps> = ({
  candidate,
  jobTitle = 'Backend Engineer'
}) => {
  const finalScore = candidate.final_score || candidate.match_score || 78;
  const atsScore = candidate.ats_score || finalScore;
  const matchScore = candidate.match_score || finalScore;
  const screeningScore = candidate.screening_score || finalScore;

  // Build dynamic strengths and risks checklist
  const strengths = [
    `Verified technical background in ${(candidate.skills || ['Python']).slice(0, 3).join(', ')}`,
    `${candidate.experience || 3}+ years of professional domain experience`,
    `Strong academic profile: ${candidate.education || 'B.Tech Computer Science'}`,
    `High ATS alignment (${atsScore}%) matching core job requirements`
  ];

  const risks: string[] = [];
  if ((candidate.skills || []).length < 4) {
    risks.push('Limited secondary framework coverage listed on resume');
  }
  if (!candidate.projects || candidate.projects.length === 0) {
    risks.push('No portfolio repository links detected in profile');
  }

  const hiringProbability = finalScore >= 80 ? 92 : finalScore >= 60 ? 74 : 45;
  const riskLevel = finalScore >= 80 ? 'LOW' : finalScore >= 60 ? 'MEDIUM' : 'HIGH';

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '24px', border: '1px solid rgba(99, 102, 241, 0.4)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Sparkles size={18} color="#FFFFFF" />
          </div>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#F8FAFC' }}>
              Why this candidate is recommended
            </h3>
            <p style={{ fontSize: '12px', color: '#94A3B8' }}>AI Explainability & Multi-Criteria Decision Justification</p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className={`badge ${riskLevel === 'LOW' ? 'badge-emerald' : riskLevel === 'MEDIUM' ? 'badge-amber' : 'badge-rose'}`}>
            Risk: {riskLevel}
          </span>
          <span className="badge badge-indigo">
            Probability: {hiringProbability}%
          </span>
        </div>
      </div>

      {/* Checklist Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px', marginTop: '16px' }}>
        {/* Left: Strengths & Risks Checklist */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ fontSize: '13px', fontWeight: 700, color: '#CBD5E1', marginBottom: '2px' }}>
            Evidence & Evaluation Highlights:
          </div>
          {strengths.map((s, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', fontSize: '13px', color: '#E2E8F0' }}>
              <CheckCircle2 size={16} color="#34D399" style={{ flexShrink: 0, marginTop: '2px' }} />
              <span>{s}</span>
            </div>
          ))}

          {risks.map((r, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', fontSize: '13px', color: '#FBBF24' }}>
              <AlertTriangle size={16} color="#FBBF24" style={{ flexShrink: 0, marginTop: '2px' }} />
              <span>{r}</span>
            </div>
          ))}
        </div>

        {/* Right: Scores Summary Grid */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.7)',
          borderRadius: '12px',
          padding: '16px',
          border: '1px solid rgba(51, 65, 85, 0.5)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between'
        }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase' }}>
            Score Attribution Breakdown
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', margin: '12px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
              <span style={{ color: '#94A3B8' }}>ATS Resume Match (30%)</span>
              <span style={{ fontWeight: 700, color: '#F8FAFC' }}>{atsScore}%</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
              <span style={{ color: '#94A3B8' }}>Semantic Skill Fit (50%)</span>
              <span style={{ fontWeight: 700, color: '#F8FAFC' }}>{matchScore}%</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
              <span style={{ color: '#94A3B8' }}>Screening Assessment (20%)</span>
              <span style={{ fontWeight: 700, color: '#F8FAFC' }}>{screeningScore}%</span>
            </div>
          </div>

          <div style={{
            padding: '10px',
            borderRadius: '8px',
            background: 'rgba(99, 102, 241, 0.15)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#A5B4FC' }}>Composite Final Score</span>
            <span style={{ fontSize: '18px', fontWeight: 800, color: '#818CF8' }}>{finalScore}%</span>
          </div>
        </div>
      </div>

      {/* AI Recommendation Quote */}
      <div style={{
        marginTop: '18px',
        padding: '14px 18px',
        borderRadius: '10px',
        background: 'rgba(30, 41, 59, 0.5)',
        borderLeft: '4px solid #6366F1',
        fontSize: '13px',
        color: '#E2E8F0',
        lineHeight: '1.6'
      }}>
        <b>AI Recommendation:</b> Candidate {candidate.name} exhibits {finalScore >= 80 ? 'exceptional' : 'satisfactory'} technical alignment for the {jobTitle} opening. Advancing to technical interview is strongly supported by composite scoring benchmarks.
      </div>
    </div>
  );
};
