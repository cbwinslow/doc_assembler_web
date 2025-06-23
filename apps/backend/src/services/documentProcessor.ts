import { createWorker } from 'tesseract.js';
import pdfParse from 'pdf-parse';
import mammoth from 'mammoth';
import sharp from 'sharp';
import { createHash } from 'crypto';
import { PrismaClient } from '@prisma/client';
import { logger } from '@/utils/logger.js';
import { config, aiConfig } from '@/config/config.js';
import { vectorService } from './vectorService.js';
import { storageService } from './storageService.js';
import { queueService } from './queueService.js';

const prisma = new PrismaClient();

export interface ProcessingOptions {
  extractText?: boolean;
  generateEmbeddings?: boolean;
  performOCR?: boolean;
  generateSummary?: boolean;
  classifyDocument?: boolean;
  extractMetadata?: boolean;
}

export interface ProcessingResult {
  documentId: string;
  extractedText?: string;
  summary?: string;
  classification?: string;
  metadata?: Record<string, any>;
  embeddings?: number[];
  processingTime: number;
  success: boolean;
  error?: string;
}

export class DocumentProcessorService {
  private ocrWorker: any = null;

  constructor() {
    this.initializeOCR();
  }

  private async initializeOCR(): Promise<void> {
    try {
      this.ocrWorker = await createWorker('eng');
      logger.info('OCR worker initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize OCR worker:', error);
    }
  }

