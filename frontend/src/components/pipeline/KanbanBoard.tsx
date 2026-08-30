import React from 'react';
import { Candidate, CandidateStatus } from '../../types';
import { Sparkles, ArrowRight, ArrowLeft, Eye, CheckCircle2 } from 'lucide-react';

interface KanbanBoardProps {
  candidates: Candidate[];
  onSelectCandidate: (candidate: Candidate) => void;
  onUpdateStatus: (candidateId: number, newStatus: CandidateStatus) => void;
}

export const KanbanBoard: React.FC<KanbanBoardProps> = ({
  candidates,
  onSelectCandidate,
  onUpdateStatus
}) => {
  const columns: { status: CandidateStatus; label: string; color: string }[] = [
    { status: 'Applied', label: 'Applied', color: '#6366F1' },
    { status: 'Screening', label: 'Screening', color: '#8B5CF6' },
    { status: 'Shortlisted', label: 'Shortlisted', color: '#F59E0B' },
    { status: 'Interview', label: 'Interview', color: '#3B82F6' },
    { status: 'Hired', label: 'Hired', color: '#10B981' }
  ];

  const getNextStatus = (current: CandidateStatus): CandidateStatus | null => {
    switch (current) {
      case 'Applied': return 'Screening';
      case 'Screening': return 'Shortlisted';
      case 'Shortlisted': return 'Interview';
      case 'Interview': return 'Hired';
      default: return null;
    }
  };

  const getPrevStatus = (current: CandidateStatus): CandidateStatus | null => {
    switch (current) {
      case 'Screening': return 'Applied';
      case 'Shortlisted': return 'Screening';
      case 'Interview': return 'Shortlisted';
      case 'Hired': return 'Interview';
      default: return null;
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#F8FAFC' }}>Candidate Pipeline Stages</h2>
          <p style={{ fontSize: '12px', color: '#94A3B8' }}>Interactive Kanban workflow with real-time status progression</p>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(5, minmax(240px, 1fr))',
        gap: '16px',
        overflowX: 'auto',
        paddingBottom: '16px'
      }}>
        {columns.map((col) => {
          const colCandidates = candidates.filter((c) => {
            if (col.status === 'Interview') {
              return c.status === 'Interview' || c.status === 'Interview Scheduled';
            }
            if (col.status === 'Hired') {
              return c.status === 'Hired' || c.status === 'Selected';
            }
            return c.status === col.status;
          });

          return (
            <div
              key={col.status}
              style={{
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid rgba(51, 65, 85, 0.4)',
                borderRadius: '14px',
                display: 'flex',
                flexDirection: 'column',
                height: 'calc(100vh - 210px)',
                minWidth: '240px'
              }}
            >
              {/* Column Header */}
              <div style={{
                padding: '16px',
                borderBottom: '1px solid rgba(51, 65, 85, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: col.color }} />
                  <span style={{ fontWeight: 700, fontSize: '14px', color: '#F8FAFC' }}>{col.label}</span>
                </div>
                <span className="badge badge-indigo" style={{ fontSize: '11px' }}>
                  {colCandidates.length}
                </span>
              </div>

              {/* Cards Container */}
              <div style={{ flex: 1, padding: '12px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {colCandidates.length === 0 ? (
                  <div style={{
                    padding: '30px 10px',
                    textAlign: 'center',
                    color: '#64748B',
                    fontSize: '12px',
                    border: '1px dashed rgba(51, 65, 85, 0.4)',
                    borderRadius: '10px'
                  }}>
                    No candidates in {col.label}
                  </div>
                ) : (
                  colCandidates.map((cand) => {
                    const score = cand.final_score || cand.match_score || 70;
                    const nextSt = getNextStatus(col.status);
                    const prevSt = getPrevStatus(col.status);

                    return (
                      <div
                        key={cand.id}
                        style={{
                          background: '#1E293B',
                          border: '1px solid rgba(51, 65, 85, 0.6)',
                          borderRadius: '12px',
                          padding: '14px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '8px',
                          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                          transition: 'transform 0.15s ease, border-color 0.15s ease'
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <div>
                            <div style={{ fontWeight: 700, fontSize: '14px', color: '#F8FAFC' }}>{cand.name}</div>
                            <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '2px' }}>{cand.email}</div>
                          </div>
                          <span className={`badge ${score >= 80 ? 'badge-emerald' : score >= 60 ? 'badge-indigo' : 'badge-amber'}`}>
                            {score}%
                          </span>
                        </div>

                        {/* Skills */}
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', margin: '4px 0' }}>
                          {(cand.skills || []).slice(0, 2).map((s, idx) => (
                            <span key={idx} style={{
                              fontSize: '10px',
                              background: 'rgba(51, 65, 85, 0.5)',
                              color: '#CBD5E1',
                              padding: '2px 6px',
                              borderRadius: '4px'
                            }}>
                              {s}
                            </span>
                          ))}
                        </div>

                        {/* Action buttons */}
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '6px', paddingTop: '8px', borderTop: '1px solid rgba(51, 65, 85, 0.4)' }}>
                          <button
                            onClick={() => onSelectCandidate(cand)}
                            style={{
                              background: 'none',
                              border: 'none',
                              color: '#818CF8',
                              fontSize: '12px',
                              fontWeight: 600,
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px'
                            }}
                          >
                            <Eye size={13} />
                            <span>Details</span>
                          </button>

                          <div style={{ display: 'flex', gap: '4px' }}>
                            {prevSt && (
                              <button
                                title={`Move back to ${prevSt}`}
                                onClick={() => onUpdateStatus(cand.id, prevSt)}
                                style={{
                                  background: 'rgba(30, 41, 59, 0.9)',
                                  border: '1px solid #475569',
                                  color: '#94A3B8',
                                  padding: '4px 6px',
                                  borderRadius: '6px',
                                  cursor: 'pointer'
                                }}
                              >
                                <ArrowLeft size={12} />
                              </button>
                            )}
                            {nextSt && (
                              <button
                                title={`Advance to ${nextSt}`}
                                onClick={() => onUpdateStatus(cand.id, nextSt)}
                                style={{
                                  background: 'rgba(99, 102, 241, 0.2)',
                                  border: '1px solid #6366F1',
                                  color: '#818CF8',
                                  padding: '4px 8px',
                                  borderRadius: '6px',
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '2px',
                                  fontSize: '11px',
                                  fontWeight: 700
                                }}
                              >
                                <span>{nextSt}</span>
                                <ArrowRight size={12} />
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
