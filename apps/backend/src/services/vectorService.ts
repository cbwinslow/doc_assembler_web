import { ChromaApi, OpenAIEmbeddingFunction } from 'chromadb';
import { logger } from '@/utils/logger.js';
import { aiConfig } from '@/config/config.js';

export interface DocumentMetadata {
  text: string;
  title: string;
  type: string;
  userId: string;
  documentId?: string;
  createdAt?: string;
  [key: string]: any;
}

export interface SearchResult {
  id: string;
  score: number;
  metadata: DocumentMetadata;
  distance: number;
}

export interface SearchOptions {
  limit?: number;
  threshold?: number;
  filters?: Record<string, any>;
}

export class VectorService {
  private client: ChromaApi;
  private collection: any = null;
  private embeddingFunction: any;

  constructor() {
    this.client = new ChromaApi({
      path: aiConfig.chromadb.url
    });
    
    // Initialize embedding function
    if (aiConfig.openai.apiKey) {
      this.embeddingFunction = new OpenAIEmbeddingFunction({
        openai_api_key: aiConfig.openai.apiKey,
        openai_model: aiConfig.openai.embeddingModel
      });
    }
    
    this.initializeCollection();
  }

  /**
   * Initialize ChromaDB collection
   */
  private async initializeCollection(): Promise<void> {
    try {
      // Try to get existing collection
      try {
        this.collection = await this.client.getCollection({
          name: aiConfig.chromadb.collectionName,
          embeddingFunction: this.embeddingFunction
        });
        logger.info('Connected to existing ChromaDB collection');
      } catch {
        // Create new collection if it doesn't exist
        this.collection = await this.client.createCollection({
          name: aiConfig.chromadb.collectionName,
          embeddingFunction: this.embeddingFunction,
          metadata: {
            description: 'Document embeddings for similarity search',
            created: new Date().toISOString()
          }
        });
        logger.info('Created new ChromaDB collection');
      }
    } catch (error) {
      logger.error('Failed to initialize ChromaDB collection:', error);
      throw error;
    }
  }

  /**
   * Generate embeddings for text using OpenAI or fallback
   */
  async generateEmbeddings(text: string): Promise<number[]> {
    try {
      if (aiConfig.openai.apiKey) {
        return await this.generateOpenAIEmbeddings(text);
      } else if (aiConfig.cohere.apiKey) {
        return await this.generateCohereEmbeddings(text);
      } else {
        // Fallback to simple hash-based embeddings for development
        return this.generateSimpleEmbeddings(text);
      }
    } catch (error) {
      logger.error('Failed to generate embeddings:', error);
      throw error;
    }
  }

  /**
   * Generate embeddings using OpenAI
   */
  private async generateOpenAIEmbeddings(text: string): Promise<number[]> {
    try {
      const { OpenAI } = await import('openai');
      const openai = new OpenAI({ apiKey: aiConfig.openai.apiKey });

      const response = await openai.embeddings.create({
        model: aiConfig.openai.embeddingModel,
        input: text.substring(0, 8000), // Truncate to model limits
        encoding_format: 'float'
      });

      return response.data[0].embedding;
    } catch (error) {
      logger.error('OpenAI embedding generation failed:', error);
      throw error;
    }
  }

  /**
   * Generate embeddings using Cohere
   */
  private async generateCohereEmbeddings(text: string): Promise<number[]> {
    try {
      const { CohereClient } = await import('cohere-ai');
      const cohere = new CohereClient({
        token: aiConfig.cohere.apiKey
      });

      const response = await cohere.embed({
        texts: [text.substring(0, 8000)],
        model: aiConfig.cohere.embeddingModel,
        inputType: 'search_document'
      });

      return response.embeddings[0];
    } catch (error) {
      logger.error('Cohere embedding generation failed:', error);
      throw error;
    }
  }

