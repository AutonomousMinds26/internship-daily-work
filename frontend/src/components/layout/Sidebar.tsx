import React from 'react';
import {
  LayoutDashboard,
  Kanban,
  Users,
  UploadCloud,
  Briefcase,
  Bot,
  TrendingUp,
  GraduationCap,
  CalendarCheck,
  Mail,
  PieChart,
  LogOut,
  Sparkles,
  ShieldCheck
} from 'lucide-react';
import { UserRole } from '../../types';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  userRole: UserRole;
  username: string;
  onLogout: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  userRole,
  username,
  onLogout
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'pipeline', label: 'Kanban Pipeline', icon: Kanban, badge: 'Live' },
    { id: 'candidates', label: 'Candidate List', icon: Users },
    { id: 'upload', label: 'Resume Upload', icon: UploadCloud, badge: 'Batch' },
    { id: 'jobs', label: 'Job Management', icon: Briefcase },
    { id: 'screening', label: 'AI Screening', icon: Bot, badge: 'AI' },
    { id: 'predictive', label: 'Predictive Analytics', icon: TrendingUp },
    { id: 'skillgap', label: 'Skill-Gap Analysis', icon: GraduationCap },
    { id: 'interviews', label: 'Interview Scheduling', icon: CalendarCheck },
    { id: 'communication', label: 'Communication', icon: Mail },
    { id: 'analytics', label: 'Diversity & Reports', icon: PieChart },
    ...(userRole === 'Admin' ? [{ id: 'admin', label: 'Admin Console', icon: ShieldCheck, badge: 'Admin' }] : [])
  ];


  return (
    <aside style={{
      width: '260px',
      background: '#0B1120',
      borderRight: '1px solid rgba(51, 65, 85, 0.4)',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      position: 'fixed',
      left: 0,
      top: 0,
      zIndex: 50,
      userSelect: 'none'
    }}>
      {/* Brand Header */}
      <div style={{
        padding: '24px 20px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        borderBottom: '1px solid rgba(51, 65, 85, 0.3)'
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)'
        }}>
          <Sparkles size={22} color="#FFFFFF" />
        </div>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#F8FAFC', letterSpacing: '-0.03em' }}>RecruiterAI</h2>
          <span style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Portal v2.0</span>
        </div>
      </div>

      {/* Role Badge */}
      <div style={{ padding: '14px 20px', background: 'rgba(30, 41, 59, 0.4)', borderBottom: '1px solid rgba(51, 65, 85, 0.2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck size={16} color="#818CF8" />
          <span style={{ fontSize: '12px', color: '#94A3B8' }}>Signed in as:</span>
          <span className="badge badge-indigo" style={{ fontSize: '11px', padding: '2px 8px' }}>{userRole}</span>
        </div>
        <div style={{ fontSize: '12px', fontWeight: 600, color: '#E2E8F0', marginTop: '4px', paddingLeft: '24px' }}>
          {username}
        </div>
      </div>

      {/* Navigation List */}
      <nav style={{ flex: 1, padding: '16px 12px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                width: '100%',
                padding: '10px 14px',
                borderRadius: '10px',
                border: 'none',
                background: isActive ? 'linear-gradient(90deg, rgba(99, 102, 241, 0.2) 0%, rgba(99, 102, 241, 0.05) 100%)' : 'transparent',
                color: isActive ? '#818CF8' : '#94A3B8',
                fontWeight: isActive ? 700 : 500,
                fontSize: '14px',
                cursor: 'pointer',
                textAlign: 'left',
                borderLeft: isActive ? '3px solid #6366F1' : '3px solid transparent',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.color = '#F8FAFC';
                if (!isActive) e.currentTarget.style.background = 'rgba(30, 41, 59, 0.5)';
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.color = '#94A3B8';
                if (!isActive) e.currentTarget.style.background = 'transparent';
              }}
            >
              <Icon size={18} />
              <span style={{ flex: 1 }}>{item.label}</span>
              {item.badge && (
                <span style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  padding: '2px 6px',
                  borderRadius: '6px',
                  background: item.badge === 'Live' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(99, 102, 241, 0.2)',
                  color: item.badge === 'Live' ? '#34D399' : '#A5B4FC'
                }}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Logout Footer */}
      <div style={{ padding: '16px 20px', borderTop: '1px solid rgba(51, 65, 85, 0.3)' }}>
        <button
          onClick={onLogout}
          className="btn-secondary"
          style={{ width: '100%', justifyContent: 'center', color: '#F87171', borderColor: 'rgba(239, 68, 68, 0.3)' }}
        >
          <LogOut size={16} />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};
