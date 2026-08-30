import React, { useState, useEffect } from 'react';
import {
  X,
  User,
  Mail,
  Phone,
  Briefcase,
  GraduationCap,
  Sparkles,
  FileText,
  Clock,
  MessageSquare,
  CheckCircle2,
  Calendar
} from 'lucide-react';
import { Candidate, CandidateHistoryItem, CandidateStatus } from '../../types';
import { candidateService } from '../../services/candidateService';
import { AIExplanationCard } from './AIExplanationCard';
import { useToast } from '../layout/Toast';

interface CandidateDetailsModalProps {
  candidate: Candidate;
  onClose: () => void;
  onUpdateStatus: (id: number, status: CandidateStatus) => void;
  onScheduleInterview: (candidate: Candidate) => void;
}

export const CandidateDetailsModal: React.FC<CandidateDetailsModalProps> = ({
  candidate,
  onClose,
  onUpdateStatus,
  onScheduleInterview
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'ai' | 'history' | 'resume'>('overview');
  const [history, setHistory] = useState<CandidateHistoryItem[]>([]);
  const [feedback, setFeedback] = useState(candidate.feedback || '');
  const [savingFeedback, setSavingFeedback] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    candidateService.getCandidateHistory(candidate.id)
      .then(setHistory)
      .catch((e) => console.warn('Could not load history:', e));
  }, [candidate.id]);

  const handleSaveFeedback = async () => {
    setSavingFeedback(true);
    try {
      await candidateService.updateFeedback(candidate.id, feedback);
      showToast('Candidate notes & feedback updated successfully!', 'success');
    } catch (e: any) {
      showToast('Failed to save feedback.', 'error');
    } finally {
      setSavingFeedback(false);
    }
  };

  const finalScore = candidate.final_score || candidate.match_score || 75;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '24px'
    }}>
      <div className="glass-panel animate-fade-in" style={{
        width: '100%',
        maxWidth: '900px',
        maxHeight: '90vh',
        background: '#0F172A',
        border: '1px solid rgba(51, 65, 85, 0.7)',
        borderRadius: '20px',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: '0 25px 60px rgba(0,0,0,0.6)'
      }}>
        {/* Header */}
        <div style={{
          padding: '24px 30px',
          borderBottom: '1px solid rgba(51, 65, 85, 0.4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '14px',
              background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: '20px',
              color: '#FFFFFF'
            }}>
              {candidate.name.charAt(0)}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#F8FAFC' }}>{candidate.name}</h2>
                <span className={`badge ${finalScore >= 80 ? 'badge-emerald' : finalScore >= 60 ? 'badge-indigo' : 'badge-amber'}`}>
                  {finalScore}% Final Score
                </span>
              </div>
              <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>
                {candidate.email} {candidate.phone && `• ${candidate.phone}`} • {candidate.location || 'Location Not Specified'}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              onClick={() => onScheduleInterview(candidate)}
              className="btn-primary btn-sm"
            >
              <Calendar size={14} />
              <span>Schedule Interview</span>
            </button>
            <button
              onClick={onClose}
              style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer', padding: '6px' }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div style={{
          display: 'flex',
          gap: '8px',
          padding: '0 30px',
          background: 'rgba(15, 23, 42, 0.9)',
          borderBottom: '1px solid rgba(51, 65, 85, 0.4)'
        }}>
          {[
            { id: 'overview', label: 'Candidate Profile', icon: User },
            { id: 'ai', label: 'AI Score & Explanation', icon: Sparkles },
            { id: 'history', label: 'Journey Audit Trail', icon: Clock },
            { id: 'resume', label: 'Raw Resume', icon: FileText }
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
                  padding: '14px 16px',
                  background: 'none',
                  border: 'none',
                  borderBottom: isActive ? '2px solid #6366F1' : '2px solid transparent',
                  color: isActive ? '#818CF8' : '#94A3B8',
                  fontWeight: isActive ? 700 : 500,
                  fontSize: '13px',
                  cursor: 'pointer'
                }}
              >
                <Icon size={15} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Content Body */}
        <div style={{ flex: 1, padding: '24px 30px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="glass-panel" style={{ padding: '18px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '10px' }}>
                    Professional Background
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px' }}>
                    <div><b style={{ color: '#CBD5E1' }}>Experience:</b> {candidate.experience || 0} years</div>
                    <div><b style={{ color: '#CBD5E1' }}>Education:</b> {candidate.education || 'Not Specified'}</div>
                    <div><b style={{ color: '#CBD5E1' }}>Notice Period:</b> {candidate.notice_period || '30 days'}</div>
                    <div><b style={{ color: '#CBD5E1' }}>Expected CTC:</b> {candidate.expected_ctc || 'Negotiable'}</div>
                  </div>
                </div>

                <div className="glass-panel" style={{ padding: '18px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '10px' }}>
                    Current Pipeline Status
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '6px' }}>
                    <select
                      value={candidate.status}
                      onChange={(e) => onUpdateStatus(candidate.id, e.target.value as CandidateStatus)}
                      style={{ padding: '8px 12px', background: '#1E293B', fontSize: '13px', fontWeight: 600 }}
                    >
                      <option value="Applied">Applied</option>
                      <option value="Screening">Screening</option>
                      <option value="Shortlisted">Shortlisted</option>
                      <option value="Interview">Interview</option>
                      <option value="Hired">Hired</option>
                      <option value="Rejected">Rejected</option>
                    </select>
                  </div>
                  <p style={{ fontSize: '11px', color: '#94A3B8', marginTop: '10px' }}>
                    Status transitions are automatically logged in the audit trail.
                  </p>
                </div>
              </div>

              {/* Verified Skills */}
              <div className="glass-panel" style={{ padding: '18px' }}>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '10px' }}>
                  Extracted Skills & Competencies
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {(candidate.skills || []).map((s, idx) => (
                    <span key={idx} className="badge badge-indigo" style={{ padding: '5px 12px', fontSize: '12px' }}>
                      {s}
                    </span>
                  ))}
                </div>
              </div>

              {/* Interviewer Feedback Notes */}
              <div className="glass-panel" style={{ padding: '18px' }}>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '10px' }}>
                  Interviewer Feedback & Notes
                </div>
                <textarea
                  rows={3}
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="Enter candidate feedback, interview impressions, or hiring manager notes..."
                  style={{ marginBottom: '10px' }}
                />
                <button
                  onClick={handleSaveFeedback}
                  className="btn-secondary btn-sm"
                  disabled={savingFeedback}
                >
                  {savingFeedback ? 'Saving...' : 'Save Feedback'}
                </button>
              </div>
            </div>
          )}

          {/* TAB 2: AI SCORE & EXPLANATION */}
          {activeTab === 'ai' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <AIExplanationCard candidate={candidate} />
            </div>
          )}

          {/* TAB 3: AUDIT HISTORY */}
          {activeTab === 'history' && (
            <div className="glass-panel" style={{ padding: '20px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#F8FAFC', marginBottom: '16px' }}>Candidate Timeline</h3>
              {history.length === 0 ? (
                <div style={{ color: '#94A3B8', fontSize: '13px' }}>No audit history records available.</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {history.map((h) => (
                    <div key={h.id} style={{ display: 'flex', gap: '12px', borderLeft: '2px solid #6366F1', paddingLeft: '14px' }}>
                      <div style={{ fontSize: '12px', color: '#94A3B8', width: '120px', flexShrink: 0 }}>
                        {new Date(h.created_at).toLocaleDateString()} {new Date(h.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '13px', color: '#F8FAFC' }}>{h.action}</div>
                        {h.details && <div style={{ fontSize: '12px', color: '#CBD5E1', marginTop: '2px' }}>{h.details}</div>}
                        {h.performed_by && <div style={{ fontSize: '11px', color: '#818CF8', marginTop: '2px' }}>By: {h.performed_by}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 4: RAW RESUME */}
          {activeTab === 'resume' && (
            <div className="glass-panel" style={{ padding: '20px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#F8FAFC', marginBottom: '12px' }}>Parsed Resume Document</h3>
              <pre style={{
                background: '#0B1120',
                padding: '16px',
                borderRadius: '10px',
                border: '1px solid #334155',
                fontSize: '12px',
                color: '#CBD5E1',
                whiteSpace: 'pre-wrap',
                fontFamily: 'monospace',
                maxHeight: '400px',
                overflowY: 'auto'
              }}>
                {candidate.resume_text || 'No raw resume text available for this candidate profile.'}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
