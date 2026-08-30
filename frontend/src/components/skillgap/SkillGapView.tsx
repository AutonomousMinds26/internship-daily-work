import React, { useState } from 'react';
import { GraduationCap, CheckCircle2, AlertTriangle, BookOpen, Sparkles, ExternalLink } from 'lucide-react';
import { Candidate, Job } from '../../types';

interface SkillGapViewProps {
  candidates: Candidate[];
  jobs: Job[];
}

export const SkillGapView: React.FC<SkillGapViewProps> = ({
  candidates,
  jobs
}) => {
  const [selectedCandId, setSelectedCandId] = useState<number>(candidates[0]?.id || 1);
  const [selectedJobId, setSelectedJobId] = useState<number>(jobs[0]?.id || 1);

  const cand = candidates.find((c) => c.id === selectedCandId) || candidates[0];
  const job = jobs.find((j) => j.id === selectedJobId) || jobs[0];

  const candSkills = (cand?.skills || []).map((s) => s.toLowerCase());
  const jobSkills = (job?.requirements || ['Python', 'FastAPI', 'Docker', 'AWS', 'PostgreSQL']);

  const matched = jobSkills.filter((s) => candSkills.includes(s.toLowerCase()));
  const missing = jobSkills.filter((s) => !candSkills.includes(s.toLowerCase()));

  const courses = [
    { title: 'Cloud Native Microservices with Docker & Kubernetes', platform: 'Coursera / AWS', duration: '4 weeks', skill: missing[0] || 'Docker' },
    { title: 'Advanced Cloud Architecture on AWS', platform: 'AWS SkillBuilder', duration: '6 weeks', skill: missing[1] || 'AWS' },
    { title: 'High-Performance PostgreSQL & Query Tuning', platform: 'Udemy', duration: '3 weeks', skill: 'PostgreSQL' }
  ];

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '900px', margin: '0 auto' }}>
      {/* Selector Header */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexWrap: 'wrap', gap: '16px', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#F8FAFC' }}>Skill-Gap & Upskilling Roadmap</h2>
          <p style={{ fontSize: '12px', color: '#94A3B8' }}>Compare candidate skills against target job requirements and formulate onboarding training</p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <select
            value={selectedCandId}
            onChange={(e) => setSelectedCandId(Number(e.target.value))}
            style={{ width: '200px', background: '#0F172A', height: '40px' }}
          >
            {candidates.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>

          <select
            value={selectedJobId}
            onChange={(e) => setSelectedJobId(Number(e.target.value))}
            style={{ width: '200px', background: '#0F172A', height: '40px' }}
          >
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>{j.title}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Side-by-Side Skills Comparison */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Matched Skills */}
        <div className="glass-panel" style={{ padding: '24px', border: '1px solid rgba(16, 185, 129, 0.4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <CheckCircle2 size={20} color="#34D399" />
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#F8FAFC' }}>
                Matched Skills ({matched.length})
              </h3>
              <p style={{ fontSize: '12px', color: '#94A3B8' }}>Verified proficiencies matching job requirements</p>
            </div>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {matched.length === 0 ? (
              <div style={{ color: '#94A3B8', fontSize: '13px' }}>No direct skill matches found.</div>
            ) : (
              matched.map((s, idx) => (
                <div key={idx} style={{
                  padding: '8px 14px',
                  background: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  borderRadius: '10px',
                  color: '#6EE7B7',
                  fontWeight: 600,
                  fontSize: '13px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <span>✓ {s}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Missing Skills */}
        <div className="glass-panel" style={{ padding: '24px', border: '1px solid rgba(245, 158, 11, 0.4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <AlertTriangle size={20} color="#FBBF24" />
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#F8FAFC' }}>
                Skill Gaps ({missing.length})
              </h3>
              <p style={{ fontSize: '12px', color: '#94A3B8' }}>Target job requirements missing on resume</p>
            </div>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {missing.length === 0 ? (
              <div style={{ color: '#34D399', fontSize: '13px', fontWeight: 600 }}>
                ✓ 100% Full Skill Coverage! Zero identified gaps.
              </div>
            ) : (
              missing.map((s, idx) => (
                <div key={idx} style={{
                  padding: '8px 14px',
                  background: 'rgba(245, 158, 11, 0.15)',
                  border: '1px solid rgba(245, 158, 11, 0.4)',
                  borderRadius: '10px',
                  color: '#FCD34D',
                  fontWeight: 600,
                  fontSize: '13px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <span>⚠ {s}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Recommended Upskilling Pathways */}
      <div className="glass-panel" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <BookOpen size={20} color="#818CF8" />
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#F8FAFC' }}>
              Recommended Learning & Upskilling Roadmap
            </h3>
            <p style={{ fontSize: '12px', color: '#94A3B8' }}>Personalized training modules to bridge technical gaps post-hire</p>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {courses.map((c, idx) => (
            <div
              key={idx}
              style={{
                padding: '16px 20px',
                background: 'rgba(15, 23, 42, 0.8)',
                borderRadius: '12px',
                border: '1px solid rgba(51, 65, 85, 0.5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
            >
              <div>
                <div style={{ fontWeight: 700, color: '#F8FAFC', fontSize: '14px' }}>{c.title}</div>
                <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '2px' }}>
                  Platform: {c.platform} • Est. Duration: {c.duration} • Focus Skill: <span style={{ color: '#818CF8' }}>{c.skill}</span>
                </div>
              </div>
              <span className="badge badge-indigo">Recommended</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
