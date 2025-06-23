import nodemailer from 'nodemailer';
import { readFile } from 'fs/promises';
import { join } from 'path';
import Handlebars from 'handlebars';
import { logger } from '@/utils/logger.js';
import { config } from '@/config/config.js';

export interface EmailOptions {
  to: string | string[];
  cc?: string | string[];
  bcc?: string | string[];
  subject: string;
  template?: string;
  html?: string;
  text?: string;
  data?: Record<string, any>;
  attachments?: Array<{
    filename: string;
    path?: string;
    content?: Buffer | string;
    contentType?: string;
  }>;
}

export interface EmailTemplate {
  name: string;
  subject: string;
  html: string;
  text?: string;
}

export class EmailService {
  private transporter: nodemailer.Transporter;
  private templates: Map<string, EmailTemplate> = new Map();
  private isInitialized = false;

  constructor() {
    this.initializeTransporter();
    this.loadTemplates();
  }

  /**
   * Initialize email transporter based on environment
   */
  private initializeTransporter(): void {
    try {
      if (config.NODE_ENV === 'development') {
        // Use MailHog for development
        this.transporter = nodemailer.createTransporter({
          host: 'localhost',
          port: 1025,
          secure: false,
          ignoreTLS: true,
        });
      } else if (config.SMTP_HOST) {
        // Use configured SMTP server
        this.transporter = nodemailer.createTransporter({
          host: config.SMTP_HOST,
          port: Number(config.SMTP_PORT) || 587,
          secure: Number(config.SMTP_PORT) === 465,
          auth: config.SMTP_USER && config.SMTP_PASS ? {
            user: config.SMTP_USER,
            pass: config.SMTP_PASS,
          } : undefined,
          tls: {
            rejectUnauthorized: config.NODE_ENV === 'production',
          },
        });
      } else {
        // Use test account for testing
        this.createTestAccount();
      }

      this.isInitialized = true;
      logger.info('Email transporter initialized', {
        mode: config.NODE_ENV,
        host: config.SMTP_HOST || 'localhost'
      });

    } catch (error) {
      logger.error('Failed to initialize email transporter:', error);
      this.isInitialized = false;
    }
  }

  /**
   * Create test account for development/testing
   */
  private async createTestAccount(): Promise<void> {
    try {
      const testAccount = await nodemailer.createTestAccount();
      
      this.transporter = nodemailer.createTransporter({
        host: 'smtp.ethereal.email',
        port: 587,
        secure: false,
        auth: {
          user: testAccount.user,
          pass: testAccount.pass,
        },
      });

      logger.info('Test email account created', {
        user: testAccount.user,
        pass: testAccount.pass,
      });

    } catch (error) {
      logger.error('Failed to create test email account:', error);
    }
  }

