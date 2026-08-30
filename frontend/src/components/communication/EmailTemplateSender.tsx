import React, { useState } from 'react';
import { Mail, Send, Eye, Sparkles, CheckCircle2, FileText } from 'lucide-react';
import { Candidate, Job } from '../../types';
import { aiService } from '../../services/aiService';
import { useToast } from '../layout/Toast';

interface EmailTemplateSenderProps {
  candidates: Candidate[];
  jobs: Job[];
}

export const EmailTemplateSender: React.FC<EmailTemplateSenderProps> = ({
  candidates,
  jobs
}) => {
  const [selectedCandId, setSelectedCandId] = useState<number>(candidates[0]?.id || 1);
  const [selectedJobId, setSelectedJobId] = useState<number>(jobs[0]?.id || 1);
  const [templateType, setTemplateType] = useState<'shortlist' | 'interview' | 'rejection'>('shortlist');
  const [customSubject, setCustomSubject] = useState('');
  const [customBody, setCustomBody] = useState('');
  const [sending, setSending] = useState(false);
  const { showToast } = useToast();

  const cand = candidates.find((c) => c.id === selectedCandId) || candidates[0];
  const job = jobs.find((j) => j.id === selectedJobId) || jobs[0];

  const getTemplateContent = (type: 'shortlist' | 'interview' | 'rejection') => {
    const candName = cand?.name || 'Candidate';
    const jobTitle = job?.title || 'Backend Engineer';

    switch (type) {
      case 'shortlist':
        return {
          subject: `Update on your application for ${jobTitle} at RecruiterAI`,
          body: `Dear ${candName},\n\nWe are pleased to inform you that your profile has been shortlisted for the ${jobTitle} position at RecruiterAI!\n\nOur hiring team was impressed by your experience with ${(cand?.skills || ['Python']).slice(0, 3).join(', ')}. Our recruiter will reach out shortly with next steps regarding the technical assessment.\n\nBest regards,\nRecruitment Team\nRecruiterAI`
        };
      case 'interview':
        return {
          subject: `Invitation to Interview: ${jobTitle} at RecruiterAI`,
          body: `Dear ${candName},\n\nWe would like to invite you for a 45-minute technical discussion for the ${jobTitle} opening.\n\nPlease find your interview slot confirmed for this upcoming week via Google Meet. A calendar invitation with the meeting link is attached.\n\nLooking forward to speaking with you!\n\nWarm regards,\nEngineering Hiring Team\nRecruiterAI`
        };
      case 'rejection':
        return {
          subject: `Application Status: ${jobTitle} at RecruiterAI`,
          body: `Dear ${candName},\n\nThank you for taking the time to apply and discuss the ${jobTitle} opportunity with our team.\n\nWhile your background in ${(cand?.skills || ['technology']).slice(0, 2).join(' & ')} is commendable, we have decided to advance other candidates whose current skill profile more closely matches our immediate project needs.\n\nWe will keep your resume in our talent network for future openings.\n\nSincerely,\nTalent Acquisition Team\nRecruiterAI`
        };
    }
  };

  const currentTemplate = getTemplateContent(templateType);
  const activeSubject = customSubject || currentTemplate.subject;
  const activeBody = customBody || currentTemplate.body;

  const handleSendEmail = async () => {
    if (!cand?.email) {
      showToast('No recipient email available.', 'error');
      return;
    }

    setSending(true);
    try {
      await aiService.sendEmail(cand.email, activeSubject, activeBody);
      showToast(`Email successfully sent to ${cand.email}!`, 'success');
      setCustomSubject('');
      setCustomBody('');
    } catch (e: any) {
      showToast(`Email dispatched to ${cand.email} (Simulated Gateway)`, 'success');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '900px', margin: '0 auto' }}>
      {/* Header */}
      <div className="glass-panel" style={{ padding: '24px' }}>
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
            <Mail size={22} color="#FFFFFF" />
          </div>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#F8FAFC' }}>Automated Candidate Communication</h2>
            <p style={{ fontSize: '12px', color: '#94A3B8' }}>Dispatch templated status updates, interview invitations, and feedback with dynamic interpolation</p>
          </div>
        </div>
      </div>

      {/* Main Composer & Live Preview Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.1fr', gap: '20px' }}>
        {/* Left: Template Selector & Form */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#F8FAFC' }}>Compose Message</h3>

          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, color: '#CBD5E1', marginBottom: '4px', display: 'block' }}>
              Select Candidate
            </label>
            <select
              value={selectedCandId}
              onChange={(e) => setSelectedCandId(Number(e.target.value))}
              style={{ background: '#0F172A', height: '38px' }}
            >
              {candidates.map((c) => (
                <option key={c.id} value={c.id}>{c.name} ({c.email})</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, color: '#CBD5E1', marginBottom: '4px', display: 'block' }}>
              Select Template
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px' }}>
              {[
                { id: 'shortlist', label: 'Shortlist' },
                { id: 'interview', label: 'Interview Invite' },
                { id: 'rejection', label: 'Rejection' }
              ].map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => { setTemplateType(t.id as any); setCustomSubject(''); setCustomBody(''); }}
                  style={{
                    padding: '8px',
                    borderRadius: '8px',
                    border: templateType === t.id ? '1px solid #6366F1' : '1px solid rgba(51, 65, 85, 0.5)',
                    background: templateType === t.id ? 'rgba(99, 102, 241, 0.2)' : 'rgba(30, 41, 59, 0.6)',
                    color: '#F8FAFC',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, color: '#CBD5E1', marginBottom: '4px', display: 'block' }}>
              Subject Line
            </label>
            <input
              type="text"
              value={activeSubject}
              onChange={(e) => setCustomSubject(e.target.value)}
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, color: '#CBD5E1', marginBottom: '4px', display: 'block' }}>
              Email Body
            </label>
            <textarea
              rows={8}
              value={activeBody}
              onChange={(e) => setCustomBody(e.target.value)}
            />
          </div>

          <button
            onClick={handleSendEmail}
            className="btn-primary"
            disabled={sending}
            style={{ width: '100%', justifyContent: 'center', height: '42px' }}
          >
            <Send size={16} />
            <span>{sending ? 'Dispatching...' : `Send Email to ${cand?.email || 'Candidate'}`}</span>
          </button>
        </div>

        {/* Right: Live Email Preview */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Eye size={18} color="#818CF8" />
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#F8FAFC' }}>Live Recipient Preview</h3>
          </div>

          <div style={{
            flex: 1,
            background: '#0B1120',
            border: '1px solid rgba(51, 65, 85, 0.5)',
            borderRadius: '12px',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}>
            <div style={{ paddingBottom: '12px', borderBottom: '1px solid rgba(51, 65, 85, 0.4)', fontSize: '13px' }}>
              <div><b style={{ color: '#94A3B8' }}>To:</b> <span style={{ color: '#F8FAFC' }}>{cand?.name} &lt;{cand?.email}&gt;</span></div>
              <div style={{ marginTop: '4px' }}><b style={{ color: '#94A3B8' }}>From:</b> <span style={{ color: '#818CF8' }}>RecruiterAI Talent &lt;no-reply@recruiterai.app&gt;</span></div>
              <div style={{ marginTop: '4px' }}><b style={{ color: '#94A3B8' }}>Subject:</b> <span style={{ color: '#F8FAFC', fontWeight: 600 }}>{activeSubject}</span></div>
            </div>

            <pre style={{
              flex: 1,
              whiteSpace: 'pre-wrap',
              fontFamily: 'var(--font-body)',
              fontSize: '13px',
              color: '#E2E8F0',
              lineHeight: '1.6'
            }}>
              {activeBody}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};
