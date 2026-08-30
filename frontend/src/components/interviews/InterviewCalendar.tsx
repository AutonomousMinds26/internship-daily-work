import React, { useState, useEffect } from 'react';
import { Calendar, Plus, Clock, User, Download, CheckCircle2, XCircle, Video, MapPin } from 'lucide-react';
import { Candidate, Job, Interview, InterviewSlot } from '../../types';
import { interviewService } from '../../services/interviewService';
import { useToast } from '../layout/Toast';

interface InterviewCalendarProps {
  candidates: Candidate[];
  jobs: Job[];
  preselectedCandidate?: Candidate | null;
}

export const InterviewCalendar: React.FC<InterviewCalendarProps> = ({
  candidates,
  jobs,
  preselectedCandidate
}) => {
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [slots, setSlots] = useState<InterviewSlot[]>([]);
  const [selectedCandId, setSelectedCandId] = useState<number>(preselectedCandidate?.id || candidates[0]?.id || 1);
  const [selectedJobId, setSelectedJobId] = useState<number>(jobs[0]?.id || 1);
  const [interviewerName, setInterviewerName] = useState('Sarah Jenkins (Engineering Manager)');
  const [interviewerEmail, setInterviewerEmail] = useState('sarah.jenkins@company.com');
  const [interviewDate, setInterviewDate] = useState('2026-09-02T10:00');
  const [duration, setDuration] = useState(45);
  const [mode, setMode] = useState('Online');
  const [scheduling, setScheduling] = useState(false);
  const { showToast } = useToast();

  const loadData = async () => {
    try {
      const [intList, slotList] = await Promise.all([
        interviewService.getInterviews(),
        interviewService.getAvailableSlots()
      ]);
      setInterviews(intList);
      setSlots(slotList);
    } catch (e: any) {
      console.warn('Could not load interview data:', e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    setScheduling(true);
    try {
      const created = await interviewService.createInterview({
        candidate_id: selectedCandId,
        job_id: selectedJobId,
        interviewer_name: interviewerName,
        interviewer_email: interviewerEmail,
        scheduled_time: interviewDate,
        duration_minutes: duration,
        mode: mode,
        status: 'Scheduled'
      });

      showToast(`Interview scheduled for ${new Date(interviewDate).toLocaleString()}!`, 'success');
      loadData();
    } catch (e: any) {
      showToast('Failed to schedule interview.', 'error');
    } finally {
      setScheduling(false);
    }
  };

  const handleStatusChange = async (id: number, newStatus: string) => {
    try {
      await interviewService.updateStatus(id, newStatus);
      showToast(`Interview marked as ${newStatus}`, 'success');
      loadData();
    } catch (e: any) {
      showToast('Failed to update status.', 'error');
    }
  };

  const handleCancelInterview = async (id: number) => {
    try {
      await interviewService.deleteInterview(id);
      showToast('Interview cancelled successfully.', 'info');
      loadData();
    } catch (e: any) {
      showToast('Failed to cancel interview.', 'error');
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#F8FAFC' }}>Interview Scheduling & Slot Management</h2>
          <p style={{ fontSize: '12px', color: '#94A3B8' }}>Coordinate interviewer calendars, book interview slots, and generate calendar invites</p>
        </div>
      </div>

      {/* Grid: Schedule Form on Left, Scheduled Calendar Feed on Right */}
      <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: '20px' }}>
        {/* Schedule Interview Form */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#F8FAFC', marginBottom: '16px' }}>
            Book New Interview
          </h3>

          <form onSubmit={handleSchedule} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#CBD5E1', marginBottom: '4px', display: 'block' }}>
                Candidate
              </label>
              <select
                value={selectedCandId}
                onChange={(e) => setSelectedCandId(Number(e.target.value))}
                style={{ height: '38px', background: '#0F172A' }}
              >
                {candidates.map((c) => (
                  <option key={c.id} value={c.id}>{c.name} ({c.email})</option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#CBD5E1', marginBottom: '4px', display: 'block' }}>
                Target Requisition
              </label>
              <select
                value={selectedJobId}
                onChange={(e) => setSelectedJobId(Number(e.target.value))}
                style={{ height: '38px', background: '#0F172A' }}
              >
                {jobs.map((j) => (
                  <option key={j.id} value={j.id}>{j.title}</option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#CBD5E1', marginBottom: '4px', display: 'block' }}>
                Interviewer Name & Role
              </label>
              <input
                type="text"
                value={interviewerName}
                onChange={(e) => setInterviewerName(e.target.value)}
                required
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '10px' }}>
              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, color: '#CBD5E1', marginBottom: '4px', display: 'block' }}>
                  Date & Time
                </label>
                <input
                  type="datetime-local"
                  value={interviewDate}
                  onChange={(e) => setInterviewDate(e.target.value)}
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, color: '#CBD5E1', marginBottom: '4px', display: 'block' }}>
                  Duration (Mins)
                </label>
                <input
                  type="number"
                  value={duration}
                  onChange={(e) => setDuration(Number(e.target.value))}
                  min={15}
                  step={15}
                  required
                />
              </div>
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#CBD5E1', marginBottom: '4px', display: 'block' }}>
                Interview Mode
              </label>
              <select value={mode} onChange={(e) => setMode(e.target.value)} style={{ height: '38px', background: '#0F172A' }}>
                <option value="Online">Google Meet / Video Conference</option>
                <option value="In-Person">In-Person (HQ Office)</option>
                <option value="Phone">Phone Screening</option>
              </select>
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={scheduling}
              style={{ width: '100%', justifyContent: 'center', marginTop: '8px', height: '42px' }}
            >
              <Calendar size={16} />
              <span>{scheduling ? 'Scheduling...' : 'Confirm & Schedule Interview'}</span>
            </button>
          </form>
        </div>

        {/* Scheduled Interviews Feed */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#F8FAFC' }}>
              Upcoming Scheduled Interviews ({interviews.length})
            </h3>
            <span className="badge badge-indigo">Auto-Synced</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {interviews.length === 0 ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#64748B', fontSize: '13px' }}>
                No interviews scheduled currently.
              </div>
            ) : (
              interviews.map((intv) => {
                const cand = candidates.find((c) => c.id === intv.candidate_id);
                const job = jobs.find((j) => j.id === intv.job_id);

                return (
                  <div
                    key={intv.id}
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
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ fontWeight: 700, color: '#F8FAFC', fontSize: '14px' }}>
                          {cand ? cand.name : `Candidate #${intv.candidate_id}`}
                        </span>
                        <span className={`badge ${intv.status === 'Completed' ? 'badge-emerald' : intv.status === 'Cancelled' ? 'badge-rose' : 'badge-indigo'}`}>
                          {intv.status}
                        </span>
                      </div>
                      <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>
                        {job ? job.title : 'Software Engineer'} • Interviwer: {intv.interviewer_name}
                      </div>
                      <div style={{ fontSize: '11px', color: '#818CF8', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Clock size={12} />
                        <span>{new Date(intv.scheduled_time).toLocaleString()} ({intv.duration_minutes} mins) • {intv.mode}</span>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <a
                        href={interviewService.getInviteDownloadUrl(intv.id)}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-secondary btn-sm"
                        title="Download .ics Calendar Invite"
                      >
                        <Download size={13} />
                        <span>.ICS</span>
                      </a>
                      <button
                        onClick={() => handleStatusChange(intv.id, 'Completed')}
                        className="btn-secondary btn-sm"
                        style={{ color: '#34D399' }}
                        title="Mark Completed"
                      >
                        <CheckCircle2 size={14} />
                      </button>
                      <button
                        onClick={() => handleCancelInterview(intv.id)}
                        className="btn-secondary btn-sm"
                        style={{ color: '#F87171' }}
                        title="Cancel Interview"
                      >
                        <XCircle size={14} />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
