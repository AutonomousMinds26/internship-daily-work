import React, { useState, useMemo } from 'react';
import { Candidate, CandidateStatus } from '../../types';
import { Search, Filter, ArrowUpDown, Eye, Calendar, Award, ChevronLeft, ChevronRight } from 'lucide-react';

interface CandidateListViewProps {
  candidates: Candidate[];
  onSelectCandidate: (candidate: Candidate) => void;
  onScheduleInterview: (candidate: Candidate) => void;
  onUpdateStatus: (candidateId: number, status: CandidateStatus) => void;
}

export const CandidateListView: React.FC<CandidateListViewProps> = ({
  candidates,
  onSelectCandidate,
  onScheduleInterview,
  onUpdateStatus
}) => {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [scoreFilter, setScoreFilter] = useState('ALL');
  const [sortBy, setSortBy] = useState<'score' | 'name' | 'experience'>('score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 8;

  const filteredCandidates = useMemo(() => {
    return candidates.filter((c) => {
      const matchSearch =
        c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.email.toLowerCase().includes(search.toLowerCase()) ||
        (c.skills || []).some((s) => s.toLowerCase().includes(search.toLowerCase()));

      const matchStatus = statusFilter === 'ALL' || c.status === statusFilter;

      const score = c.final_score || c.match_score || 50;
      let matchScore = true;
      if (scoreFilter === 'HIGH') matchScore = score >= 80;
      else if (scoreFilter === 'MEDIUM') matchScore = score >= 60 && score < 80;
      else if (scoreFilter === 'LOW') matchScore = score < 60;

      return matchSearch && matchStatus && matchScore;
    }).sort((a, b) => {
      let valA: any = a.final_score || a.match_score || 0;
      let valB: any = b.final_score || b.match_score || 0;

      if (sortBy === 'name') {
        valA = a.name.toLowerCase();
        valB = b.name.toLowerCase();
      } else if (sortBy === 'experience') {
        valA = a.experience || 0;
        valB = b.experience || 0;
      }

      if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
      if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
  }, [candidates, search, statusFilter, scoreFilter, sortBy, sortOrder]);

  const totalPages = Math.ceil(filteredCandidates.length / pageSize) || 1;
  const paginatedCandidates = filteredCandidates.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Search & Filter Header Bar */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexWrap: 'wrap', gap: '14px', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', flex: 1, minWidth: '320px' }}>
          <div style={{ position: 'relative', width: '260px' }}>
            <Search size={16} color="#94A3B8" style={{ position: 'absolute', left: '12px', top: '12px' }} />
            <input
              type="text"
              placeholder="Search by name, email, skill..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setCurrentPage(1); }}
              style={{ paddingLeft: '36px', height: '40px' }}
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1); }}
            style={{ width: '160px', height: '40px' }}
          >
            <option value="ALL">All Statuses</option>
            <option value="Applied">Applied</option>
            <option value="Screening">Screening</option>
            <option value="Shortlisted">Shortlisted</option>
            <option value="Interview">Interview</option>
            <option value="Hired">Hired</option>
            <option value="Rejected">Rejected</option>
          </select>

          <select
            value={scoreFilter}
            onChange={(e) => { setScoreFilter(e.target.value); setCurrentPage(1); }}
            style={{ width: '160px', height: '40px' }}
          >
            <option value="ALL">All Scores</option>
            <option value="HIGH">High Fit (&ge;80%)</option>
            <option value="MEDIUM">Medium Fit (60-79%)</option>
            <option value="LOW">Low Fit (&lt;60%)</option>
          </select>
        </div>

        {/* Sort Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '13px', color: '#94A3B8' }}>Sort by:</span>
          <select
            value={sortBy}
            onChange={(e: any) => setSortBy(e.target.value)}
            style={{ width: '140px', height: '40px' }}
          >
            <option value="score">Final Score</option>
            <option value="name">Candidate Name</option>
            <option value="experience">Years Experience</option>
          </select>
          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="btn-secondary btn-sm"
            style={{ height: '40px', padding: '0 12px' }}
          >
            <ArrowUpDown size={15} />
            <span>{sortOrder.toUpperCase()}</span>
          </button>
        </div>
      </div>

      {/* Candidate Data Table */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: 'rgba(15, 23, 42, 0.8)', borderBottom: '1px solid rgba(51, 65, 85, 0.5)', color: '#94A3B8' }}>
              <th style={{ padding: '14px 20px', fontWeight: 700 }}>Candidate</th>
              <th style={{ padding: '14px 16px', fontWeight: 700 }}>Experience & Edu</th>
              <th style={{ padding: '14px 16px', fontWeight: 700 }}>Skills</th>
              <th style={{ padding: '14px 16px', fontWeight: 700 }}>Scores Breakdown</th>
              <th style={{ padding: '14px 16px', fontWeight: 700 }}>Status</th>
              <th style={{ padding: '14px 20px', fontWeight: 700, textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {paginatedCandidates.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '40px', textAlign: 'center', color: '#64748B' }}>
                  No candidates found matching filter criteria.
                </td>
              </tr>
            ) : (
              paginatedCandidates.map((c) => {
                const finalScore = c.final_score || c.match_score || 70;
                const ats = c.ats_score || finalScore;
                const match = c.match_score || finalScore;

                return (
                  <tr
                    key={c.id}
                    style={{ borderBottom: '1px solid rgba(51, 65, 85, 0.3)', transition: 'background 0.15s ease' }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(30, 41, 59, 0.4)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    <td style={{ padding: '14px 20px' }}>
                      <div style={{ fontWeight: 700, color: '#F8FAFC' }}>{c.name}</div>
                      <div style={{ fontSize: '11px', color: '#94A3B8' }}>{c.email}</div>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ color: '#E2E8F0' }}>{c.experience || 0} years</div>
                      <div style={{ fontSize: '11px', color: '#94A3B8' }}>{c.education || 'N/A'}</div>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', maxWidth: '240px' }}>
                        {(c.skills || []).slice(0, 3).map((s, idx) => (
                          <span key={idx} className="badge badge-indigo" style={{ fontSize: '10px' }}>
                            {s}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span className={`badge ${finalScore >= 80 ? 'badge-emerald' : finalScore >= 60 ? 'badge-indigo' : 'badge-amber'}`}>
                          {finalScore}% Final
                        </span>
                      </div>
                      <div style={{ fontSize: '10px', color: '#94A3B8', marginTop: '2px' }}>
                        ATS: {ats}% | Match: {match}%
                      </div>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <select
                        value={c.status}
                        onChange={(e) => onUpdateStatus(c.id, e.target.value as CandidateStatus)}
                        style={{ padding: '4px 8px', fontSize: '11px', width: 'auto', background: '#1E293B' }}
                      >
                        <option value="Applied">Applied</option>
                        <option value="Screening">Screening</option>
                        <option value="Shortlisted">Shortlisted</option>
                        <option value="Interview">Interview</option>
                        <option value="Hired">Hired</option>
                        <option value="Rejected">Rejected</option>
                      </select>
                    </td>
                    <td style={{ padding: '14px 20px', textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '6px' }}>
                        <button
                          onClick={() => onSelectCandidate(c)}
                          className="btn-secondary btn-sm"
                          style={{ padding: '6px 10px' }}
                          title="View Profile & AI Analysis"
                        >
                          <Eye size={14} />
                        </button>
                        <button
                          onClick={() => onScheduleInterview(c)}
                          className="btn-primary btn-sm"
                          style={{ padding: '6px 10px' }}
                          title="Schedule Interview"
                        >
                          <Calendar size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>

        {/* Pagination Footer */}
        <div style={{
          padding: '16px 20px',
          background: 'rgba(15, 23, 42, 0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderTop: '1px solid rgba(51, 65, 85, 0.4)'
        }}>
          <span style={{ fontSize: '12px', color: '#94A3B8' }}>
            Showing {Math.min((currentPage - 1) * pageSize + 1, filteredCandidates.length)} to {Math.min(currentPage * pageSize, filteredCandidates.length)} of {filteredCandidates.length} candidates
          </span>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => p - 1)}
              className="btn-secondary btn-sm"
              style={{ opacity: currentPage === 1 ? 0.5 : 1 }}
            >
              <ChevronLeft size={14} />
              <span>Previous</span>
            </button>
            <span style={{ padding: '6px 12px', fontSize: '12px', color: '#F8FAFC', fontWeight: 700 }}>
              {currentPage} / {totalPages}
            </span>
            <button
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage((p) => p + 1)}
              className="btn-secondary btn-sm"
              style={{ opacity: currentPage === totalPages ? 0.5 : 1 }}
            >
              <span>Next</span>
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
