import React, { useState, useEffect } from 'react';
import { ToastProvider, useToast } from './components/layout/Toast';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { LoginView } from './components/auth/LoginView';
import { RegisterView } from './components/auth/RegisterView';
import { ExecutiveDashboard } from './components/dashboard/ExecutiveDashboard';
import { KanbanBoard } from './components/pipeline/KanbanBoard';
import { CandidateListView } from './components/candidates/CandidateListView';
import { CandidateDetailsModal } from './components/candidates/CandidateDetailsModal';
import { ResumeUploader } from './components/upload/ResumeUploader';
import { JobManagementView } from './components/jobs/JobManagementView';
import { AIScreeningWizard } from './components/screening/AIScreeningWizard';
import { PredictiveAnalyticsView } from './components/predictive/PredictiveAnalyticsView';
import { SkillGapView } from './components/skillgap/SkillGapView';
import { InterviewCalendar } from './components/interviews/InterviewCalendar';
import { EmailTemplateSender } from './components/communication/EmailTemplateSender';
import { DiversityAnalyticsView } from './components/analytics/DiversityAnalyticsView';
import { AdminConsole } from './components/admin/AdminConsole';

import { User, Candidate, Job, CandidateStatus } from './types';
import { authService } from './services/authService';
import { candidateService } from './services/candidateService';
import { jobService } from './services/jobService';
import { realtimeService } from './services/websocketService';

