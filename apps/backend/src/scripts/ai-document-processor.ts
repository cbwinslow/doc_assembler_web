#!/usr/bin/env node

/**
 * AI Document Processing Script
 * 
 * This script provides a command-line interface for processing documents
 * using the AI document processing pipeline. It can be used for batch
 * processing, testing, or integration with external systems.
 */

import { Command } from 'commander';
import { PrismaClient } from '@prisma/client';
import { existsSync, statSync } from 'fs';
import { readdir } from 'fs/promises';
import { join, extname, basename } from 'path';
import { logger } from '@/utils/logger.js';
import { documentProcessor, ProcessingOptions } from '@/services/documentProcessor.js';
import { queueService } from '@/services/queueService.js';
import { vectorService } from '@/services/vectorService.js';
import { emailService } from '@/services/emailService.js';

const prisma = new PrismaClient();
const program = new Command();

// Supported file extensions
const SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.doc', '.txt', '.md', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'];

interface ProcessingStats {
  totalFiles: number;
  processed: number;
  failed: number;
  skipped: number;
  startTime: Date;
  endTime?: Date;
  errors: Array<{ file: string; error: string }>;
}

/**
 * Process a single document
 */
async function processSingleDocument(filePath: string, options: ProcessingOptions): Promise<{
  success: boolean;
  documentId?: string;
  error?: string;
}> {
  try {
    // Check if file exists
    if (!existsSync(filePath)) {
      throw new Error(`File not found: ${filePath}`);
    }

    // Check file extension
    const ext = extname(filePath).toLowerCase();
    if (!SUPPORTED_EXTENSIONS.includes(ext)) {
      throw new Error(`Unsupported file type: ${ext}`);
    }

    // Create document record
    const document = await prisma.document.create({
      data: {
        filename: basename(filePath),
        originalName: basename(filePath),
        size: statSync(filePath).size,
        mimeType: getMimeType(ext),
        status: 'PENDING',
        metadata: {
          source: 'cli-script',
          processedAt: new Date().toISOString(),
        }
      }
    });

    logger.info(`Processing document: ${filePath}`, {
      documentId: document.id,
      filename: document.filename,
      size: document.size
    });

    // Process the document
    const result = await documentProcessor.processDocument(document.id, filePath, options);

    if (result.success) {
      logger.info(`Document processed successfully: ${filePath}`, {
        documentId: document.id,
        processingTime: result.processingTime,
        textLength: result.extractedText?.length || 0,
        embeddingsGenerated: !!result.embeddings
      });

      return {
        success: true,
        documentId: document.id
      };
    } else {
      logger.error(`Document processing failed: ${filePath}`, {
        documentId: document.id,
        error: result.error
      });

      return {
        success: false,
        documentId: document.id,
        error: result.error
      };
    }

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    logger.error(`Failed to process document: ${filePath}`, { error: errorMessage });
    
    return {
      success: false,
      error: errorMessage
    };
  }
}

/**
 * Process multiple documents in a directory
 */
