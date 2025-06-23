// User & Authentication Types
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'USER' | 'ADMIN' | 'DEVELOPER';
  avatar?: string;
  preferences?: Record<string, any>;
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

export interface RegisterData {
  email: string;
  password: string;
  name: string;
}

// Document Types
export interface Document {
  id: string;
  filename: string;
  originalName: string;
  size: number;
  mimeType: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'QUEUED';
  extractedText?: string;
  summary?: string;
  classification?: string;
  metadata: Record<string, any>;
  processingResults?: ProcessingResult[];
  uploadedAt: string;
  processedAt?: string;
  userId: string;
  url?: string;
  thumbnailUrl?: string;
}

export interface ProcessingResult {
  id: string;
  type: 'TEXT_EXTRACTION' | 'CLASSIFICATION' | 'SUMMARY' | 'EMBEDDING' | 'OCR';
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  result?: any;
  error?: string;
  processingTime?: number;
  confidence?: number;
  createdAt: string;
  completedAt?: string;
}

export interface ProcessingJob {
  id: string;
  documentId: string;
  type: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  progress: number;
  input?: any;
  output?: any;
  error?: string;
  priority: number;
  queueId?: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  failedAt?: string;
}

// Search & Analytics Types
export interface SearchQuery {
  query: string;
  filters?: {
    status?: Document['status'][];
    mimeType?: string[];
    dateRange?: {
      start: string;
      end: string;
    };
    classification?: string[];
  };
  pagination?: {
    page: number;
    limit: number;
  };
  sort?: {
    field: string;
    direction: 'asc' | 'desc';
  };
}

export interface SearchResult {
  document: Document;
  score: number;
  highlights?: string[];
  snippet?: string;
}

export interface AnalyticsData {
  totalDocuments: number;
  documentsProcessed: number;
  processingTime: {
    average: number;
    total: number;
  };
  statusDistribution: Record<Document['status'], number>;
  typeDistribution: Record<string, number>;
  dailyUploads: Array<{
    date: string;
    count: number;
  }>;
  processingStats: {
    successRate: number;
    averageProcessingTime: number;
    queueLength: number;
  };
}

// UI State Types
export interface NotificationState {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  actions?: Array<{
    label: string;
    action: () => void;
  }>;
}

export interface LoadingState {
  isLoading: boolean;
  message?: string;
}

export interface FileUploadState {
  files: File[];
  uploading: boolean;
  progress: Record<string, number>;
  errors: Record<string, string>;
  completed: string[];
}

// Settings & Preferences Types
export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  notifications: {
    email: boolean;
    push: boolean;
    documentProcessed: boolean;
    processingFailed: boolean;
  };
  dashboard: {
    defaultView: 'grid' | 'list';
    itemsPerPage: number;
    showPreview: boolean;
  };
  processing: {
    autoProcess: boolean;
    extractText: boolean;
    generateEmbeddings: boolean;
    classify: boolean;
    summarize: boolean;
    enableOCR: boolean;
  };
}

// WebSocket Types
export interface WebSocketMessage {
  type: 'document_updated' | 'processing_progress' | 'processing_complete' | 'processing_failed' | 'queue_update';
  payload: any;
  timestamp: string;
}

export interface ProcessingProgress {
  documentId: string;
  jobId: string;
  progress: number;
  stage: string;
  estimatedTimeRemaining?: number;
}

// API Response Types
export interface ApiError {
  message: string;
  code?: string;
  details?: any;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

// Form Types
export interface DocumentUploadForm {
  files: FileList;
  options: {
    extractText: boolean;
    generateEmbeddings: boolean;
    classify: boolean;
    summarize: boolean;
    enableOCR: boolean;
    priority: number;
  };
}

export interface DocumentSearchForm {
  query: string;
  status: string[];
  mimeType: string[];
  dateFrom?: string;
  dateTo?: string;
  classification: string[];
}

// Chart & Visualization Types
export interface ChartDataPoint {
  label: string;
  value: number;
  color?: string;
}

export interface TimeSeriesData {
  timestamp: string;
  value: number;
  category?: string;
}

export interface ProcessingMetrics {
  totalJobs: number;
  completedJobs: number;
  failedJobs: number;
  averageProcessingTime: number;
  queueLength: number;
  throughputPerHour: number;
}

// Component Props Types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

export interface ButtonProps extends BaseComponentProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
}

export interface InputProps extends BaseComponentProps {
  type?: string;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  error?: string;
  disabled?: boolean;
  required?: boolean;
}

export interface ModalProps extends BaseComponentProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

// Route Types
export interface AppRoute {
  path: string;
  component: React.ComponentType;
  title: string;
  requiresAuth?: boolean;
  roles?: User['role'][];
  exact?: boolean;
}

// Store Types (for Zustand)
export interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
}

export interface DocumentStore {
  documents: Document[];
  selectedDocument: Document | null;
  isLoading: boolean;
  searchQuery: string;
  filters: SearchQuery['filters'];
  pagination: PaginationMeta | null;
  fetchDocuments: () => Promise<void>;
  uploadDocument: (file: File, options?: any) => Promise<void>;
  deleteDocument: (id: string) => Promise<void>;
  setSelectedDocument: (document: Document | null) => void;
  setSearchQuery: (query: string) => void;
  setFilters: (filters: SearchQuery['filters']) => void;
}

export interface NotificationStore {
  notifications: NotificationState[];
  addNotification: (notification: Omit<NotificationState, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

