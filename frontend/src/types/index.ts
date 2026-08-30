export type UserRole = 'Admin' | 'Recruiter' | 'Hiring Manager' | 'Candidate';

export type CandidateStatus =
  | 'Applied'
  | 'Screening'
  | 'Shortlisted'
  | 'Interview'
  | 'Selected'
  | 'Hired'
  | 'Rejected'
  | 'Parsed'
  | 'Matched'
  | 'Interview Scheduled';

export interface User {
  username: string;
  role: UserRole;
  token?: string;
}

export interface Candidate {
  id: number;
  name: string;
  email: string;
  phone?: string;
  education?: string;
  experience?: number;
  skills: string[];
  projects?: string[];
  notice_period?: string;
  expected_ctc?: string;
  location?: string;
  resume_text?: string;
  status: CandidateStatus;
  ats_score?: number;
  match_score?: number;
  screening_score?: number;
  final_score?: number;
  ai_summary?: string;
  created_at?: string;
  updated_at?: string;
  feedback?: string;
}

export interface Job {
  id: number;
  title: string;
  description: string;
  requirements?: string[];
  department?: string;
  location?: string;
  experience_required?: number;
  salary_range?: string;
  is_active?: boolean;
  created_at?: string;
  candidate_count?: number;
}

export interface CandidateScore {
  id?: number;
  candidate_id: number;
  job_id: number;
  match_score: number;
  skill_gap_report?: any;
  recommendation?: string;
}

export interface CandidateHistoryItem {
  id: number;
  candidate_id: number;
  action: string;
  details?: string;
  performed_by?: string;
  created_at: string;
}

export interface InterviewSlot {
  id: number;
  interviewer_name: string;
  interviewer_email: string;
  start_time: string;
  end_time: string;
  is_booked: boolean;
  interview_id?: number;
}

export interface Interview {
  id: number;
  candidate_id: number;
  job_id: number;
  interviewer_name: string;
  interviewer_email: string;
  scheduled_time: string;
  duration_minutes: number;
  mode: string;
  notes?: string;
  status: string;
  candidate_name?: string;
  job_title?: string;
}

export interface ScreeningEvaluation {
  score: number;
  relevance: 'High' | 'Medium' | 'Low';
  concerns: string[];
  explanation: string;
  question?: string;
  answer?: string;
}

export interface ScreeningBatchResult {
  screening_score: number;
  average_score_out_of_10: number;
  evaluations: ScreeningEvaluation[];
  concerns: string[];
  strengths: string[];
  summary: string;
}

export interface PredictiveAnalyticsResult {
  candidate: string;
  final_score: number;
  hiring_probability: number;
  hiring_probability_percentage: string;
  hiring_probability_category: 'High' | 'Medium' | 'Low';
  risk_level: 'Low' | 'Medium' | 'High';
  recommendation: string;
  strengths: string[];
  risks: string[];
  missing_skills: string[];
  matched_skills: string[];
  explanation: string;
  model_version: string;
}

export interface AIExplainabilityBundle {
  candidate_name: string;
  candidate_email: string;
  ats_score: number;
  match_score: number;
  screening_score: number;
  skill_coverage: number;
  skill_coverage_percentage: string;
  experience_fit: number;
  experience_fit_percentage: string;
  final_score: number;
  hiring_probability: number;
  hiring_probability_percentage: string;
  risk_level: 'Low' | 'Medium' | 'High';
  strengths: string[];
  weaknesses: string[];
  missing_skills: string[];
  matched_skills: string[];
  recommendation: string;
  explanation: string;
}

export interface DiversityInsightsReport {
  total_candidates: number;
  average_final_score: number;
  score_tiers: {
    'High (>=80%)': number;
    'Medium (60-79%)': number;
    'Low (<60%)': number;
  };
  experience_distribution: Record<string, number>;
  top_represented_skills: Record<string, number>;
  status_distribution: Record<string, number>;
  fairness_audit: {
    demographic_neutrality_verified: boolean;
    scoring_methodology: string;
    compliance_notice: string;
  };
}

export interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  body: string;
}

export interface AdminUser {
  id: number;
  username: string;
  email?: string;
  role: UserRole;
  is_active: boolean;
  organization_id?: number;
  hiring_team_id?: number;
  last_login?: string;
  created_at: string;
}

export interface IntegrationConfigItem {
  id: number;
  provider_name: string;
  provider_category: string;
  is_enabled: boolean;
  config_data?: any;
  last_sync_at?: string;
}

export interface AuditLogItem {
  id: number;
  user_id?: number;
  username?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details?: any;
  timestamp: string;
}

export interface OfferItem {
  id: number;
  candidate_id: number;
  job_id: number;
  base_salary: number;
  bonus: number;
  stock_grant: number;
  currency: string;
  status: 'Draft' | 'Sent' | 'Accepted' | 'Rejected' | 'Expired';
  offer_letter_text?: string;
  expiration_date?: string;
  created_by?: string;
  created_at: string;
}

export interface SystemStatusItem {
  status: string;
  timestamp: string;
  environment: string;
  database: {
    status: string;
    type: string;
    counts: {
      users: number;
      candidates: number;
      jobs: number;
      offers: number;
    };
  };
  background_worker: {
    broker: string;
    status: string;
  };
  llm_provider: {
    active_provider: string;
  };
  integrations_mode: string;
}

