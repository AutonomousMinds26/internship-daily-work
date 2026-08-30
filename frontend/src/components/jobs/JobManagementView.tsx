import React, { useState } from 'react';
import { Briefcase, Plus, Users, MapPin, DollarSign, Clock, Sparkles, X } from 'lucide-react';
import { Job, Candidate } from '../../types';
import { jobService } from '../../services/jobService';
import { useToast } from '../layout/Toast';

interface JobManagementViewProps {
  jobs: Job[];
  candidates: Candidate[];
  onJobCreated: (newJob: Job) => void;
  onSelectCandidate: (candidate: Candidate) => void;
}

export const JobManagementView: React.FC<JobManagementViewProps> = ({
  jobs,
  candidates,
  onJobCreated,
  onSelectCandidate
}) => {
  const [selectedJob, setSelectedJob] = useState<Job | null>(jobs[0] || null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newSkills, setNewSkills] = useState('Python, FastAPI, PostgreSQL, Docker, AWS');
  const [newExp, setNewExp] = useState(3);
  const [newLoc, setNewLoc] = useState('Pune');
  const [newSalary, setNewSalary] = useState('18-25 LPA');
  const [creating, setCreating] = useState(false);
  const { showToast } = useToast();

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newDesc.trim()) {
      showToast('Please provide job title and description.', 'error');
      return;
    }

    setCreating(true);
    try {
      const skillsArray = newSkills.split(',').map((s) => s.trim()).filter((s) => s.length > 0);
      const created = await jobService.createJob({
        title: newTitle,
        description: newDesc,
        requirements: skillsArray,
        experience_required: newExp,
        location: newLoc,
        salary_range: newSalary
      });

      showToast(`Job '${created.title}' created successfully!`, 'success');
      onJobCreated(created);
      setSelectedJob(created);
      setShowCreateModal(false);
      setNewTitle('');
      setNewDesc('');
    } catch (err: any) {
      showToast('Failed to create job opening.', 'error');
    } finally {
      setCreating(false);
    }
  };

  // Find matching candidates for selected job
  const matchingCandidates = candidates.filter((c) => {
    if (!selectedJob) return false;
    const reqs = selectedJob.requirements || [];
    if (reqs.length === 0) return true;
    const candSkills = (c.skills || []).map((s) => s.toLowerCase());
    return reqs.some((r) => candSkills.includes(r.toLowerCase()));
  }).sort((a, b) => (b.final_score || 0) - (a.final_score || 0));

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#F8FAFC' }}>Active Job Requisitions</h2>
          <p style={{ fontSize: '12px', color: '#94A3B8' }}>Manage open positions and view automated talent matching</p>
        </div>
        <button onClick={() => setShowCreateModal(true)} className="btn-primary">
          <Plus size={16} />
          <span>Create New Job</span>
        </button>
      </div>

      {/* Grid: Job List on Left, Selected Job Details & Ranked Candidates on Right */}
      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '20px' }}>
        {/* Jobs List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {jobs.map((job) => {
            const isSelected = selectedJob?.id === job.id;
            return (
              <div
                key={job.id}
                onClick={() => setSelectedJob(job)}
                className="glass-panel"
                style={{
                  padding: '16px',
                  cursor: 'pointer',
                  borderLeft: isSelected ? '4px solid #6366F1' : '4px solid transparent',
                  background: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'rgba(30, 41, 59, 0.7)'
                }}
              >
                <div style={{ fontWeight: 700, fontSize: '14px', color: '#F8FAFC' }}>{job.title}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '6px', fontSize: '12px', color: '#94A3B8' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <MapPin size={12} />
                    {job.location || 'Pune'}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} />
                    {job.experience_required || 2}+ yrs
                  </span>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '8px' }}>
                  {(job.requirements || ['Python', 'FastAPI']).slice(0, 3).map((r, idx) => (
                    <span key={idx} className="badge badge-indigo" style={{ fontSize: '10px' }}>{r}</span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Selected Job Workspace */}
        {selectedJob && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Job Details Card */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3 style={{ fontSize: '20px', fontWeight: 800, color: '#F8FAFC' }}>{selectedJob.title}</h3>
                  <div style={{ display: 'flex', gap: '16px', marginTop: '6px', fontSize: '13px', color: '#94A3B8' }}>
                    <span>📍 {selectedJob.location || 'Pune'}</span>
                    <span>💼 {selectedJob.experience_required || 3}+ years required</span>
                    <span>💰 {selectedJob.salary_range || 'Competitive'}</span>
                  </div>
                </div>
                <span className="badge badge-emerald">Active Opening</span>
              </div>

              <div style={{ margin: '16px 0', fontSize: '13px', color: '#CBD5E1', lineHeight: '1.6' }}>
                {selectedJob.description}
              </div>

              <div>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '6px' }}>
                  Required Competencies:
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {(selectedJob.requirements || []).map((r, idx) => (
                    <span key={idx} className="badge badge-indigo" style={{ padding: '4px 10px' }}>{r}</span>
                  ))}
                </div>
              </div>
            </div>

            {/* Matched & Ranked Candidates */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h4 style={{ fontSize: '16px', fontWeight: 700, color: '#F8FAFC' }}>
                    Ranked Matching Candidates ({matchingCandidates.length})
                  </h4>
                  <p style={{ fontSize: '12px', color: '#94A3B8' }}>Ranked automatically by composite fit score</p>
                </div>
                <span className="badge badge-indigo">
                  <Sparkles size={12} />
                  <span>AI Matcher v2.0</span>
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {matchingCandidates.slice(0, 6).map((c) => {
                  const finalScore = c.final_score || c.match_score || 70;
                  return (
                    <div
                      key={c.id}
                      onClick={() => onSelectCandidate(c)}
                      style={{
                        padding: '14px 18px',
                        background: 'rgba(15, 23, 42, 0.8)',
                        borderRadius: '12px',
                        border: '1px solid rgba(51, 65, 85, 0.5)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        cursor: 'pointer',
                        transition: 'border-color 0.2s ease'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                        <div style={{
                          width: '38px',
                          height: '38px',
                          borderRadius: '10px',
                          background: 'rgba(99, 102, 241, 0.2)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 700,
                          color: '#818CF8'
                        }}>
                          {c.name.charAt(0)}
                        </div>
                        <div>
                          <div style={{ fontWeight: 700, color: '#F8FAFC', fontSize: '14px' }}>{c.name}</div>
                          <div style={{ fontSize: '12px', color: '#94A3B8' }}>
                            {c.email} • {c.experience || 0} yrs exp
                          </div>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <span className={`badge ${finalScore >= 80 ? 'badge-emerald' : finalScore >= 60 ? 'badge-indigo' : 'badge-amber'}`}>
                          {finalScore}% Match
                        </span>
                        <span className="badge badge-indigo">{c.status}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Create Job Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '20px'
        }}>
          <div className="glass-panel animate-fade-in" style={{
            width: '100%',
            maxWidth: '560px',
            background: '#0F172A',
            borderRadius: '16px',
            padding: '28px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#F8FAFC' }}>Create Job Requisition</h3>
              <button onClick={() => setShowCreateModal(false)} style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreateJob} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '13px', fontWeight: 600, color: '#CBD5E1', marginBottom: '4px', display: 'block' }}>
                  Job Title
                </label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Senior Python Backend Engineer"
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: '13px', fontWeight: 600, color: '#CBD5E1', marginBottom: '4px', display: 'block' }}>
                  Required Skills (Comma separated)
                </label>
                <input
                  type="text"
                  value={newSkills}
                  onChange={(e) => setNewSkills(e.target.value)}
                  placeholder="e.g. Python, FastAPI, Docker, PostgreSQL"
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '13px', fontWeight: 600, color: '#CBD5E1', marginBottom: '4px', display: 'block' }}>
                    Min Experience (Years)
                  </label>
                  <input
                    type="number"
                    value={newExp}
                    onChange={(e) => setNewExp(Number(e.target.value))}
                    min={0}
                    required
                  />
                </div>
                <div>
                  <label style={{ fontSize: '13px', fontWeight: 600, color: '#CBD5E1', marginBottom: '4px', display: 'block' }}>
                    Location
                  </label>
                  <input
                    type="text"
                    value={newLoc}
                    onChange={(e) => setNewLoc(e.target.value)}
                    placeholder="e.g. Pune / Hybrid"
                    required
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '13px', fontWeight: 600, color: '#CBD5E1', marginBottom: '4px', display: 'block' }}>
                  Job Description & Scope
                </label>
                <textarea
                  rows={4}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Describe key responsibilities, qualifications, and team mission..."
                  required
                />
              </div>

              <button
                type="submit"
                className="btn-primary"
                disabled={creating}
                style={{ width: '100%', justifyContent: 'center', marginTop: '10px', height: '42px' }}
              >
                {creating ? 'Creating Job...' : 'Publish Job Opening'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
