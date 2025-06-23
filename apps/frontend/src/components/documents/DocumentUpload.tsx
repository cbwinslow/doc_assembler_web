import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CloudArrowUpIcon,
  DocumentTextIcon,
  PhotoIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { Button } from '../ui/Button';
import { Modal } from '../ui/Modal';
import { cn } from '../../utils/cn';
import { apiClient, endpoints } from '../../services/api';
import { notify } from '../../stores/notificationStore';

interface UploadFile extends File {
  id: string;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
}

interface ProcessingOptions {
  extractText: boolean;
  generateEmbeddings: boolean;
  classify: boolean;
  summarize: boolean;
  enableOCR: boolean;
  priority: number;
}

export const DocumentUpload: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [options, setOptions] = useState<ProcessingOptions>({
    extractText: true,
    generateEmbeddings: true,
    classify: false,
    summarize: false,
    enableOCR: true,
    priority: 5,
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadFile[] = acceptedFiles.map((file) => ({
      ...file,
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      progress: 0,
      status: 'pending',
    }));

    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'],
    },
    maxFileSize: 50 * 1024 * 1024, // 50MB
  });

  const removeFile = (fileId: string) => {
    setFiles((prev) => prev.filter((file) => file.id !== fileId));
  };

  const uploadFile = async (file: UploadFile) => {
    setFiles((prev) =>
      prev.map((f) =>
        f.id === file.id ? { ...f, status: 'uploading', progress: 0 } : f
      )
    );

    try {
      // Create FormData with processing options
      const formData = new FormData();
      formData.append('file', file);
      formData.append('options', JSON.stringify(options));

      const response = await apiClient.upload(endpoints.documents.upload, file, formData);

      if (response.success) {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id ? { ...f, status: 'completed', progress: 100 } : f
          )
        );

        notify.success('Upload Complete', `${file.name} has been uploaded and queued for processing.`);
      } else {
        throw new Error(response.error || 'Upload failed');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      
      setFiles((prev) =>
        prev.map((f) =>
          f.id === file.id
            ? { ...f, status: 'error', error: errorMessage }
            : f
        )
      );

      notify.error('Upload Failed', `Failed to upload ${file.name}: ${errorMessage}`);
    }
  };

  const uploadAllFiles = async () => {
    const pendingFiles = files.filter((file) => file.status === 'pending');
    
    for (const file of pendingFiles) {
      await uploadFile(file);
      // Small delay between uploads to avoid overwhelming the server
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return PhotoIcon;
    }
    return DocumentTextIcon;
  };

  const getStatusColor = (status: UploadFile['status']) => {
    switch (status) {
      case 'completed':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      case 'uploading':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: UploadFile['status']) => {
    switch (status) {
      case 'completed':
        return CheckCircleIcon;
      case 'error':
        return ExclamationTriangleIcon;
      default:
        return null;
    }
  };

  return (
    <>
      <Button onClick={() => setIsOpen(true)} className="flex items-center">
        <CloudArrowUpIcon className="h-5 w-5 mr-2" />
        Upload Documents
      </Button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Upload Documents"
        size="lg"
      >
        <div className="space-y-6">
          {/* Dropzone */}
          <div
            {...getRootProps()}
            className={cn(
              'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
              isDragActive
                ? 'border-blue-400 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            )}
          >
            <input {...getInputProps()} />
            <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600">
              {isDragActive
                ? 'Drop the files here...'
                : 'Drag & drop files here, or click to select files'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Supports PDF, DOC, DOCX, TXT, MD, and image files (max 50MB)
            </p>
          </div>

          {/* Processing Options */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Processing Options</h4>
            <div className="grid grid-cols-2 gap-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={options.extractText}
                  onChange={(e) =>
                    setOptions((prev) => ({ ...prev, extractText: e.target.checked }))
                  }
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">Extract Text</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={options.generateEmbeddings}
                  onChange={(e) =>
                    setOptions((prev) => ({ ...prev, generateEmbeddings: e.target.checked }))
                  }
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">Generate Embeddings</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={options.classify}
                  onChange={(e) =>
                    setOptions((prev) => ({ ...prev, classify: e.target.checked }))
                  }
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">Classify Document</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={options.summarize}
                  onChange={(e) =>
                    setOptions((prev) => ({ ...prev, summarize: e.target.checked }))
                  }
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">Generate Summary</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={options.enableOCR}
                  onChange={(e) =>
                    setOptions((prev) => ({ ...prev, enableOCR: e.target.checked }))
                  }
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">Enable OCR</span>
              </label>

              <div className="flex items-center">
                <label className="text-sm text-gray-700 mr-2">Priority:</label>
                <select
                  value={options.priority}
                  onChange={(e) =>
                    setOptions((prev) => ({ ...prev, priority: Number(e.target.value) }))
                  }
                  className="text-sm border-gray-300 rounded-md"
                >
                  <option value={1}>High</option>
                  <option value={5}>Normal</option>
                  <option value={10}>Low</option>
                </select>
              </div>
            </div>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-900">Files to Upload</h4>
              <div className="max-h-48 overflow-y-auto space-y-2">
                <AnimatePresence>
                  {files.map((file) => {
                    const FileIcon = getFileIcon(file);
                    const StatusIcon = getStatusIcon(file.status);

                    return (
                      <motion.div
                        key={file.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="flex items-center justify-between p-3 bg-white border rounded-lg"
                      >
                        <div className="flex items-center space-x-3">
                          <FileIcon className="h-6 w-6 text-gray-400" />
                          <div>
                            <p className="text-sm font-medium text-gray-900">{file.name}</p>
                            <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                          </div>
                        </div>

                        <div className="flex items-center space-x-3">
                          {file.status === 'uploading' && (
                            <div className="w-16 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full transition-all"
                                style={{ width: `${file.progress}%` }}
                              />
                            </div>
                          )}

                          {StatusIcon && (
                            <StatusIcon className={cn('h-5 w-5', getStatusColor(file.status))} />
                          )}

                          {file.status === 'error' && file.error && (
                            <p className="text-xs text-red-600">{file.error}</p>
                          )}

                          <button
                            onClick={() => removeFile(file.id)}
                            className="text-gray-400 hover:text-gray-600"
                            disabled={file.status === 'uploading'}
                          >
                            <XMarkIcon className="h-5 w-5" />
                          </button>
                        </div>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-3">
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            {files.length > 0 && (
              <Button
                onClick={uploadAllFiles}
                disabled={files.every((f) => f.status !== 'pending')}
              >
                Upload All Files
              </Button>
            )}
          </div>
        </div>
      </Modal>
    </>
  );
};

