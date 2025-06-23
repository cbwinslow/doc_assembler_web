import Bull from 'bull';
import { PrismaClient } from '@prisma/client';
import { logger } from '@/utils/logger.js';
import { config } from '@/config/config.js';
import { documentProcessor, ProcessingOptions } from './documentProcessor.js';

const prisma = new PrismaClient();

export interface DocumentProcessingJob {
  documentId: string;
  filePath: string;
  options: ProcessingOptions;
}

export interface EmailJob {
  to: string;
  subject: string;
  template: string;
  data: Record<string, any>;
}

export interface WebhookJob {
  url: string;
  payload: Record<string, any>;
  headers?: Record<string, string>;
  retries?: number;
}

export class QueueService {
  private documentQueue: Bull.Queue<DocumentProcessingJob>;
  private emailQueue: Bull.Queue<EmailJob>;
  private webhookQueue: Bull.Queue<WebhookJob>;

  constructor() {
    const redisConfig = {
      host: config.REDIS_URL.includes('://') 
        ? new URL(config.REDIS_URL).hostname 
        : config.REDIS_URL.split(':')[0],
      port: config.REDIS_URL.includes('://') 
        ? Number(new URL(config.REDIS_URL).port) || 6379
        : Number(config.REDIS_URL.split(':')[1]) || 6379,
      maxRetriesPerRequest: 3,
      retryDelayOnFailover: 100,
      connectTimeout: 10000,
      commandTimeout: 5000,
    };

    // Initialize queues
    this.documentQueue = new Bull('document-processing', {
      redis: redisConfig,
      defaultJobOptions: {
        removeOnComplete: 100,
        removeOnFail: 50,
        attempts: 3,
        backoff: {
          type: 'exponential',
          delay: 2000,
        },
      },
    });

    this.emailQueue = new Bull('email-sending', {
      redis: redisConfig,
      defaultJobOptions: {
        removeOnComplete: 50,
        removeOnFail: 20,
        attempts: 5,
        backoff: {
          type: 'exponential',
          delay: 3000,
        },
      },
    });

    this.webhookQueue = new Bull('webhook-delivery', {
      redis: redisConfig,
      defaultJobOptions: {
        removeOnComplete: 50,
        removeOnFail: 30,
        attempts: 3,
        backoff: {
          type: 'exponential',
          delay: 1000,
        },
      },
    });

    this.setupProcessors();
    this.setupEventListeners();
  }

