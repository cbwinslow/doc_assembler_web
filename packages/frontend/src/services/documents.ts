import { apiClient } from './api';
import { Document, DocumentUpload, DocumentFilter, PaginatedResponse } from '@/types';

export interface DocumentsResponse extends PaginatedResponse<Document> {}

export interface DocumentStats {
  totalDocuments: number;
  processingDocuments: number;
  completedDocuments: number;
  errorDocuments: number;
  storageUsed: number;
  storageLimit: number;
}

class DocumentService {
  // Get paginated list of documents with filtering
  async getDocuments(params: {
    page?: number;
    limit?: number;
    filter?: DocumentFilter;
    sort?: string;
    order?: 'asc' | 'desc';
  } = {}): Promise<DocumentsResponse> {
    const response = await apiClient.get<DocumentsResponse>('/documents', params);
    return response.data;
  }

  // Get a single document by ID
  async getDocument(id: string): Promise<Document> {
    const response = await apiClient.get<Document>(`/documents/${id}`);
    return response.data;
  }

  // Upload a new document
  async uploadDocument(
    upload: DocumentUpload,
    onProgress?: (progress: number) => void
  ): Promise<Document> {
    const formData = new FormData();
    formData.append('file', upload.file);
    
    if (upload.title) {
      formData.append('title', upload.title);
    }
    
    if (upload.tags && upload.tags.length > 0) {
      formData.append('tags', JSON.stringify(upload.tags));
    }

    const response = await apiClient.upload<Document>('/documents/upload', formData, onProgress);
    return response.data;
  }

  // Upload multiple documents
  async uploadDocuments(
    uploads: DocumentUpload[],
    onProgress?: (fileIndex: number, progress: number) => void
  ): Promise<Document[]> {
    const results: Document[] = [];
    
    for (let i = 0; i < uploads.length; i++) {
      const upload = uploads[i];
      const document = await this.uploadDocument(upload, (progress) => {
        if (onProgress) {
          onProgress(i, progress);
        }
      });
      results.push(document);
    }
    
    return results;
  }

  // Update document metadata
  async updateDocument(id: string, data: Partial<Document>): Promise<Document> {
    const response = await apiClient.patch<Document>(`/documents/${id}`, data);
    return response.data;
  }

  // Delete a document
  async deleteDocument(id: string): Promise<void> {
    await apiClient.delete(`/documents/${id}`);
  }

  // Delete multiple documents
  async deleteDocuments(ids: string[]): Promise<void> {
    await apiClient.post('/documents/bulk-delete', { ids });
  }

  // Download a document
  async downloadDocument(id: string, filename?: string): Promise<void> {
    await apiClient.download(`/documents/${id}/download`, filename);
  }

  // Get document content as text
  async getDocumentContent(id: string): Promise<string> {
    const response = await apiClient.get<{ content: string }>(`/documents/${id}/content`);
    return response.data.content;
  }

  // Search documents
  async searchDocuments(query: string, filters?: DocumentFilter): Promise<Document[]> {
    const response = await apiClient.get<Document[]>('/documents/search', { 
      q: query,
      ...filters 
    });
    return response.data;
  }

  // Get document processing status
  async getProcessingStatus(id: string): Promise<{
    status: Document['status'];
    progress: number;
    message?: string;
  }> {
    const response = await apiClient.get<{
      status: Document['status'];
      progress: number;
      message?: string;
    }>(`/documents/${id}/status`);
    return response.data;
  }

  // Reprocess a document
  async reprocessDocument(id: string): Promise<Document> {
    const response = await apiClient.post<Document>(`/documents/${id}/reprocess`);
    return response.data;
  }

  // Get document statistics
  async getDocumentStats(): Promise<DocumentStats> {
    const response = await apiClient.get<DocumentStats>('/documents/stats');
    return response.data;
  }

  // Get document tags (all unique tags)
  async getDocumentTags(): Promise<string[]> {
    const response = await apiClient.get<string[]>('/documents/tags');
    return response.data;
  }

  // Add tags to a document
  async addDocumentTags(id: string, tags: string[]): Promise<Document> {
    const response = await apiClient.post<Document>(`/documents/${id}/tags`, { tags });
    return response.data;
  }

  // Remove tags from a document
  async removeDocumentTags(id: string, tags: string[]): Promise<Document> {
    const response = await apiClient.delete<Document>(`/documents/${id}/tags`, { data: { tags } });
    return response.data;
  }

  // Get document versions
  async getDocumentVersions(id: string): Promise<Document[]> {
    const response = await apiClient.get<Document[]>(`/documents/${id}/versions`);
    return response.data;
  }

  // Restore document to specific version
  async restoreDocumentVersion(id: string, version: number): Promise<Document> {
    const response = await apiClient.post<Document>(`/documents/${id}/versions/${version}/restore`);
    return response.data;
  }

  // Get documents by status
  async getDocumentsByStatus(status: Document['status']): Promise<Document[]> {
    const response = await apiClient.get<Document[]>('/documents', { filter: { status } });
    return response.data;
  }

  // Get recent documents
  async getRecentDocuments(limit: number = 10): Promise<Document[]> {
    const response = await apiClient.get<Document[]>('/documents/recent', { limit });
    return response.data;
  }

  // Export documents as ZIP
  async exportDocuments(ids: string[]): Promise<void> {
    await apiClient.download('/documents/export', 'documents.zip', { ids });
  }

  // Get document analytics
  async getDocumentAnalytics(dateRange?: { start: string; end: string }) {
    const response = await apiClient.get('/documents/analytics', dateRange);
    return response.data;
  }

  // Share document (generate shareable link)
  async shareDocument(id: string, options: {
    expiresAt?: string;
    password?: string;
    downloadEnabled?: boolean;
  } = {}): Promise<{ shareUrl: string; token: string }> {
    const response = await apiClient.post<{ shareUrl: string; token: string }>(
      `/documents/${id}/share`,
      options
    );
    return response.data;
  }

  // Get shared document (public endpoint)
  async getSharedDocument(token: string): Promise<Document> {
    const response = await apiClient.get<Document>(`/public/documents/${token}`);
    return response.data;
  }
}

export const documentService = new DocumentService();
export default documentService;