  /**
   * Simple fallback embedding generation for development
   */
  private generateSimpleEmbeddings(text: string): number[] {
    // Simple TF-IDF style embeddings for development/testing
    const words = text.toLowerCase().match(/\b\w+\b/g) || [];
    const wordFreq: Record<string, number> = {};
    
    // Calculate word frequencies
    words.forEach(word => {
      wordFreq[word] = (wordFreq[word] || 0) + 1;
    });

    // Create a fixed-size embedding vector
    const embeddingSize = 384; // Smaller size for development
    const embedding = new Array(embeddingSize).fill(0);
    
    // Hash words to embedding dimensions
    Object.entries(wordFreq).forEach(([word, freq]) => {
      const hash = this.simpleHash(word);
      const index = Math.abs(hash) % embeddingSize;
      embedding[index] += freq / words.length;
    });

    // Normalize the vector
    const magnitude = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0));
    return magnitude > 0 ? embedding.map(val => val / magnitude) : embedding;
  }

  /**
   * Simple hash function for development embeddings
   */
  private simpleHash(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return hash;
  }

  /**
   * Store document embeddings in ChromaDB
   */
  async storeDocumentEmbeddings(
    documentId: string,
    embeddings: number[],
    metadata: DocumentMetadata
  ): Promise<void> {
    try {
      if (!this.collection) {
        await this.initializeCollection();
      }

      await this.collection.add({
        ids: [documentId],
        embeddings: [embeddings],
        metadatas: [{
          ...metadata,
          documentId,
          createdAt: new Date().toISOString()
        }],
        documents: [metadata.text.substring(0, 1000)] // Store truncated text for preview
      });

      logger.info(`Stored embeddings for document ${documentId}`);
    } catch (error) {
      logger.error(`Failed to store embeddings for document ${documentId}:`, error);
      throw error;
    }
  }

  /**
   * Search for similar documents using vector similarity
   */
  async searchSimilarDocuments(
    query: string,
    options: SearchOptions = {}
  ): Promise<SearchResult[]> {
    try {
      if (!this.collection) {
        await this.initializeCollection();
      }

      const {
        limit = 10,
        threshold = 0.7,
        filters = {}
      } = options;

      // Generate embeddings for the query
      const queryEmbeddings = await this.generateEmbeddings(query);

      // Perform similarity search
      const results = await this.collection.query({
        queryEmbeddings: [queryEmbeddings],
        nResults: limit,
        where: Object.keys(filters).length > 0 ? filters : undefined
      });

      // Format results
      const searchResults: SearchResult[] = [];
      
      if (results.ids && results.ids[0]) {
        for (let i = 0; i < results.ids[0].length; i++) {
          const score = results.distances?.[0]?.[i] || 0;
          const distance = 1 - score; // Convert distance to similarity score
          
          if (distance >= threshold) {
            searchResults.push({
              id: results.ids[0][i],
              score: distance,
              metadata: results.metadatas?.[0]?.[i] as DocumentMetadata,
              distance: score
            });
          }
        }
      }

      logger.info(`Vector search found ${searchResults.length} similar documents`);
      return searchResults.sort((a, b) => b.score - a.score);
      
    } catch (error) {
      logger.error('Vector search failed:', error);
      throw error;
    }
  }

  /**
   * Search for similar documents by document ID
   */
  async findSimilarToDocument(
    documentId: string,
    options: SearchOptions = {}
  ): Promise<SearchResult[]> {
    try {
      if (!this.collection) {
        await this.initializeCollection();
      }

      // Get the document from ChromaDB
      const document = await this.collection.get({
        ids: [documentId],
        include: ['embeddings', 'metadatas']
      });

      if (!document.embeddings || !document.embeddings[0]) {
        throw new Error(`Document ${documentId} not found in vector database`);
      }

      // Search using the document's embeddings
      const results = await this.collection.query({
        queryEmbeddings: [document.embeddings[0]],
        nResults: (options.limit || 10) + 1, // +1 to exclude the original document
        where: options.filters
      });

      // Format and filter results (exclude the original document)
      const searchResults: SearchResult[] = [];
      
      if (results.ids && results.ids[0]) {
        for (let i = 0; i < results.ids[0].length; i++) {
          const id = results.ids[0][i];
          
          // Skip the original document
          if (id === documentId) continue;
          
          const score = results.distances?.[0]?.[i] || 0;
          const distance = 1 - score;
          
          if (distance >= (options.threshold || 0.7)) {
            searchResults.push({
              id,
              score: distance,
              metadata: results.metadatas?.[0]?.[i] as DocumentMetadata,
              distance: score
            });
          }
        }
      }

      return searchResults
        .sort((a, b) => b.score - a.score)
        .slice(0, options.limit || 10);
        
    } catch (error) {
      logger.error(`Failed to find similar documents to ${documentId}:`, error);
      throw error;
    }
  }

  /**
   * Update document embeddings
   */
  async updateDocumentEmbeddings(
    documentId: string,
    embeddings: number[],
    metadata: DocumentMetadata
  ): Promise<void> {
    try {
      if (!this.collection) {
        await this.initializeCollection();
      }

      // Delete existing embeddings
      await this.deleteDocumentEmbeddings(documentId);
      
      // Add new embeddings
      await this.storeDocumentEmbeddings(documentId, embeddings, metadata);
      
      logger.info(`Updated embeddings for document ${documentId}`);
    } catch (error) {
      logger.error(`Failed to update embeddings for document ${documentId}:`, error);
      throw error;
    }
  }

  /**
   * Delete document embeddings
   */
  async deleteDocumentEmbeddings(documentId: string): Promise<void> {
    try {
      if (!this.collection) {
        await this.initializeCollection();
      }

      await this.collection.delete({
        ids: [documentId]
      });

      logger.info(`Deleted embeddings for document ${documentId}`);
    } catch (error) {
      logger.error(`Failed to delete embeddings for document ${documentId}:`, error);
      throw error;
    }
  }

  /**
   * Get collection statistics
   */
  async getCollectionStats(): Promise<{
    count: number;
    dimension: number;
    lastUpdated: string;
  }> {
    try {
      if (!this.collection) {
        await this.initializeCollection();
      }

      const count = await this.collection.count();
      
      return {
        count,
        dimension: aiConfig.pinecone.dimension, // Default dimension
        lastUpdated: new Date().toISOString()
      };
    } catch (error) {
      logger.error('Failed to get collection stats:', error);
      throw error;
    }
  }

  /**
   * Perform semantic search with advanced filtering
   */
  async semanticSearch(
    query: string,
    filters: {
      userId?: string;
      documentType?: string;
      dateRange?: { start: Date; end: Date };
      tags?: string[];
    } = {},
    options: SearchOptions = {}
  ): Promise<SearchResult[]> {
    try {
      const whereClause: Record<string, any> = {};

      // Build ChromaDB where clause
      if (filters.userId) {
        whereClause.userId = filters.userId;
      }
      
      if (filters.documentType) {
        whereClause.type = filters.documentType;
      }
      
      if (filters.tags && filters.tags.length > 0) {
        whereClause.tags = { $in: filters.tags };
      }

      return await this.searchSimilarDocuments(query, {
        ...options,
        filters: whereClause
      });
    } catch (error) {
      logger.error('Semantic search failed:', error);
      throw error;
    }
  }

  /**
   * Batch process multiple documents
   */
  async batchStoreEmbeddings(
    documents: Array<{
      id: string;
      embeddings: number[];
      metadata: DocumentMetadata;
    }>
  ): Promise<void> {
    try {
      if (!this.collection) {
        await this.initializeCollection();
      }

      const ids = documents.map(doc => doc.id);
      const embeddings = documents.map(doc => doc.embeddings);
      const metadatas = documents.map(doc => ({
        ...doc.metadata,
        documentId: doc.id,
        createdAt: new Date().toISOString()
      }));
      const texts = documents.map(doc => doc.metadata.text.substring(0, 1000));

      await this.collection.add({
        ids,
        embeddings,
        metadatas,
        documents: texts
      });

      logger.info(`Batch stored embeddings for ${documents.length} documents`);
    } catch (error) {
      logger.error('Batch store embeddings failed:', error);
      throw error;
    }
  }

  /**
   * Health check for vector service
   */
  async healthCheck(): Promise<{ status: string; details: any }> {
    try {
      if (!this.collection) {
        await this.initializeCollection();
      }

      const stats = await this.getCollectionStats();
      
      return {
        status: 'healthy',
        details: {
          collectionName: aiConfig.chromadb.collectionName,
          documentCount: stats.count,
          embeddingFunction: this.embeddingFunction ? 'configured' : 'fallback',
          chromadbUrl: aiConfig.chromadb.url
        }
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        details: {
          error: error instanceof Error ? error.message : 'Unknown error'
        }
      };
    }
  }
}

export const vectorService = new VectorService();

