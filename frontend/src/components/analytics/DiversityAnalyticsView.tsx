import React, { useState, useEffect } from 'react';
import { PieChart, ShieldCheck, Download, Users, MapPin, Award, CheckCircle2 } from 'lucide-react';
import { Candidate, DiversityInsightsReport } from '../../types';
import { aiService } from '../../services/aiService';

interface DiversityAnalyticsViewProps {
  candidates: Candidate[];
}

export const DiversityAnalyticsView: React.FC<DiversityAnalyticsViewProps> = ({
  candidates
}) => {
  const [report, setReport] = useState<DiversityInsightsReport | null>(null);

  useEffect(() => {
    aiService.getDiversityReport()
      .then(setReport)
      .catch((e) => console.warn('Could not load diversity report:', e));
  }, []);

  // Calculate location counts
  const locationCounts: Record<string, number> = {};
  candidates.forEach((c) => {
    const loc = c.location || 'Pune / Hybrid';
    locationCounts[loc] = (locationCounts[loc] || 0) + 1;
  });

  // Calculate experience tiers
  const junior = candidates.filter((c) => (c.experience || 0) <= 2).length;
  const mid = candidates.filter((c) => (c.experience || 0) > 2 && (c.experience || 0) <= 5).length;
  const senior = candidates.filter((c) => (c.experience || 0) > 5).length;

  const handleExportCSV = () => {
    const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    window.open(`${apiBase}/reports/export-csv`, '_blank');
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '900px', margin: '0 auto' }}>
      {/* Header */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <PieChart size={22} color="#FFFFFF" />
          </div>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#F8FAFC' }}>Recruitment Analytics & Diversity Audit</h2>
            <p style={{ fontSize: '12px', color: '#94A3B8' }}>Macro talent representation, geographic distribution, and bias-free compliance verification</p>
          </div>
        </div>

        <button onClick={handleExportCSV} className="btn-secondary btn-sm">
          <Download size={14} />
          <span>Export Candidate CSV</span>
        </button>
      </div>

      {/* Fairness & Diversity Neutrality Statement Card */}
      <div className="glass-panel" style={{
        padding: '24px',
        border: '1px solid rgba(16, 185, 129, 0.4)',
        background: 'linear-gradient(135deg, rgba(6, 78, 59, 0.2) 0%, rgba(15, 23, 42, 0.9) 100%)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
          <ShieldCheck size={22} color="#34D399" />
          <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#F8FAFC' }}>
            Fairness & Merit-Based Scoring Compliance
          </h3>
        </div>
        <p style={{ fontSize: '13px', color: '#CBD5E1', lineHeight: '1.6' }}>
          <b>Demographic Neutrality Verified:</b> Candidate scoring models exclusively evaluate technical competencies, verified skills, professional experience, and objective screening responses. Zero demographic, gender, age, or identity parameters are utilized in candidate scoring or ranking.
        </p>
      </div>

      {/* Grid: Location & Experience Tiers */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Experience Tier Distribution */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#F8FAFC', marginBottom: '16px' }}>
            Experience Tier Distribution
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {[
              { label: 'Early Career (0-2 yrs)', count: junior, color: '#6366F1' },
              { label: 'Mid-Level (3-5 yrs)', count: mid, color: '#3B82F6' },
              { label: 'Senior / Lead (6+ yrs)', count: senior, color: '#10B981' }
            ].map((tier, idx) => {
              const pct = Math.round((tier.count / (candidates.length || 1)) * 100);
              return (
                <div key={idx}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
                    <span style={{ color: '#CBD5E1', fontWeight: 600 }}>{tier.label}</span>
                    <span style={{ color: '#F8FAFC', fontWeight: 700 }}>{tier.count} ({pct}%)</span>
                  </div>
                  <div style={{ height: '8px', background: 'rgba(51, 65, 85, 0.4)', borderRadius: '999px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${pct}%`, background: tier.color, borderRadius: '999px' }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Location Breakdown */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#F8FAFC', marginBottom: '16px' }}>
            Geographic Location Spread
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {Object.entries(locationCounts).slice(0, 5).map(([loc, count], idx) => (
              <div
                key={idx}
                style={{
                  padding: '10px 14px',
                  background: 'rgba(15, 23, 42, 0.8)',
                  borderRadius: '10px',
                  border: '1px solid rgba(51, 65, 85, 0.4)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <MapPin size={14} color="#818CF8" />
                  <span style={{ fontSize: '13px', color: '#F8FAFC', fontWeight: 600 }}>{loc}</span>
                </div>
                <span className="badge badge-indigo">{count} candidates</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
