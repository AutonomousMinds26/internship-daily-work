import React from 'react';
import { Search, Plus, Upload, Bell } from 'lucide-react';
import { UserRole } from '../../types';

interface HeaderProps {
  title: string;
  subtitle?: string;
  userRole: UserRole;
  onQuickUpload: () => void;
  onQuickJob: () => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  userRole,
  onQuickUpload,
  onQuickJob,
  searchQuery,
  onSearchChange
}) => {
  return (
    <header style={{
      height: '70px',
      background: 'rgba(15, 23, 42, 0.8)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid rgba(51, 65, 85, 0.4)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 32px',
      position: 'sticky',
      top: 0,
      zIndex: 40
    }}>
      <div>
        <h1 style={{ fontSize: '20px', fontWeight: 700, color: '#F8FAFC' }}>{title}</h1>
        {subtitle && <p style={{ fontSize: '12px', color: '#94A3B8' }}>{subtitle}</p>}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Global Search */}
        <div style={{ position: 'relative', width: '280px' }}>
          <Search size={16} color="#94A3B8" style={{ position: 'absolute', left: '12px', top: '12px' }} />
          <input
            type="text"
            placeholder="Search candidates, skills, jobs..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            style={{ paddingLeft: '36px', height: '38px', fontSize: '13px' }}
          />
        </div>

        {/* Quick Action Buttons */}
        {userRole !== 'Candidate' && (
          <>
            <button onClick={onQuickUpload} className="btn-secondary btn-sm" style={{ height: '38px' }}>
              <Upload size={15} />
              <span>Upload Resume</span>
            </button>
            <button onClick={onQuickJob} className="btn-primary btn-sm" style={{ height: '38px' }}>
              <Plus size={15} />
              <span>Post New Job</span>
            </button>
          </>
        )}

        {/* Notification Bell */}
        <button style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'rgba(30, 41, 59, 0.6)',
          border: '1px solid rgba(51, 65, 85, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#94A3B8',
          cursor: 'pointer'
        }}>
          <Bell size={18} />
        </button>
      </div>
    </header>
  );
};
