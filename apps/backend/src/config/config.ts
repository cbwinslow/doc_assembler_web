import { z } from 'zod';
import dotenv from 'dotenv';

dotenv.config();

const configSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.string().transform(Number).default('3001'),
  
  // Database
  DATABASE_URL: z.string().min(1),
  REDIS_URL: z.string().min(1),
  
  // Authentication
  JWT_SECRET: z.string().min(32),
  JWT_EXPIRES_IN: z.string().default('7d'),
  JWT_REFRESH_SECRET: z.string().min(32),
  JWT_REFRESH_EXPIRES_IN: z.string().default('30d'),
  
  // OAuth
  AUTH0_DOMAIN: z.string().optional(),
  AUTH0_CLIENT_ID: z.string().optional(),
  AUTH0_CLIENT_SECRET: z.string().optional(),
  
  // API
  API_URL: z.string().url().default('http://localhost:3001'),
  CLIENT_URL: z.string().url().default('http://localhost:5173'),
  
  // AI Services
  OPENAI_API_KEY: z.string().optional(),
  COHERE_API_KEY: z.string().optional(),
  PINECONE_API_KEY: z.string().optional(),
  PINECONE_ENVIRONMENT: z.string().optional(),
  CHROMADB_URL: z.string().default('http://localhost:8000'),
  
  // Cloud Storage
  CLOUDFLARE_ACCOUNT_ID: z.string().optional(),
  CLOUDFLARE_API_TOKEN: z.string().optional(),
  CLOUDFLARE_R2_BUCKET: z.string().optional(),
  
  // Oracle Cloud
  OCI_USER_ID: z.string().optional(),
  OCI_FINGERPRINT: z.string().optional(),
  OCI_TENANCY_ID: z.string().optional(),
  OCI_REGION: z.string().optional(),
  OCI_PRIVATE_KEY_PATH: z.string().optional(),
  OCI_BUCKET_NAME: z.string().optional(),
  
  // AWS (fallback)
  AWS_ACCESS_KEY_ID: z.string().optional(),
  AWS_SECRET_ACCESS_KEY: z.string().optional(),
  AWS_REGION: z.string().optional(),
  AWS_S3_BUCKET: z.string().optional(),
  
  // Email
  SMTP_HOST: z.string().optional(),
  SMTP_PORT: z.string().transform(Number).optional(),
  SMTP_USER: z.string().optional(),
  SMTP_PASS: z.string().optional(),
  FROM_EMAIL: z.string().email().optional(),
  
  // Monitoring
  SENTRY_DSN: z.string().optional(),
  LOG_LEVEL: z.enum(['error', 'warn', 'info', 'debug']).default('info'),
  
  // Rate Limiting
  RATE_LIMIT_WINDOW_MS: z.string().transform(Number).default('900000'), // 15 minutes
  RATE_LIMIT_MAX_REQUESTS: z.string().transform(Number).default('100'),
  
  // File Upload
  MAX_FILE_SIZE: z.string().transform(Number).default('104857600'), // 100MB
  ALLOWED_FILE_TYPES: z.string().default('pdf,doc,docx,txt,md'),
  
  // WebSocket
  WS_HEARTBEAT_INTERVAL: z.string().transform(Number).default('30000'),
  WS_TIMEOUT: z.string().transform(Number).default('60000'),
});

// Validate environment variables
const parseConfig = () => {
  try {
    return configSchema.parse(process.env);
  } catch (error) {
    if (error instanceof z.ZodError) {
      const missingVars = error.errors.map(err => err.path.join('.')).join(', ');
      throw new Error(`Missing or invalid environment variables: ${missingVars}`);
    }
    throw error;
  }
};

export const config = parseConfig();

// Database configuration
export const dbConfig = {
  url: config.DATABASE_URL,
  ssl: config.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
  pool: {
    min: 2,
    max: 10,
    acquireTimeoutMillis: 30000,
    createTimeoutMillis: 30000,
    destroyTimeoutMillis: 5000,
    idleTimeoutMillis: 30000,
    reapIntervalMillis: 1000,
    createRetryIntervalMillis: 100,
  },
};

// Redis configuration
export const redisConfig = {
  url: config.REDIS_URL,
  retryDelayOnFailover: 100,
  enableReadyCheck: false,
  maxRetriesPerRequest: null,
  lazyConnect: true,
};

// CORS configuration
export const corsConfig = {
  origin: [config.CLIENT_URL, 'http://localhost:3000', 'http://localhost:5173'],
  credentials: true,
  optionsSuccessStatus: 200,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
};

// JWT configuration
export const jwtConfig = {
  secret: config.JWT_SECRET,
  expiresIn: config.JWT_EXPIRES_IN,
  refreshSecret: config.JWT_REFRESH_SECRET,
  refreshExpiresIn: config.JWT_REFRESH_EXPIRES_IN,
  issuer: 'doc-assembler-web',
  audience: 'doc-assembler-web-users',
};

// File upload configuration
export const uploadConfig = {
  maxFileSize: config.MAX_FILE_SIZE,
  allowedTypes: config.ALLOWED_FILE_TYPES.split(','),
  uploadPath: '/tmp/uploads',
  maxFiles: 10,
};

// AI service configuration
export const aiConfig = {
  openai: {
    apiKey: config.OPENAI_API_KEY,
    model: 'gpt-3.5-turbo',
    embeddingModel: 'text-embedding-ada-002',
    maxTokens: 4000,
    temperature: 0.7,
  },
  cohere: {
    apiKey: config.COHERE_API_KEY,
    model: 'command',
    embeddingModel: 'embed-english-v2.0',
  },
  pinecone: {
    apiKey: config.PINECONE_API_KEY,
    environment: config.PINECONE_ENVIRONMENT,
    indexName: 'doc-assembler-embeddings',
    dimension: 1536,
  },
  chromadb: {
    url: config.CHROMADB_URL,
    collectionName: 'documents',
  },
};

export default config;