async function processDirectory(
  dirPath: string, 
  options: ProcessingOptions,
  recursive: boolean = false,
  maxConcurrency: number = 3
): Promise<ProcessingStats> {
  const stats: ProcessingStats = {
    totalFiles: 0,
    processed: 0,
    failed: 0,
    skipped: 0,
    startTime: new Date(),
    errors: []
  };

  try {
    // Get all files in directory
    const files = await getFilesInDirectory(dirPath, recursive);
    
    // Filter supported files
    const supportedFiles = files.filter(file => {
      const ext = extname(file).toLowerCase();
      return SUPPORTED_EXTENSIONS.includes(ext);
    });

    stats.totalFiles = supportedFiles.length;

    if (stats.totalFiles === 0) {
      logger.warn(`No supported files found in directory: ${dirPath}`);
      return stats;
    }

    logger.info(`Found ${stats.totalFiles} supported files in ${dirPath}`);

    // Process files with concurrency control
    const semaphore = new Array(maxConcurrency).fill(null);
    const processQueue = [...supportedFiles];

    const processFile = async (): Promise<void> => {
      while (processQueue.length > 0) {
        const filePath = processQueue.shift();
        if (!filePath) break;

        try {
          const result = await processSingleDocument(filePath, options);
          
          if (result.success) {
            stats.processed++;
          } else {
            stats.failed++;
            stats.errors.push({
              file: filePath,
              error: result.error || 'Unknown error'
            });
          }
        } catch (error) {
          stats.failed++;
          stats.errors.push({
            file: filePath,
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }

        // Progress update
        const completed = stats.processed + stats.failed + stats.skipped;
        logger.info(`Progress: ${completed}/${stats.totalFiles} files processed`);
      }
    };

    // Start concurrent processing
    await Promise.all(semaphore.map(() => processFile()));

    stats.endTime = new Date();

    logger.info('Directory processing completed', {
      totalFiles: stats.totalFiles,
      processed: stats.processed,
      failed: stats.failed,
      skipped: stats.skipped,
      duration: stats.endTime.getTime() - stats.startTime.getTime(),
      errors: stats.errors.length
    });

    return stats;

  } catch (error) {
    stats.endTime = new Date();
    logger.error(`Failed to process directory: ${dirPath}`, { error });
    throw error;
  }
}

/**
 * Get all files in directory (optionally recursive)
 */
async function getFilesInDirectory(dirPath: string, recursive: boolean): Promise<string[]> {
  const files: string[] = [];
  
  const items = await readdir(dirPath, { withFileTypes: true });
  
  for (const item of items) {
    const fullPath = join(dirPath, item.name);
    
    if (item.isFile()) {
      files.push(fullPath);
    } else if (item.isDirectory() && recursive) {
      const subFiles = await getFilesInDirectory(fullPath, recursive);
      files.push(...subFiles);
    }
  }
  
  return files;
}

/**
 * Get MIME type from file extension
 */
function getMimeType(ext: string): string {
  const mimeTypes: Record<string, string> = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc': 'application/msword',
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.bmp': 'image/bmp',
    '.tiff': 'image/tiff',
  };
  
  return mimeTypes[ext.toLowerCase()] || 'application/octet-stream';
}

/**
 * Queue processing job
 */
async function queueProcessingJob(filePath: string, options: ProcessingOptions, priority: number = 5): Promise<void> {
  try {
    if (!existsSync(filePath)) {
      throw new Error(`File not found: ${filePath}`);
    }

    // Create document record
    const document = await prisma.document.create({
      data: {
        filename: basename(filePath),
        originalName: basename(filePath),
        size: statSync(filePath).size,
        mimeType: getMimeType(extname(filePath)),
        status: 'QUEUED',
        metadata: {
          source: 'cli-script',
          queuedAt: new Date().toISOString(),
        }
      }
    });

    // Add to queue
    const job = await queueService.addDocumentProcessingJob(
      {
        documentId: document.id,
        filePath,
        options
      },
      priority
    );

    logger.info(`Document queued for processing`, {
      documentId: document.id,
      jobId: job.id,
      priority,
      filename: basename(filePath)
    });

  } catch (error) {
    logger.error(`Failed to queue document: ${filePath}`, { error });
    throw error;
  }
}

/**
 * Test document processing pipeline
 */
async function testPipeline(): Promise<void> {
  logger.info('Testing document processing pipeline...');

  try {
    // Test vector service
    logger.info('Testing vector service...');
    const testEmbedding = await vectorService.generateEmbedding('This is a test document for pipeline testing.');
    logger.info(`Vector service test passed. Embedding dimensions: ${testEmbedding.length}`);

    // Test email service
    logger.info('Testing email service...');
    const emailStatus = await emailService.testConnection();
    if (emailStatus.success) {
      logger.info('Email service test passed');
    } else {
      logger.warn('Email service test failed:', emailStatus.error);
    }

    // Test queue service
    logger.info('Testing queue service...');
    const queueHealth = await queueService.getHealthStatus();
    logger.info('Queue service status:', queueHealth);

    logger.info('Pipeline test completed successfully');

  } catch (error) {
    logger.error('Pipeline test failed:', error);
    throw error;
  }
}

/**
 * Show processing statistics
 */
async function showStats(): Promise<void> {
  try {
    // Document statistics
    const documentStats = await prisma.document.groupBy({
      by: ['status'],
      _count: {
        status: true
      }
    });

    // Processing job statistics
    const jobStats = await prisma.processingJob.groupBy({
      by: ['status'],
      _count: {
        status: true
      }
    });

    // Queue statistics
    const queueStats = await queueService.getQueueStats();

    logger.info('Document Processing Statistics', {
      documents: documentStats.reduce((acc, stat) => {
        acc[stat.status] = stat._count.status;
        return acc;
      }, {} as Record<string, number>),
      
      processingJobs: jobStats.reduce((acc, stat) => {
        acc[stat.status] = stat._count.status;
        return acc;
      }, {} as Record<string, number>),
      
      queues: queueStats
    });

  } catch (error) {
    logger.error('Failed to get statistics:', error);
    throw error;
  }
}

// CLI Commands
program
  .name('ai-document-processor')
  .description('AI Document Processing CLI')
  .version('1.0.0');

program
  .command('process')
  .description('Process a single document or directory')
  .argument('<path>', 'File or directory path to process')
  .option('-r, --recursive', 'Process directories recursively', false)
  .option('-c, --concurrency <number>', 'Maximum concurrent processing jobs', '3')
  .option('--extract-text', 'Extract text from documents', true)
  .option('--generate-embeddings', 'Generate vector embeddings', true)
  .option('--classify', 'Classify documents', false)
  .option('--summarize', 'Generate document summaries', false)
  .option('--ocr', 'Enable OCR for images', true)
  .option('--notify-email <email>', 'Send notification email when complete')
  .action(async (path: string, options) => {
    try {
      const processingOptions: ProcessingOptions = {
        extractText: options.extractText,
        generateEmbeddings: options.generateEmbeddings,
        classify: options.classify,
        summarize: options.summarize,
        enableOCR: options.ocr,
      };

      const stats = existsSync(path) && statSync(path).isDirectory()
        ? await processDirectory(path, processingOptions, options.recursive, parseInt(options.concurrency))
        : await processSingleDocument(path, processingOptions).then(result => ({
            totalFiles: 1,
            processed: result.success ? 1 : 0,
            failed: result.success ? 0 : 1,
            skipped: 0,
            startTime: new Date(),
            endTime: new Date(),
            errors: result.success ? [] : [{ file: path, error: result.error || 'Unknown error' }]
          } as ProcessingStats));

      // Send notification email if requested
      if (options.notifyEmail && stats.endTime) {
        await emailService.sendNotificationEmail(options.notifyEmail, {
          subject: 'Document Processing Complete',
          title: 'Processing Results',
          message: `Processed ${stats.processed}/${stats.totalFiles} documents successfully. ${stats.failed} failed.`,
          actionUrl: 'http://localhost:3000/documents',
          actionText: 'View Documents'
        });
      }

      process.exit(stats.failed > 0 ? 1 : 0);

    } catch (error) {
      logger.error('Processing failed:', error);
      process.exit(1);
    }
  });

program
  .command('queue')
  .description('Queue documents for background processing')
  .argument('<path>', 'File or directory path to queue')
  .option('-p, --priority <number>', 'Processing priority (1-10)', '5')
  .option('-r, --recursive', 'Queue directories recursively', false)
  .option('--extract-text', 'Extract text from documents', true)
  .option('--generate-embeddings', 'Generate vector embeddings', true)
  .option('--classify', 'Classify documents', false)
  .option('--summarize', 'Generate document summaries', false)
  .option('--ocr', 'Enable OCR for images', true)
  .action(async (path: string, options) => {
    try {
      const processingOptions: ProcessingOptions = {
        extractText: options.extractText,
        generateEmbeddings: options.generateEmbeddings,
        classify: options.classify,
        summarize: options.summarize,
        enableOCR: options.ocr,
      };

      const priority = parseInt(options.priority);

      if (existsSync(path) && statSync(path).isDirectory()) {
        const files = await getFilesInDirectory(path, options.recursive);
        const supportedFiles = files.filter(file => {
          const ext = extname(file).toLowerCase();
          return SUPPORTED_EXTENSIONS.includes(ext);
        });

        for (const filePath of supportedFiles) {
          await queueProcessingJob(filePath, processingOptions, priority);
        }

        logger.info(`Queued ${supportedFiles.length} files for processing`);
      } else {
        await queueProcessingJob(path, processingOptions, priority);
        logger.info('File queued for processing');
      }

    } catch (error) {
      logger.error('Queueing failed:', error);
      process.exit(1);
    }
  });

program
  .command('status')
  .description('Show queue and processing status')
  .action(async () => {
    try {
      await showStats();
    } catch (error) {
      logger.error('Failed to get status:', error);
      process.exit(1);
    }
  });

program
  .command('test')
  .description('Test the document processing pipeline')
  .action(async () => {
    try {
      await testPipeline();
      logger.info('All tests passed');
    } catch (error) {
      logger.error('Tests failed:', error);
      process.exit(1);
    }
  });

program
  .command('cleanup')
  .description('Clean up old jobs and temporary files')
  .option('--older-than <hours>', 'Clean jobs older than specified hours', '24')
  .action(async (options) => {
    try {
      const olderThan = parseInt(options.olderThan) * 60 * 60 * 1000; // Convert to milliseconds
      await queueService.cleanupOldJobs(olderThan);
      
      // Clean up temporary processing files (implement as needed)
      logger.info('Cleanup completed');
      
    } catch (error) {
      logger.error('Cleanup failed:', error);
      process.exit(1);
    }
  });

// Error handling
process.on('uncaughtException', (error) => {
  logger.error('Uncaught exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', async () => {
  logger.info('Received SIGINT, shutting down gracefully...');
  
  try {
    await queueService.shutdown();
    await emailService.shutdown();
    await prisma.$disconnect();
    
    logger.info('Graceful shutdown completed');
    process.exit(0);
    
  } catch (error) {
    logger.error('Error during shutdown:', error);
    process.exit(1);
  }
});

process.on('SIGTERM', async () => {
  logger.info('Received SIGTERM, shutting down gracefully...');
  
  try {
    await queueService.shutdown();
    await emailService.shutdown();
    await prisma.$disconnect();
    
    logger.info('Graceful shutdown completed');
    process.exit(0);
    
  } catch (error) {
    logger.error('Error during shutdown:', error);
    process.exit(1);
  }
});

// Parse command line arguments
program.parse();

