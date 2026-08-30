import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Sparkles, Loader2, ListPlus } from 'lucide-react';
import { Job, Candidate } from '../../types';
import { candidateService } from '../../services/candidateService';
import { useToast } from '../layout/Toast';

interface ResumeUploaderProps {
  jobs: Job[];
  onUploadSuccess: (createdCandidate: Candidate) => void;
}

export const ResumeUploader: React.FC<ResumeUploaderProps> = ({
  jobs,
  onUploadSuccess
}) => {
  const [selectedJobId, setSelectedJobId] = useState<number | undefined>(jobs[0]?.id);
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [uploadedCandidates, setUploadedCandidates] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { showToast } = useToast();

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const validFiles = Array.from(e.dataTransfer.files).filter((f) =>
        f.name.endsWith('.pdf') || f.name.endsWith('.docx') || f.name.endsWith('.txt')
      );
      setFiles(validFiles);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleProcessUploads = async () => {
    if (files.length === 0) {
      showToast('Please select at least one resume file.', 'error');
      return;
    }

    setUploading(true);
    const createdList = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      setCurrentStep(`Processing ${file.name} (${i + 1}/${files.length}): Document Reader...`);
      await new Promise((r) => setTimeout(r, 400));

      setCurrentStep(`Extracting candidate entities & AI matching...`);
      try {
        const res = await candidateService.uploadResume(file, selectedJobId);
        createdList.push(res);
        if (res.candidate) {
          onUploadSuccess(res.candidate);
        }
      } catch (err: any) {
        showToast(`Failed uploading ${file.name}: ${err.response?.data?.detail || err.message}`, 'error');
      }
    }

    setUploading(false);
    setCurrentStep('');
    setUploadedCandidates(createdList);
    setFiles([]);
    showToast(`Successfully processed ${createdList.length} resume(s)!`, 'success');
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '850px', margin: '0 auto' }}>
      <div className="glass-panel" style={{ padding: '30px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <UploadCloud size={22} color="#FFFFFF" />
          </div>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#F8FAFC' }}>Resume Ingestion & Batch Processing</h2>
            <p style={{ fontSize: '12px', color: '#94A3B8' }}>Upload single or batch PDF / DOCX files for automatic entity extraction and AI scoring</p>
          </div>
        </div>

        {/* Target Job Selector */}
        <div style={{ margin: '20px 0' }}>
          <label style={{ fontSize: '13px', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px', display: 'block' }}>
            Target Job Opening for Matching:
          </label>
          <select
            value={selectedJobId || ''}
            onChange={(e) => setSelectedJobId(Number(e.target.value))}
            style={{ height: '42px', background: '#0F172A' }}
          >
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.title} ({j.department || 'Engineering'}) — {j.location || 'Pune'}
              </option>
            ))}
          </select>
        </div>

        {/* Dropzone */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleFileDrop}
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: '2px dashed rgba(99, 102, 241, 0.4)',
            borderRadius: '16px',
            padding: '40px 20px',
            textAlign: 'center',
            background: 'rgba(15, 23, 42, 0.6)',
            cursor: 'pointer',
            transition: 'border-color 0.2s ease, background 0.2s ease'
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.docx,.txt"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />

          <div style={{
            width: '50px',
            height: '50px',
            borderRadius: '50%',
            background: 'rgba(99, 102, 241, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 12px auto'
          }}>
            <UploadCloud size={24} color="#818CF8" />
          </div>

          <div style={{ fontWeight: 700, fontSize: '15px', color: '#F8FAFC' }}>
            Click to upload or drag & drop resumes here
          </div>
          <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>
            Supported formats: PDF, DOCX, TXT (Batch Upload Supported • Max 5MB per file)
          </div>
        </div>

        {/* Selected Files Queue */}
        {files.length > 0 && (
          <div style={{ marginTop: '20px' }}>
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#E2E8F0', marginBottom: '8px' }}>
              Files Selected for Batch Ingestion ({files.length}):
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {files.map((f, idx) => (
                <div key={idx} style={{
                  padding: '10px 14px',
                  background: 'rgba(30, 41, 59, 0.6)',
                  borderRadius: '8px',
                  border: '1px solid rgba(51, 65, 85, 0.4)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  fontSize: '13px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <FileText size={16} color="#818CF8" />
                    <span style={{ color: '#F8FAFC', fontWeight: 600 }}>{f.name}</span>
                    <span style={{ fontSize: '11px', color: '#94A3B8' }}>({(f.size / 1024).toFixed(1)} KB)</span>
                  </div>
                  <span className="badge badge-indigo">Ready</span>
                </div>
              ))}
            </div>

            <button
              onClick={handleProcessUploads}
              className="btn-primary"
              disabled={uploading}
              style={{ marginTop: '16px', width: '100%', justifyContent: 'center', height: '44px' }}
            >
              {uploading ? (
                <>
                  <Loader2 size={18} className="spin" />
                  <span>{currentStep}</span>
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  <span>Run AI Pipeline & Ingest {files.length} Resume(s)</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Upload Results Preview */}
      {uploadedCandidates.length > 0 && (
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#F8FAFC', marginBottom: '16px' }}>
            🎉 Successfully Ingested Candidate Profiles
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px' }}>
            {uploadedCandidates.map((res, idx) => {
              const cand = res.candidate;
              if (!cand) return null;
              const finalScore = cand.final_score || cand.match_score || 75;
              return (
                <div key={idx} style={{
                  padding: '16px',
                  background: 'rgba(15, 23, 42, 0.8)',
                  borderRadius: '12px',
                  border: '1px solid rgba(51, 65, 85, 0.5)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, color: '#F8FAFC' }}>{cand.name}</span>
                    <span className="badge badge-emerald">{finalScore}% Final</span>
                  </div>
                  <div style={{ fontSize: '12px', color: '#94A3B8' }}>{cand.email}</div>
                  <div style={{ fontSize: '12px', color: '#CBD5E1' }}>Experience: {cand.experience || 0} years</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                    {(cand.skills || []).slice(0, 3).map((s: string, sIdx: number) => (
                      <span key={sIdx} className="badge badge-indigo" style={{ fontSize: '10px' }}>{s}</span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