  /**
   * Process a document through the complete AI pipeline
   */
  async processDocument(
    documentId: string,
    filePath: string,
    options: ProcessingOptions = {}
  ): Promise<ProcessingResult> {
    const startTime = Date.now();
    
    try {
      logger.info(`Starting document processing for ${documentId}`, {
        documentId,
        filePath,
        options
      });

      // Get document from database
      const document = await prisma.document.findUnique({
        where: { id: documentId }
      });

      if (!document) {
        throw new Error(`Document ${documentId} not found`);
      }

      // Update document status
      await this.updateDocumentStatus(documentId, 'IN_PROGRESS');

      const result: ProcessingResult = {
        documentId,
        processingTime: 0,
        success: false
      };

      // Step 1: Extract text based on file type
      if (options.extractText !== false) {
        result.extractedText = await this.extractText(filePath, document.mimeType);
        
        // Update document with extracted text
        await prisma.document.update({
          where: { id: documentId },
          data: { extractedText: result.extractedText }
        });
      }

      // Step 2: Extract metadata
      if (options.extractMetadata) {
        result.metadata = await this.extractMetadata(filePath, document.mimeType);
        
        await prisma.document.update({
          where: { id: documentId },
          data: { 
            metadata: {
              ...document.metadata,
              ...result.metadata
            }
          }
        });
      }

      // Step 3: Generate embeddings
      if (options.generateEmbeddings && result.extractedText) {
        result.embeddings = await vectorService.generateEmbeddings(result.extractedText);
        
        // Store embeddings in ChromaDB
        await vectorService.storeDocumentEmbeddings(documentId, result.embeddings, {
          text: result.extractedText,
          title: document.title,
          type: document.type,
          userId: document.userId
        });

        // Update document with embeddings
        await prisma.document.update({
          where: { id: documentId },
          data: { embeddings: result.embeddings }
        });
      }

      // Step 4: Generate summary
      if (options.generateSummary && result.extractedText) {
        result.summary = await this.generateSummary(result.extractedText);
        
        await prisma.document.update({
          where: { id: documentId },
          data: { summary: result.summary }
        });
      }

      // Step 5: Classify document
      if (options.classifyDocument && result.extractedText) {
        result.classification = await this.classifyDocument(result.extractedText);
        
        await prisma.document.update({
          where: { id: documentId },
          data: { 
            aiMetadata: {
              ...document.aiMetadata,
              classification: result.classification
            }
          }
        });
      }

      // Update final status
      await this.updateDocumentStatus(documentId, 'COMPLETED', new Date());
      
      result.processingTime = Date.now() - startTime;
      result.success = true;

      logger.info(`Document processing completed for ${documentId}`, {
        documentId,
        processingTime: result.processingTime,
        hasText: !!result.extractedText,
        hasEmbeddings: !!result.embeddings,
        hasSummary: !!result.summary
      });

      return result;

    } catch (error) {
      logger.error(`Document processing failed for ${documentId}:`, error);
      
      await this.updateDocumentStatus(documentId, 'FAILED');
      
      return {
        documentId,
        processingTime: Date.now() - startTime,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Extract text from various file formats
   */
  private async extractText(filePath: string, mimeType: string): Promise<string> {
    try {
      switch (mimeType) {
        case 'application/pdf':
          return await this.extractPDFText(filePath);
        
        case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        case 'application/msword':
          return await this.extractWordText(filePath);
        
        case 'text/plain':
        case 'text/markdown':
          return await this.extractPlainText(filePath);
        
        case 'image/jpeg':
        case 'image/png':
        case 'image/tiff':
          return await this.performOCR(filePath);
        
        default:
          throw new Error(`Unsupported file type: ${mimeType}`);
      }
    } catch (error) {
      logger.error(`Text extraction failed for ${filePath}:`, error);
      throw error;
    }
  }

  /**
   * Extract text from PDF files
   */
  private async extractPDFText(filePath: string): Promise<string> {
    const fs = await import('fs/promises');
    const buffer = await fs.readFile(filePath);
    const data = await pdfParse(buffer);
    return data.text;
  }

  /**
   * Extract text from Word documents
   */
  private async extractWordText(filePath: string): Promise<string> {
    const fs = await import('fs/promises');
    const buffer = await fs.readFile(filePath);
    const result = await mammoth.extractRawText({ buffer });
    return result.value;
  }

  /**
   * Extract text from plain text files
   */
  private async extractPlainText(filePath: string): Promise<string> {
    const fs = await import('fs/promises');
    return await fs.readFile(filePath, 'utf-8');
  }

  /**
   * Perform OCR on image files
   */
  private async performOCR(filePath: string): Promise<string> {
    if (!this.ocrWorker) {
      throw new Error('OCR worker not initialized');
    }

    try {
      // Preprocess image for better OCR results
      const processedImagePath = await this.preprocessImage(filePath);
      
      const { data: { text } } = await this.ocrWorker.recognize(processedImagePath);
      return text;
    } catch (error) {
      logger.error('OCR processing failed:', error);
      throw error;
    }
  }

  /**
   * Preprocess images for better OCR results
   */
  private async preprocessImage(inputPath: string): Promise<string> {
    const outputPath = inputPath.replace(/\.[^.]+$/, '_processed.png');
    
    await sharp(inputPath)
      .greyscale()
      .normalise()
      .sharpen()
      .png()
      .toFile(outputPath);
    
    return outputPath;
  }

  /**
   * Extract metadata from files
   */
  private async extractMetadata(filePath: string, mimeType: string): Promise<Record<string, any>> {
    const fs = await import('fs/promises');
    const stats = await fs.stat(filePath);
    
    const metadata: Record<string, any> = {
      fileSize: stats.size,
      lastModified: stats.mtime,
      processed: new Date(),
      mimeType
    };

    // Add specific metadata based on file type
    switch (mimeType) {
      case 'application/pdf':
        metadata.pages = await this.getPDFPageCount(filePath);
        break;
      
      case 'image/jpeg':
      case 'image/png':
        metadata.imageInfo = await this.getImageInfo(filePath);
        break;
    }

    return metadata;
  }

  /**
   * Get PDF page count
   */
  private async getPDFPageCount(filePath: string): Promise<number> {
    try {
      const fs = await import('fs/promises');
      const buffer = await fs.readFile(filePath);
      const data = await pdfParse(buffer);
      return data.numpages;
    } catch (error) {
      logger.warn('Failed to get PDF page count:', error);
      return 0;
    }
  }

  /**
   * Get image information
   */
  private async getImageInfo(filePath: string): Promise<Record<string, any>> {
    try {
      const metadata = await sharp(filePath).metadata();
      return {
        width: metadata.width,
        height: metadata.height,
        format: metadata.format,
        space: metadata.space,
        channels: metadata.channels,
        depth: metadata.depth
      };
    } catch (error) {
      logger.warn('Failed to get image info:', error);
      return {};
    }
  }

  /**
   * Generate AI summary of text
   */
  private async generateSummary(text: string): Promise<string> {
    try {
      // Truncate text if too long for API
      const maxLength = 4000;
      const truncatedText = text.length > maxLength ? text.substring(0, maxLength) + '...' : text;

      if (aiConfig.openai.apiKey) {
        const { OpenAI } = await import('openai');
        const openai = new OpenAI({ apiKey: aiConfig.openai.apiKey });

        const response = await openai.chat.completions.create({
          model: 'gpt-3.5-turbo',
          messages: [
            {
              role: 'system',
              content: 'You are a helpful assistant that creates concise, informative summaries of documents. Focus on key points, main topics, and important details.'
            },
            {
              role: 'user',
              content: `Please provide a concise summary of the following text:\n\n${truncatedText}`
            }
          ],
          max_tokens: 200,
          temperature: 0.3
        });

        return response.choices[0]?.message?.content || 'Summary generation failed';
      }

      // Fallback: Simple extractive summary
      return this.extractiveSummary(text);
      
    } catch (error) {
      logger.error('Summary generation failed:', error);
      return 'Summary generation failed';
    }
  }

  /**
   * Simple extractive summary as fallback
   */
  private extractiveSummary(text: string): string {
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 20);
    const maxSentences = Math.min(3, sentences.length);
    return sentences.slice(0, maxSentences).join('. ') + '.';
  }

  /**
   * Classify document using AI
   */
  private async classifyDocument(text: string): Promise<string> {
    try {
      const categories = [
        'legal', 'financial', 'technical', 'marketing', 'academic', 
        'medical', 'business', 'personal', 'government', 'other'
      ];

      if (aiConfig.openai.apiKey) {
        const { OpenAI } = await import('openai');
        const openai = new OpenAI({ apiKey: aiConfig.openai.apiKey });

        const response = await openai.chat.completions.create({
          model: 'gpt-3.5-turbo',
          messages: [
            {
              role: 'system',
              content: `Classify the following document into one of these categories: ${categories.join(', ')}. Respond with only the category name.`
            },
            {
              role: 'user',
              content: text.substring(0, 1000)
            }
          ],
          max_tokens: 10,
          temperature: 0.1
        });

        const classification = response.choices[0]?.message?.content?.toLowerCase().trim();
        return categories.includes(classification || '') ? classification! : 'other';
      }

      // Fallback: Simple keyword-based classification
      return this.keywordBasedClassification(text);
      
    } catch (error) {
      logger.error('Document classification failed:', error);
      return 'other';
    }
  }

  /**
   * Simple keyword-based classification as fallback
   */
  private keywordBasedClassification(text: string): string {
    const lowerText = text.toLowerCase();
    
    const keywordMap = {
      legal: ['contract', 'agreement', 'lawsuit', 'court', 'legal', 'attorney'],
      financial: ['budget', 'revenue', 'profit', 'investment', 'financial', 'money'],
      technical: ['algorithm', 'software', 'programming', 'technical', 'system', 'code'],
      medical: ['patient', 'diagnosis', 'treatment', 'medical', 'health', 'doctor'],
      academic: ['research', 'study', 'analysis', 'academic', 'university', 'paper']
    };

    for (const [category, keywords] of Object.entries(keywordMap)) {
      if (keywords.some(keyword => lowerText.includes(keyword))) {
        return category;
      }
    }

    return 'other';
  }

  /**
   * Update document processing status
   */
  private async updateDocumentStatus(
    documentId: string,
    status: string,
    processedAt?: Date
  ): Promise<void> {
    await prisma.document.update({
      where: { id: documentId },
      data: {
        status: status as any,
        processedAt: processedAt || (status === 'COMPLETED' ? new Date() : undefined)
      }
    });
  }

  /**
   * Queue document for processing
   */
  async queueDocumentProcessing(
    documentId: string,
    filePath: string,
    options: ProcessingOptions = {},
    priority: number = 5
  ): Promise<void> {
    await queueService.addDocumentProcessingJob({
      documentId,
      filePath,
      options
    }, priority);
  }

  /**
   * Calculate document checksum
   */
  async calculateChecksum(filePath: string): Promise<string> {
    const fs = await import('fs/promises');
    const buffer = await fs.readFile(filePath);
    return createHash('sha256').update(buffer).digest('hex');
  }

  /**
   * Clean up processed files
   */
  async cleanup(filePath: string): Promise<void> {
    try {
      const fs = await import('fs/promises');
      await fs.unlink(filePath);
      
      // Clean up processed image files
      const processedPath = filePath.replace(/\.[^.]+$/, '_processed.png');
      try {
        await fs.unlink(processedPath);
      } catch {
        // Ignore if file doesn't exist
      }
    } catch (error) {
      logger.warn('Failed to cleanup files:', error);
    }
  }

  /**
   * Destroy OCR worker on shutdown
   */
  async destroy(): Promise<void> {
    if (this.ocrWorker) {
      await this.ocrWorker.terminate();
      this.ocrWorker = null;
    }
  }
}

export const documentProcessor = new DocumentProcessorService();