const MainApp: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(authService.getCurrentUser());
  const [authView, setAuthView] = useState<'login' | 'register'>('login');
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [preselectedInterviewCand, setPreselectedInterviewCand] = useState<Candidate | null>(null);
  const [globalSearch, setGlobalSearch] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const { showToast } = useToast();

  const loadCoreData = async () => {
    setLoading(true);
    try {
      const [cands, jbs] = await Promise.all([
        candidateService.getCandidates(),
        jobService.getJobs()
      ]);
      setCandidates(cands);
      setJobs(jbs);
    } catch (e: any) {
      console.warn('Initial data load error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentUser) {
      loadCoreData();
      realtimeService.connect();

      const unsubscribe = realtimeService.subscribe((event) => {
        if (event.type === 'STATUS_UPDATE') {
          showToast(`Live update: Candidate #${event.payload?.candidate_id} status changed to ${event.payload?.status}`, 'info');
          setCandidates((prev) =>
            prev.map((c) =>
              c.id === event.payload?.candidate_id ? { ...c, status: event.payload?.status } : c
            )
          );
        } else if (event.type === 'OFFER_EXTENDED') {
          showToast(`Live event: Offer extended to ${event.payload?.candidate_name || 'Candidate'}`, 'success');
        }
      });

      return () => {
        unsubscribe();
        realtimeService.disconnect();
      };
    }
  }, [currentUser]);

  const handleLogout = async () => {
    await authService.logout();
    setCurrentUser(null);
    showToast('Signed out successfully.', 'info');
  };

  const handleUpdateStatus = async (candidateId: number, newStatus: CandidateStatus) => {
    try {
      const updated = await candidateService.updateStatus(candidateId, newStatus);
      setCandidates((prev) => prev.map((c) => (c.id === candidateId ? { ...c, status: newStatus } : c)));
      if (selectedCandidate && selectedCandidate.id === candidateId) {
        setSelectedCandidate({ ...selectedCandidate, status: newStatus });
      }
      realtimeService.send('STATUS_UPDATE', { candidate_id: candidateId, status: newStatus }, currentUser?.username);
      showToast(`Candidate status updated to ${newStatus}`, 'success');
    } catch (e: any) {
      showToast('Failed to update candidate status.', 'error');
    }
  };

  const handleScheduleInterview = (candidate: Candidate) => {
    setPreselectedInterviewCand(candidate);
    setSelectedCandidate(null);
    setCurrentTab('interviews');
  };

  const handleUploadSuccess = (newCand: Candidate) => {
    setCandidates((prev) => [newCand, ...prev]);
  };

  const handleJobCreated = (newJob: Job) => {
    setJobs((prev) => [newJob, ...prev]);
  };

  if (!currentUser) {
    if (authView === 'register') {
      return (
        <RegisterView
          onRegisterSuccess={(u) => { setCurrentUser(u); showToast(`Welcome to RecruiterAI, ${u.username}!`, 'success'); }}
          onBackToLogin={() => setAuthView('login')}
        />
      );
    }
    return (
      <LoginView
        onLoginSuccess={(u) => setCurrentUser(u)}
        onNavigateToRegister={() => setAuthView('register')}
      />
    );
  }

  const getPageTitle = () => {
    switch (currentTab) {
      case 'dashboard': return { title: 'Executive Recruitment Dashboard', sub: 'Key performance metrics, hiring velocity & candidate overview' };
      case 'pipeline': return { title: 'Candidate Pipeline', sub: 'Interactive stage-by-stage Kanban progression' };
      case 'candidates': return { title: 'Talent Directory', sub: 'Search, filter, and inspect scored candidates' };
      case 'upload': return { title: 'Resume Ingestion Hub', sub: 'Single and batch resume extraction & parsing' };
      case 'jobs': return { title: 'Job Requisitions', sub: 'Open roles and ranked talent matching' };
      case 'screening': return { title: 'AI Screening Assessment', sub: 'Automated qualification questionnaires and grading' };
      case 'predictive': return { title: 'Predictive Hiring Analytics', sub: 'Success probability and risk modeling' };
      case 'skillgap': return { title: 'Skill-Gap Matrix', sub: 'Side-by-side gap analysis and upskilling roadmaps' };
      case 'interviews': return { title: 'Interview Coordinator', sub: 'Schedule slots and manage calendar invites' };
      case 'communication': return { title: 'Candidate Outreach', sub: 'Templated automated emails and notices' };
      case 'analytics': return { title: 'Analytics & Diversity Audit', sub: 'Macro statistics and bias-free compliance verification' };
      case 'admin': return { title: 'Administration & Control Center', sub: 'RBAC, system health, integrations & audit logs' };
      default: return { title: 'RecruiterAI Portal', sub: '' };
    }
  };

  const pageInfo = getPageTitle();

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-main)' }}>
      {/* Sidebar */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={(tab) => setCurrentTab(tab)}
        userRole={currentUser.role}
        username={currentUser.username}
        onLogout={handleLogout}
      />

      {/* Main Content Area */}
      <div style={{ marginLeft: '260px', flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <Header
          title={pageInfo.title}
          subtitle={pageInfo.sub}
          userRole={currentUser.role}
          onQuickUpload={() => setCurrentTab('upload')}
          onQuickJob={() => setCurrentTab('jobs')}
          searchQuery={globalSearch}
          onSearchChange={(q) => {
            setGlobalSearch(q);
            if (currentTab !== 'candidates') setCurrentTab('candidates');
          }}
        />

        <main style={{ flex: 1, padding: '32px', maxWidth: '1400px', width: '100%', margin: '0 auto' }}>
          {currentTab === 'dashboard' && (
            <ExecutiveDashboard
              candidates={candidates}
              jobs={jobs}
              onNavigate={(tab) => setCurrentTab(tab)}
              onSelectCandidate={(cand) => setSelectedCandidate(cand)}
            />
          )}

          {currentTab === 'pipeline' && (
            <KanbanBoard
              candidates={candidates}
              onSelectCandidate={(cand) => setSelectedCandidate(cand)}
              onUpdateStatus={handleUpdateStatus}
            />
          )}

          {currentTab === 'candidates' && (
            <CandidateListView
              candidates={candidates}
              onSelectCandidate={(cand) => setSelectedCandidate(cand)}
              onScheduleInterview={handleScheduleInterview}
              onUpdateStatus={handleUpdateStatus}
            />
          )}

          {currentTab === 'upload' && (
            <ResumeUploader
              jobs={jobs}
              onUploadSuccess={handleUploadSuccess}
            />
          )}

          {currentTab === 'jobs' && (
            <JobManagementView
              jobs={jobs}
              candidates={candidates}
              onJobCreated={handleJobCreated}
              onSelectCandidate={(cand) => setSelectedCandidate(cand)}
            />
          )}

          {currentTab === 'screening' && (
            <AIScreeningWizard
              candidates={candidates}
              jobs={jobs}
            />
          )}

          {currentTab === 'predictive' && (
            <PredictiveAnalyticsView
              candidates={candidates}
              jobs={jobs}
            />
          )}

          {currentTab === 'skillgap' && (
            <SkillGapView
              candidates={candidates}
              jobs={jobs}
            />
          )}

          {currentTab === 'interviews' && (
            <InterviewCalendar
              candidates={candidates}
              jobs={jobs}
              preselectedCandidate={preselectedInterviewCand}
            />
          )}

          {currentTab === 'communication' && (
            <EmailTemplateSender
              candidates={candidates}
              jobs={jobs}
            />
          )}

          {currentTab === 'analytics' && (
            <DiversityAnalyticsView
              candidates={candidates}
            />
          )}

          {currentTab === 'admin' && (
            <AdminConsole />
          )}
        </main>
      </div>

      {/* Candidate Deep Profile Modal */}
      {selectedCandidate && (
        <CandidateDetailsModal
          candidate={selectedCandidate}
          onClose={() => setSelectedCandidate(null)}
          onUpdateStatus={handleUpdateStatus}
          onScheduleInterview={handleScheduleInterview}
        />
      )}
    </div>
  );
};

export default function App() {
  return (
    <ToastProvider>
      <MainApp />
    </ToastProvider>
  );
}