  /**
   * Load email templates from filesystem
   */
  private async loadTemplates(): Promise<void> {
    try {
      const templatesDir = join(process.cwd(), 'src', 'templates', 'email');
      
      // Default templates
      const defaultTemplates: EmailTemplate[] = [
        {
          name: 'welcome',
          subject: 'Welcome to DocAssembler',
          html: `
            <h1>Welcome {{name}}!</h1>
            <p>Thank you for joining DocAssembler. Your account has been successfully created.</p>
            <p>You can now start uploading and processing documents.</p>
            <p><a href="{{loginUrl}}">Login to your account</a></p>
          `,
          text: `
            Welcome {{name}}!
            
            Thank you for joining DocAssembler. Your account has been successfully created.
            You can now start uploading and processing documents.
            
            Login: {{loginUrl}}
          `
        },
        {
          name: 'document-processed',
          subject: 'Document Processing Complete',
          html: `
            <h1>Document Processing Complete</h1>
            <p>Your document "{{documentName}}" has been successfully processed.</p>
            <p><strong>Processing Results:</strong></p>
            <ul>
              <li>Status: {{status}}</li>
              <li>Processing Time: {{processingTime}}</li>
              <li>Extracted Text: {{#if hasText}}Available{{else}}Not available{{/if}}</li>
              <li>Embeddings: {{#if hasEmbeddings}}Generated{{else}}Not generated{{/if}}</li>
            </ul>
            <p><a href="{{documentUrl}}">View document</a></p>
          `,
          text: `
            Document Processing Complete
            
            Your document "{{documentName}}" has been successfully processed.
            
            Processing Results:
            - Status: {{status}}
            - Processing Time: {{processingTime}}
            - Extracted Text: {{#if hasText}}Available{{else}}Not available{{/if}}
            - Embeddings: {{#if hasEmbeddings}}Generated{{else}}Not generated{{/if}}
            
            View document: {{documentUrl}}
          `
        },
        {
          name: 'processing-failed',
          subject: 'Document Processing Failed',
          html: `
            <h1>Document Processing Failed</h1>
            <p>Unfortunately, we couldn't process your document "{{documentName}}".</p>
            <p><strong>Error:</strong> {{error}}</p>
            <p>Please try uploading the document again or contact support if the issue persists.</p>
            <p><a href="{{supportUrl}}">Contact Support</a></p>
          `,
          text: `
            Document Processing Failed
            
            Unfortunately, we couldn't process your document "{{documentName}}".
            
            Error: {{error}}
            
            Please try uploading the document again or contact support if the issue persists.
            
            Contact Support: {{supportUrl}}
          `
        },
        {
          name: 'password-reset',
          subject: 'Reset Your Password',
          html: `
            <h1>Password Reset Request</h1>
            <p>You requested to reset your password for your DocAssembler account.</p>
            <p><a href="{{resetUrl}}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
            <p>This link will expire in {{expiresIn}} minutes.</p>
            <p>If you didn't request this, you can safely ignore this email.</p>
          `,
          text: `
            Password Reset Request
            
            You requested to reset your password for your DocAssembler account.
            
            Reset your password: {{resetUrl}}
            
            This link will expire in {{expiresIn}} minutes.
            
            If you didn't request this, you can safely ignore this email.
          `
        },
        {
          name: 'notification',
          subject: '{{subject}}',
          html: `
            <h1>{{title}}</h1>
            <p>{{message}}</p>
            {{#if actionUrl}}
            <p><a href="{{actionUrl}}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">{{actionText}}</a></p>
            {{/if}}
          `,
          text: `
            {{title}}
            
            {{message}}
            
            {{#if actionUrl}}
            {{actionText}}: {{actionUrl}}
            {{/if}}
          `
        }
      ];

      // Load default templates
      for (const template of defaultTemplates) {
        this.templates.set(template.name, template);
      }

      logger.info(`Loaded ${this.templates.size} email templates`);

    } catch (error) {
      logger.error('Failed to load email templates:', error);
    }
  }

  /**
   * Render template with data
   */
  private renderTemplate(templateName: string, data: Record<string, any> = {}): {
    subject: string;
    html: string;
    text?: string;
  } {
    const template = this.templates.get(templateName);
    
    if (!template) {
      throw new Error(`Email template '${templateName}' not found`);
    }

    // Compile templates with Handlebars
    const subjectTemplate = Handlebars.compile(template.subject);
    const htmlTemplate = Handlebars.compile(template.html);
    const textTemplate = template.text ? Handlebars.compile(template.text) : null;

    return {
      subject: subjectTemplate(data),
      html: htmlTemplate(data),
      text: textTemplate ? textTemplate(data) : undefined,
    };
  }

