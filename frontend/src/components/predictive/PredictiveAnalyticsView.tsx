import React, { useState } from 'react';
import { TrendingUp, ShieldCheck, CheckCircle2, AlertTriangle, Sparkles, BarChart2 } from 'lucide-react';
import { Candidate, Job } from '../../types';

interface PredictiveAnalyticsViewProps {
  candidates: Candidate[];
  jobs: Job[];
}

export const PredictiveAnalyticsView: React.FC<PredictiveAnalyticsViewProps> = ({
  candidates,
  jobs
}) => {
  const [selectedCandId, setSelectedCandId] = useState<number>(candidates[0]?.id || 1);
  const cand = candidates.find((c) => c.id === selectedCandId) || candidates[0];

  const finalScore = cand?.final_score || cand?.match_score || 82;
  const atsScore = cand?.ats_score || Math.min(95, Math.round(finalScore * 0.96));
  const matchScore = cand?.match_score || Math.min(98, Math.round(finalScore * 1.02));
  const screeningScore = cand?.screening_score || Math.min(90, Math.round(finalScore * 0.92));

  const hiringProbability = Math.min(98, Math.max(30, Math.round(finalScore * 0.98 + 4)));
  const probabilityCategory = hiringProbability >= 80 ? 'HIGH PROBABILITY' : hiringProbability >= 60 ? 'MEDIUM PROBABILITY' : 'LOW PROBABILITY';
  const riskLevel = hiringProbability >= 80 ? 'LOW' : hiringProbability >= 60 ? 'MEDIUM' : 'HIGH';

  const skillCoverage = (cand?.skills || []).length >= 4 ? 100 : 75;
  const expFit = (cand?.experience || 3) >= 3 ? 100 : 80;

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '900px', margin: '0 auto' }}>
      {/* Selector Header */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#F8FAFC' }}>Predictive Talent Analytics</h2>
          <p style={{ fontSize: '12px', color: '#94A3B8' }}>AI-driven hiring success probability, attrition risk forecasting, and evidence synthesis</p>
        </div>

        <div style={{ width: '280px' }}>
          <select
            value={selectedCandId}
            onChange={(e) => setSelectedCandId(Number(e.target.value))}
            style={{ background: '#0F172A', height: '40px' }}
          >
            {candidates.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.final_score || c.match_score || 70}% Final)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Prediction Display Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '20px' }}>
        {/* Left: Probability Metric Box */}
        <div className="glass-panel" style={{
          padding: '30px',
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%)',
          border: '1px solid rgba(99, 102, 241, 0.4)'
        }}>
          <div style={{ fontSize: '13px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Hiring Success Probability
          </div>

          <div style={{
            fontSize: '64px',
            fontWeight: 900,
            color: hiringProbability >= 80 ? '#34D399' : hiringProbability >= 60 ? '#818CF8' : '#FB7185',
            fontFamily: 'var(--font-heading)',
            margin: '12px 0 4px 0'
          }}>
            {hiringProbability}%
          </div>

          <span className={`badge ${hiringProbability >= 80 ? 'badge-emerald' : hiringProbability >= 60 ? 'badge-indigo' : 'badge-amber'}`} style={{ padding: '6px 16px', fontSize: '13px' }}>
            {probabilityCategory}
          </span>

          <div style={{
            marginTop: '20px',
            padding: '12px 20px',
            background: 'rgba(15, 23, 42, 0.8)',
            borderRadius: '12px',
            border: '1px solid rgba(51, 65, 85, 0.6)',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            width: '100%',
            justifyContent: 'center'
          }}>
            <ShieldCheck size={18} color={riskLevel === 'LOW' ? '#34D399' : '#FBBF24'} />
            <span style={{ fontSize: '13px', color: '#94A3B8' }}>Overall Risk Level:</span>
            <span style={{
              fontWeight: 800,
              fontSize: '13px',
              color: riskLevel === 'LOW' ? '#34D399' : riskLevel === 'MEDIUM' ? '#FBBF24' : '#F87171'
            }}>
              {riskLevel} RISK
            </span>
          </div>
        </div>

        {/* Right: Multi-Factor Evidence Breakdown */}
        <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#F8FAFC', marginBottom: '4px' }}>
              Predictive Evidence Breakdown
            </h3>
            <p style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '16px' }}>Multi-criteria weighted evaluation factors</p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[
              { label: 'ATS Resume Match', value: atsScore, color: '#6366F1' },
              { label: 'Semantic Skills Alignment', value: matchScore, color: '#8B5CF6' },
              { label: 'Screening Response Quality', value: screeningScore, color: '#3B82F6' },
              { label: 'Core Skill Coverage', value: skillCoverage, color: '#10B981' },
              { label: 'Experience Fit Ratio', value: expFit, color: '#06B6D4' }
            ].map((factor, idx) => (
              <div key={idx}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                  <span style={{ color: '#CBD5E1', fontWeight: 600 }}>{factor.label}</span>
                  <span style={{ color: '#F8FAFC', fontWeight: 700 }}>{factor.value}%</span>
                </div>
                <div style={{ height: '6px', background: 'rgba(51, 65, 85, 0.4)', borderRadius: '999px', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    width: `${factor.value}%`,
                    background: factor.color,
                    borderRadius: '999px'
                  }} />
                </div>
              </div>
            ))}
          </div>

          <div style={{
            marginTop: '16px',
            padding: '12px',
            background: 'rgba(99, 102, 241, 0.1)',
            borderRadius: '8px',
            fontSize: '12px',
            color: '#A5B4FC',
            lineHeight: '1.5'
          }}>
            <b>Prediction Driver:</b> High likelihood of role longevity and technical performance due to verified experience in {(cand?.skills || ['Python']).slice(0, 2).join(' & ')}.
          </div>
        </div>
      </div>

      {/* Identified Strengths & Hiring Risks */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <CheckCircle2 size={18} color="#34D399" />
            <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#F8FAFC' }}>Key Positive Drivers</h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px', color: '#E2E8F0' }}>
            <div>✓ Strong background in {(cand?.skills || []).slice(0, 3).join(', ')}</div>
            <div>✓ {cand?.experience || 3}+ years relevant production experience</div>
            <div>✓ Competitive final composite score of {finalScore}%</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <AlertTriangle size={18} color="#FBBF24" />
            <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#F8FAFC' }}>Potential Hiring Risks & Gaps</h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px', color: '#CBD5E1' }}>
            <div>⚠ Inquire regarding notice period and availability during interview</div>
            <div>⚠ Verify architectural scaling experience during technical round</div>
          </div>
        </div>
      </div>
    </div>
  );
};
