// User and Authentication Types
export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'admin' | 'user';
  createdAt: string;
  updatedAt: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  password: string;
  name: string;
}

// Document Types
export interface Document {
  id: string;
  title: string;
  content: string;
  status: 'draft' | 'processing' | 'completed' | 'error';
  type: 'pdf' | 'docx' | 'txt' | 'md';
  size: number;
  uploadedAt: string;
  updatedAt: string;
  userId: string;
  metadata?: {
    pages?: number;
    words?: number;
    language?: string;
  };
  processingProgress?: number;
  tags: string[];
  version: number;
}

export interface DocumentUpload {
  file: File;
  title?: string;
  tags?: string[];
}

export interface DocumentFilter {
  status?: Document['status'];
  type?: Document['type'];
  search?: string;
  tags?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

// Socket Event Types
export interface SocketEvents {
  'document:updated': (document: Document) => void;
  'document:processing': (data: { id: string; progress: number }) => void;
  'document:completed': (document: Document) => void;
  'document:error': (data: { id: string; error: string }) => void;
  'user:connected': (data: { userId: string; count: number }) => void;
  'user:disconnected': (data: { userId: string; count: number }) => void;
}

// Dashboard Types
export interface DashboardStats {
  totalDocuments: number;
  processingDocuments: number;
  completedDocuments: number;
  errorDocuments: number;
  storageUsed: number;
  storageLimit: number;
  recentActivity: ActivityItem[];
}

export interface ActivityItem {
  id: string;
  type: 'upload' | 'processing' | 'completed' | 'error' | 'download';
  message: string;
  timestamp: string;
  documentId?: string;
}

// UI Component Types
export interface ComponentProps {
  children?: React.ReactNode;
  className?: string;
}

export interface LoadingState {
  isLoading: boolean;
  error?: string | null;
}

export interface FormState<T> {
  values: T;
  errors: Partial<Record<keyof T, string>>;
  isSubmitting: boolean;
  isValid: boolean;
}

// File Upload Types
export interface UploadProgress {
  documentId: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}

// Search and Filter Types
export interface SearchResult {
  id: string;
  type: 'document' | 'user';
  title: string;
  subtitle?: string;
  relevance: number;
  highlight?: string;
}

// Analytics Types
export interface AnalyticsData {
  documentsOverTime: Array<{
    date: string;
    count: number;
    processed: number;
  }>;
  documentsByType: Array<{
    type: string;
    count: number;
  }>;
  processingTimes: Array<{
    date: string;
    avgTime: number;
  }>;
  userActivity: Array<{
    date: string;
    activeUsers: number;
  }>;
}

// Settings Types
export interface UserSettings {
  theme: 'light' | 'dark' | 'system';
  language: string;
  notifications: {
    email: boolean;
    browser: boolean;
    processing: boolean;
    completed: boolean;
  };
  privacy: {
    profileVisible: boolean;
    analyticsEnabled: boolean;
  };
}

// Error Types
export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  details?: Record<string, any>;
}

export interface ValidationError {
  field: string;
  message: string;
}

// Utility Types
export type Status = 'idle' | 'loading' | 'success' | 'error';
export type Theme = 'light' | 'dark';
export type SortOrder = 'asc' | 'desc';
export type ViewMode = 'grid' | 'list' | 'table';

export interface SortConfig {
  field: string;
  order: SortOrder;
}

export interface ViewConfig {
  mode: ViewMode;
  itemsPerPage: number;
  sortConfig: SortConfig;
}

