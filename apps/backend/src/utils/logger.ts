import winston from 'winston';
import { config } from '@/config/config.js';

// Define log levels
const levels = {
  error: 0,
  warn: 1,
  info: 2,
  http: 3,
  debug: 4,
};

// Define colors for each level
const colors = {
  error: 'red',
  warn: 'yellow',
  info: 'green',
  http: 'magenta',
  debug: 'white',
};

// Add colors to winston
winston.addColors(colors);

// Define format for logs
const format = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss:ms' }),
  winston.format.errors({ stack: true }),
  winston.format.json(),
  winston.format.printf((info) => {
    const { timestamp, level, message, ...meta } = info;
    
    let logMessage = `${timestamp} [${level.toUpperCase()}]: ${message}`;
    
    if (Object.keys(meta).length > 0) {
      logMessage += ` ${JSON.stringify(meta, null, 2)}`;
    }
    
    return logMessage;
  })
);

// Define transports
const transports = [
  // Console transport for development
  new winston.transports.Console({
    level: config.NODE_ENV === 'development' ? 'debug' : 'info',
    format: winston.format.combine(
      winston.format.colorize({ all: true }),
      winston.format.simple()
    )
  }),
  
  // File transport for errors
  new winston.transports.File({
    filename: 'logs/error.log',
    level: 'error',
    format: winston.format.combine(
      winston.format.timestamp(),
      winston.format.errors({ stack: true }),
      winston.format.json()
    ),
    maxsize: 5242880, // 5MB
    maxFiles: 5,
  }),
  
  // File transport for all logs
  new winston.transports.File({
    filename: 'logs/combined.log',
    format: winston.format.combine(
      winston.format.timestamp(),
      winston.format.errors({ stack: true }),
      winston.format.json()
    ),
    maxsize: 5242880, // 5MB
    maxFiles: 5,
  }),
];

// Create the logger
export const logger = winston.createLogger({
  level: config.LOG_LEVEL,
  levels,
  format,
  transports,
  exitOnError: false,
});

// Create a stream object for Morgan middleware
export const morganStream = {
  write: (message: string) => {
    logger.http(message.trim());
  },
};

// Custom logging methods for different scenarios
export const loggers = {
  // Authentication logging
  auth: {
    login: (userId: string, ip: string, userAgent?: string) => {
      logger.info('User login', {
        type: 'auth',
        action: 'login',
        userId,
        ip,
        userAgent
      });
    },
    logout: (userId: string, ip: string) => {
      logger.info('User logout', {
        type: 'auth',
        action: 'logout',
        userId,
        ip
      });
    },
    loginFailed: (email: string, ip: string, reason: string) => {
      logger.warn('Login failed', {
        type: 'auth',
        action: 'login_failed',
        email,
        ip,
        reason
      });
    },
    registrationAttempt: (email: string, ip: string) => {
      logger.info('Registration attempt', {
        type: 'auth',
        action: 'registration_attempt',
        email,
        ip
      });
    }
  },
  
  // Database logging
  database: {
    query: (query: string, duration: number) => {
      logger.debug('Database query', {
        type: 'database',
        query,
        duration
      });
    },
    error: (error: Error, query?: string) => {
      logger.error('Database error', {
        type: 'database',
        error: error.message,
        stack: error.stack,
        query
      });
    },
    connection: (status: 'connected' | 'disconnected' | 'error') => {
      logger.info('Database connection', {
        type: 'database',
        status
      });
    }
  },
  
  // API logging
  api: {
    request: (method: string, url: string, userId?: string, ip?: string) => {
      logger.http('API request', {
        type: 'api',
        method,
        url,
        userId,
        ip
      });
    },
    response: (method: string, url: string, statusCode: number, duration: number) => {
      logger.http('API response', {
        type: 'api',
        method,
        url,
        statusCode,
        duration
      });
    },
    error: (error: Error, method: string, url: string, userId?: string) => {
      logger.error('API error', {
        type: 'api',
        error: error.message,
        stack: error.stack,
        method,
        url,
        userId
      });
    }
  },
  
  // File processing logging
  file: {
    upload: (filename: string, size: number, userId: string) => {
      logger.info('File upload', {
        type: 'file',
        action: 'upload',
        filename,
        size,
        userId
      });
    },
    processing: (documentId: string, type: string, status: string) => {
      logger.info('File processing', {
        type: 'file',
        action: 'processing',
        documentId,
        processingType: type,
        status
      });
    },
    error: (error: Error, documentId?: string, filename?: string) => {
      logger.error('File processing error', {
        type: 'file',
        error: error.message,
        stack: error.stack,
        documentId,
        filename
      });
    }
  },
  
  // Security logging
  security: {
    suspiciousActivity: (description: string, userId?: string, ip?: string, metadata?: any) => {
      logger.warn('Suspicious activity detected', {
        type: 'security',
        description,
        userId,
        ip,
        metadata
      });
    },
    rateLimitExceeded: (ip: string, endpoint: string, userId?: string) => {
      logger.warn('Rate limit exceeded', {
        type: 'security',
        action: 'rate_limit_exceeded',
        ip,
        endpoint,
        userId
      });
    },
    unauthorizedAccess: (ip: string, endpoint: string, reason: string) => {
      logger.warn('Unauthorized access attempt', {
        type: 'security',
        action: 'unauthorized_access',
        ip,
        endpoint,
        reason
      });
    }
  },
  
  // Performance logging
  performance: {
    slowQuery: (query: string, duration: number, threshold: number = 1000) => {
      if (duration > threshold) {
        logger.warn('Slow query detected', {
          type: 'performance',
          query,
          duration,
          threshold
        });
      }
    },
    memoryUsage: (usage: NodeJS.MemoryUsage) => {
      logger.debug('Memory usage', {
        type: 'performance',
        ...usage
      });
    },
    cpuUsage: (usage: NodeJS.CpuUsage) => {
      logger.debug('CPU usage', {
        type: 'performance',
        ...usage
      });
    }
  }
};

// Error handling for logger
logger.on('error', (error) => {
  console.error('Logger error:', error);
});

// Production-specific enhancements
if (config.NODE_ENV === 'production') {
  // Add additional transports for production
  // Example: Elasticsearch, Datadog, CloudWatch, etc.
  
  // Uncomment and configure as needed:
  
  // Elasticsearch transport
  // const { ElasticsearchTransport } = require('winston-elasticsearch');
  // logger.add(new ElasticsearchTransport({
  //   level: 'info',
  //   clientOpts: { node: process.env.ELASTICSEARCH_URL }
  // }));
  
  // Datadog transport
  // const DatadogWinston = require('datadog-winston');
  // logger.add(new DatadogWinston({
  //   apiKey: process.env.DATADOG_API_KEY,
  //   hostname: process.env.HOSTNAME,
  //   service: 'doc-assembler-api',
  //   ddsource: 'nodejs'
  // }));
}

export default logger;

