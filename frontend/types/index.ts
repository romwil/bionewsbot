// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

// Authentication Types
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'analyst' | 'viewer';
  created_at: string;
  last_login?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

// Company Types
export interface Company {
  id: string;
  name: string;
  ticker?: string;
  description?: string;
  website?: string;
  industry: string;
  sub_industry?: string;
  founded_year?: number;
  headquarters?: string;
  employee_count?: number;
  market_cap?: number;
  tags: string[];
  monitoring_status: 'active' | 'paused' | 'archived';
  created_at: string;
  updated_at: string;
  insights_count?: number;
}

export interface CompanyFormData {
  name: string;
  ticker?: string;
  description?: string;
  website?: string;
  industry: string;
  sub_industry?: string;
  founded_year?: number;
  headquarters?: string;
  employee_count?: number;
  market_cap?: number;
  tags: string[];
  monitoring_status: 'active' | 'paused' | 'archived';
}

// Insight Types
export interface Insight {
  id: string;
  company_id: string;
  company_name: string;
  type: 'news' | 'financial' | 'regulatory' | 'clinical' | 'partnership' | 'product';
  title: string;
  summary: string;
  content?: string;
  source: string;
  source_url?: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  confidence_score: number;
  tags: string[];
  created_at: string;
  is_read: boolean;
  is_flagged: boolean;
}

export interface InsightFilters {
  company_id?: string;
  type?: string[];
  sentiment?: string[];
  date_from?: string;
  date_to?: string;
  is_read?: boolean;
  is_flagged?: boolean;
  search?: string;
}

// Analysis Types
export interface AnalysisRun {
  id: string;
  name: string;
  type: 'scheduled' | 'manual';
  status: 'pending' | 'running' | 'completed' | 'failed';
  companies_count: number;
  insights_generated: number;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  created_by: string;
}

export interface AnalysisConfig {
  schedule_enabled: boolean;
  schedule_cron: string;
  sources: string[];
  insight_types: string[];
  min_confidence_score: number;
  auto_flag_negative: boolean;
}

// Dashboard Types
export interface DashboardMetrics {
  total_companies: number;
  active_companies: number;
  total_insights: number;
  insights_today: number;
  insights_this_week: number;
  unread_insights: number;
  flagged_insights: number;
  sentiment_distribution: {
    positive: number;
    negative: number;
    neutral: number;
  };
}

export interface TrendData {
  date: string;
  value: number;
  label?: string;
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }[];
}

// Notification Types
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  is_read: boolean;
  action_url?: string;
}

// WebSocket Types
export interface WebSocketMessage {
  type: 'insight' | 'analysis' | 'notification' | 'system';
  data: any;
  timestamp: string;
}

// Form Types
export interface FormError {
  field: string;
  message: string;
}

// Pagination Types
export interface PaginationParams {
  page: number;
  limit: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
  limit: number;
}