  /**
   * Send email
   */
  async sendEmail(options: EmailOptions): Promise<{
    success: boolean;
    messageId?: string;
    previewUrl?: string;
    error?: string;
  }> {
    if (!this.isInitialized) {
      logger.error('Email service not initialized');
      return {
        success: false,
        error: 'Email service not initialized'
      };
    }

    try {
      let emailContent: { subject: string; html: string; text?: string };

      // Use template if specified
      if (options.template) {
        emailContent = this.renderTemplate(options.template, options.data || {});
      } else {
        emailContent = {
          subject: options.subject,
          html: options.html || options.text || '',
          text: options.text,
        };
      }

      // Prepare email options
      const mailOptions: nodemailer.SendMailOptions = {
        from: config.SMTP_FROM || '"DocAssembler" <noreply@docassembler.com>',
        to: Array.isArray(options.to) ? options.to.join(', ') : options.to,
        cc: options.cc ? (Array.isArray(options.cc) ? options.cc.join(', ') : options.cc) : undefined,
        bcc: options.bcc ? (Array.isArray(options.bcc) ? options.bcc.join(', ') : options.bcc) : undefined,
        subject: emailContent.subject,
        html: emailContent.html,
        text: emailContent.text,
        attachments: options.attachments,
      };

      // Send email
      const info = await this.transporter.sendMail(mailOptions);

      logger.info('Email sent successfully', {
        messageId: info.messageId,
        to: options.to,
        subject: emailContent.subject,
        template: options.template,
      });

      // Get preview URL for development
      const previewUrl = config.NODE_ENV === 'development' && info.messageId
        ? nodemailer.getTestMessageUrl(info)
        : undefined;

      return {
        success: true,
        messageId: info.messageId,
        previewUrl: previewUrl || undefined,
      };

    } catch (error) {
      logger.error('Failed to send email:', error);
      
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Send welcome email
   */
  async sendWelcomeEmail(to: string, data: {
    name: string;
    loginUrl: string;
  }): Promise<{ success: boolean; messageId?: string; error?: string }> {
    return this.sendEmail({
      to,
      template: 'welcome',
      data,
    });
  }

  /**
   * Send document processed notification
   */
  async sendDocumentProcessedEmail(to: string, data: {
    documentName: string;
    status: string;
    processingTime: string;
    hasText: boolean;
    hasEmbeddings: boolean;
    documentUrl: string;
  }): Promise<{ success: boolean; messageId?: string; error?: string }> {
    return this.sendEmail({
      to,
      template: 'document-processed',
      data,
    });
  }

  /**
   * Send processing failed notification
   */
  async sendProcessingFailedEmail(to: string, data: {
    documentName: string;
    error: string;
    supportUrl: string;
  }): Promise<{ success: boolean; messageId?: string; error?: string }> {
    return this.sendEmail({
      to,
      template: 'processing-failed',
      data,
    });
  }

  /**
   * Send password reset email
   */
  async sendPasswordResetEmail(to: string, data: {
    resetUrl: string;
    expiresIn: number;
  }): Promise<{ success: boolean; messageId?: string; error?: string }> {
    return this.sendEmail({
      to,
      template: 'password-reset',
      data,
    });
  }

  /**
   * Send custom notification
   */
  async sendNotificationEmail(to: string, data: {
    subject: string;
    title: string;
    message: string;
    actionUrl?: string;
    actionText?: string;
  }): Promise<{ success: boolean; messageId?: string; error?: string }> {
    return this.sendEmail({
      to,
      template: 'notification',
      data,
    });
  }

  /**
   * Add custom template
   */
  addTemplate(template: EmailTemplate): void {
    this.templates.set(template.name, template);
    logger.info(`Added email template: ${template.name}`);
  }

  /**
   * Get available templates
   */
  getTemplates(): string[] {
    return Array.from(this.templates.keys());
  }

  /**
   * Test email configuration
   */
  async testConnection(): Promise<{
    success: boolean;
    error?: string;
  }> {
    if (!this.isInitialized) {
      return {
        success: false,
        error: 'Email service not initialized'
      };
    }

    try {
      await this.transporter.verify();
      
      logger.info('Email connection test successful');
      
      return { success: true };
      
    } catch (error) {
      logger.error('Email connection test failed:', error);
      
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get service status
   */
  getStatus(): {
    initialized: boolean;
    templatesLoaded: number;
    transporterReady: boolean;
  } {
    return {
      initialized: this.isInitialized,
      templatesLoaded: this.templates.size,
      transporterReady: !!this.transporter,
    };
  }

  /**
   * Graceful shutdown
   */
  async shutdown(): Promise<void> {
    try {
      if (this.transporter) {
        this.transporter.close();
      }
      
      logger.info('Email service shutdown completed');
      
    } catch (error) {
      logger.error('Error during email service shutdown:', error);
    }
  }
}

export const emailService = new EmailService();