  /**
   * Setup queue processors
   */
  private setupProcessors(): void {
    // Document processing processor
    this.documentQueue.process('process-document', 5, async (job) => {
      const { documentId, filePath, options } = job.data;
      
      logger.info(`Processing document job for ${documentId}`, {
        jobId: job.id,
        documentId,
        options
      });

      try {
        // Create processing job record
        const processingJob = await prisma.processingJob.create({
          data: {
            documentId,
            type: 'TEXT_EXTRACTION',
            status: 'IN_PROGRESS',
            input: options,
            queueId: job.id.toString(),
            priority: job.opts.priority || 5,
          }
        });

        // Update progress
        await job.progress(10);

        // Process the document
        const result = await documentProcessor.processDocument(documentId, filePath, options);

        // Update progress
        await job.progress(90);

        // Update processing job record
        await prisma.processingJob.update({
          where: { id: processingJob.id },
          data: {
            status: result.success ? 'COMPLETED' : 'FAILED',
            output: result,
            error: result.error,
            progress: 100,
            completedAt: result.success ? new Date() : undefined,
            failedAt: result.success ? undefined : new Date(),
          }
        });

        // Complete the job
        await job.progress(100);

        // Cleanup temporary files
        await documentProcessor.cleanup(filePath);

        logger.info(`Document processing job completed for ${documentId}`, {
          jobId: job.id,
          processingTime: result.processingTime,
          success: result.success
        });

        return result;

      } catch (error) {
        logger.error(`Document processing job failed for ${documentId}:`, error);
        
        // Update processing job record
        await prisma.processingJob.updateMany({
          where: { queueId: job.id.toString() },
          data: {
            status: 'FAILED',
            error: error instanceof Error ? error.message : 'Unknown error',
            failedAt: new Date(),
          }
        });

        throw error;
      }
    });

    // Email processor
    this.emailQueue.process('send-email', 3, async (job) => {
      const { to, subject, template, data } = job.data;
      
      logger.info(`Processing email job`, {
        jobId: job.id,
        to,
        subject,
        template
      });

      try {
        // Import email service dynamically
        const { emailService } = await import('./emailService.js');
        
        await emailService.sendEmail({
          to,
          subject,
          template,
          data
        });

        logger.info(`Email sent successfully`, {
          jobId: job.id,
          to,
          subject
        });

      } catch (error) {
        logger.error(`Email sending failed:`, error);
        throw error;
      }
    });

    // Webhook processor
    this.webhookQueue.process('deliver-webhook', 5, async (job) => {
      const { url, payload, headers = {}, retries = 3 } = job.data;
      
      logger.info(`Processing webhook delivery`, {
        jobId: job.id,
        url,
        attempt: job.attemptsMade + 1
      });

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'User-Agent': 'DocAssembler-Webhook/1.0',
            ...headers
          },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          throw new Error(`Webhook delivery failed: ${response.status} ${response.statusText}`);
        }

        logger.info(`Webhook delivered successfully`, {
          jobId: job.id,
          url,
          status: response.status
        });

        return {
          success: true,
          status: response.status,
          response: await response.text()
        };

      } catch (error) {
        logger.error(`Webhook delivery failed:`, error);
        throw error;
      }
    });
  }

  /**
   * Setup event listeners for monitoring
   */
  private setupEventListeners(): void {
    // Document queue events
    this.documentQueue.on('completed', (job, result) => {
      logger.info(`Document processing job completed`, {
        jobId: job.id,
        documentId: job.data.documentId,
        processingTime: result.processingTime
      });
    });

    this.documentQueue.on('failed', (job, err) => {
      logger.error(`Document processing job failed`, {
        jobId: job.id,
        documentId: job.data.documentId,
        error: err.message,
        attempts: job.attemptsMade
      });
    });

    this.documentQueue.on('stalled', (job) => {
      logger.warn(`Document processing job stalled`, {
        jobId: job.id,
        documentId: job.data.documentId
      });
    });

    // Email queue events
    this.emailQueue.on('completed', (job) => {
      logger.info(`Email job completed`, {
        jobId: job.id,
        to: job.data.to
      });
    });

    this.emailQueue.on('failed', (job, err) => {
      logger.error(`Email job failed`, {
        jobId: job.id,
        to: job.data.to,
        error: err.message
      });
    });

    // Webhook queue events
    this.webhookQueue.on('completed', (job) => {
      logger.info(`Webhook job completed`, {
        jobId: job.id,
        url: job.data.url
      });
    });

    this.webhookQueue.on('failed', (job, err) => {
      logger.error(`Webhook job failed`, {
        jobId: job.id,
        url: job.data.url,
        error: err.message
      });
    });
  }

  /**
   * Add document processing job to queue
   */
  async addDocumentProcessingJob(
    data: DocumentProcessingJob,
    priority: number = 5,
    delay?: number
  ): Promise<Bull.Job<DocumentProcessingJob>> {
    const job = await this.documentQueue.add('process-document', data, {
      priority,
      delay,
      attempts: 3,
      backoff: {
        type: 'exponential',
        delay: 2000,
      },
    });

    logger.info(`Added document processing job to queue`, {
      jobId: job.id,
      documentId: data.documentId,
      priority,
      delay
    });

    return job;
  }

  /**
   * Add email job to queue
   */
  async addEmailJob(
    data: EmailJob,
    delay?: number
  ): Promise<Bull.Job<EmailJob>> {
    const job = await this.emailQueue.add('send-email', data, {
      delay,
      attempts: 5,
      backoff: {
        type: 'exponential',
        delay: 3000,
      },
    });

    logger.info(`Added email job to queue`, {
      jobId: job.id,
      to: data.to,
      subject: data.subject,
      delay
    });

    return job;
  }

  /**
   * Add webhook job to queue
   */
  async addWebhookJob(
    data: WebhookJob,
    delay?: number
  ): Promise<Bull.Job<WebhookJob>> {
    const job = await this.webhookQueue.add('deliver-webhook', data, {
      delay,
      attempts: data.retries || 3,
      backoff: {
        type: 'exponential',
        delay: 1000,
      },
    });

    logger.info(`Added webhook job to queue`, {
      jobId: job.id,
      url: data.url,
      delay
    });

    return job;
  }

  /**
   * Get job status and progress
   */
  async getJobStatus(jobId: string, queueName: 'document' | 'email' | 'webhook') {
    let queue: Bull.Queue;
    
    switch (queueName) {
      case 'document':
        queue = this.documentQueue;
        break;
      case 'email':
        queue = this.emailQueue;
        break;
      case 'webhook':
        queue = this.webhookQueue;
        break;
      default:
        throw new Error(`Unknown queue: ${queueName}`);
    }

    const job = await queue.getJob(jobId);
    
    if (!job) {
      return null;
    }

    return {
      id: job.id,
      data: job.data,
      progress: job.progress(),
      state: await job.getState(),
      attemptsMade: job.attemptsMade,
      finishedOn: job.finishedOn,
      processedOn: job.processedOn,
      failedReason: job.failedReason,
    };
  }

  /**
   * Get queue statistics
   */
  async getQueueStats() {
    const [documentStats, emailStats, webhookStats] = await Promise.all([
      this.getQueueInfo(this.documentQueue),
      this.getQueueInfo(this.emailQueue),
      this.getQueueInfo(this.webhookQueue),
    ]);

    return {
      document: documentStats,
      email: emailStats,
      webhook: webhookStats,
    };
  }

  /**
   * Get information about a specific queue
   */
  private async getQueueInfo(queue: Bull.Queue) {
    const [waiting, active, completed, failed, delayed] = await Promise.all([
      queue.getWaiting(),
      queue.getActive(),
      queue.getCompleted(),
      queue.getFailed(),
      queue.getDelayed(),
    ]);

    return {
      waiting: waiting.length,
      active: active.length,
      completed: completed.length,
      failed: failed.length,
      delayed: delayed.length,
      total: waiting.length + active.length + completed.length + failed.length + delayed.length,
    };
  }

  /**
   * Clean up old jobs
   */
  async cleanupOldJobs(olderThan: number = 24 * 60 * 60 * 1000): Promise<void> {
    try {
      const cleanupPromises = [
        this.documentQueue.clean(olderThan, 'completed'),
        this.documentQueue.clean(olderThan, 'failed'),
        this.emailQueue.clean(olderThan, 'completed'),
        this.emailQueue.clean(olderThan, 'failed'),
        this.webhookQueue.clean(olderThan, 'completed'),
        this.webhookQueue.clean(olderThan, 'failed'),
      ];

      const results = await Promise.all(cleanupPromises);
      const totalCleaned = results.reduce((sum, jobs) => sum + jobs.length, 0);

      logger.info(`Cleaned up ${totalCleaned} old jobs`, {
        olderThan: `${olderThan}ms`,
        cleanedByQueue: {
          document: results[0].length + results[1].length,
          email: results[2].length + results[3].length,
          webhook: results[4].length + results[5].length,
        }
      });

    } catch (error) {
      logger.error('Failed to cleanup old jobs:', error);
    }
  }

  /**
   * Pause all queues
   */
  async pauseAllQueues(): Promise<void> {
    await Promise.all([
      this.documentQueue.pause(),
      this.emailQueue.pause(),
      this.webhookQueue.pause(),
    ]);

    logger.info('All queues paused');
  }

  /**
   * Resume all queues
   */
  async resumeAllQueues(): Promise<void> {
    await Promise.all([
      this.documentQueue.resume(),
      this.emailQueue.resume(),
      this.webhookQueue.resume(),
    ]);

    logger.info('All queues resumed');
  }

  /**
   * Get queue health status
   */
  async getHealthStatus() {
    try {
      const stats = await this.getQueueStats();
      const isHealthy = Object.values(stats).every(queueStats => 
        queueStats.failed < 10 && queueStats.active < 100
      );

      return {
        status: isHealthy ? 'healthy' : 'degraded',
        stats,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      };
    }
  }

  /**
   * Graceful shutdown
   */
  async shutdown(): Promise<void> {
    logger.info('Shutting down queue service...');

    try {
      // Wait for active jobs to complete (with timeout)
      await Promise.race([
        Promise.all([
          this.documentQueue.close(),
          this.emailQueue.close(),
          this.webhookQueue.close(),
        ]),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Queue shutdown timeout')), 30000)
        )
      ]);

      logger.info('Queue service shutdown completed');
    } catch (error) {
      logger.error('Error during queue service shutdown:', error);
      throw error;
    }
  }
}

export const queueService = new QueueService();

