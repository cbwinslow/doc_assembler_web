import { Request, Response, NextFunction } from 'express';
import { Prisma } from '@prisma/client';
import { ZodError } from 'zod';
import { logger } from '@/utils/logger.js';
import { config } from '@/config/config.js';

export interface AppError extends Error {
  statusCode?: number;
  isOperational?: boolean;
}

export class CustomError extends Error implements AppError {
  statusCode: number;
  isOperational: boolean;

  constructor(message: string, statusCode: number = 500, isOperational: boolean = true) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = isOperational;
    
    Object.setPrototypeOf(this, CustomError.prototype);
    Error.captureStackTrace(this, this.constructor);
  }
}

export const errorHandler = (
  error: AppError,
  req: Request,
  res: Response,
  next: NextFunction
): void => {
  let statusCode = error.statusCode || 500;
  let message = error.message || 'Internal Server Error';
  let details: any = {};

  // Log error
  const errorInfo = {
    message: error.message,
    stack: error.stack,
    url: req.url,
    method: req.method,
    ip: req.ip,
    userAgent: req.get('User-Agent'),
    userId: req.user?.id,
    timestamp: new Date().toISOString()
  };

  if (statusCode >= 500) {
    logger.error('Server Error:', errorInfo);
  } else {
    logger.warn('Client Error:', errorInfo);
  }

  // Handle specific error types
  if (error instanceof ZodError) {
    statusCode = 400;
    message = 'Validation Error';
    details = {
      validationErrors: error.errors.map(err => ({
        field: err.path.join('.'),
        message: err.message,
        code: err.code
      }))
    };
  } else if (error instanceof Prisma.PrismaClientKnownRequestError) {
    switch (error.code) {
      case 'P2002':
        statusCode = 409;
        message = 'Unique constraint violation';
        details = {
          field: error.meta?.target,
          code: 'DUPLICATE_ENTRY'
        };
        break;
      case 'P2025':
        statusCode = 404;
        message = 'Record not found';
        details = {
          code: 'NOT_FOUND'
        };
        break;
      case 'P2003':
        statusCode = 400;
        message = 'Foreign key constraint failed';
        details = {
          code: 'FOREIGN_KEY_CONSTRAINT'
        };
        break;
      case 'P2014':
        statusCode = 400;
        message = 'Invalid relation';
        details = {
          code: 'INVALID_RELATION'
        };
        break;
      default:
        statusCode = 500;
        message = 'Database error';
        details = {
          code: 'DATABASE_ERROR'
        };
    }
  } else if (error instanceof Prisma.PrismaClientValidationError) {
    statusCode = 400;
    message = 'Database validation error';
    details = {
      code: 'VALIDATION_ERROR'
    };
  } else if (error instanceof Prisma.PrismaClientInitializationError) {
    statusCode = 503;
    message = 'Database connection error';
    details = {
      code: 'DATABASE_CONNECTION_ERROR'
    };
  } else if (error instanceof SyntaxError && 'body' in error) {
    statusCode = 400;
    message = 'Invalid JSON payload';
    details = {
      code: 'INVALID_JSON'
    };
  }

  // Handle multer errors (file upload)
  if (error.message?.includes('Unexpected field') || error.message?.includes('File too large')) {
    statusCode = 400;
    message = 'File upload error';
    details = {
      code: 'FILE_UPLOAD_ERROR'
    };
  }

  // Prepare error response
  const errorResponse: any = {
    error: getErrorName(statusCode),
    message,
    timestamp: new Date().toISOString(),
    path: req.path,
    method: req.method
  };

  // Add details if available
  if (Object.keys(details).length > 0) {
    errorResponse.details = details;
  }

  // Add stack trace in development
  if (config.NODE_ENV === 'development' && error.stack) {
    errorResponse.stack = error.stack;
  }

  // Add request ID if available
  if (req.headers['x-request-id']) {
    errorResponse.requestId = req.headers['x-request-id'];
  }

  res.status(statusCode).json(errorResponse);
};

export const notFoundHandler = (req: Request, res: Response): void => {
  res.status(404).json({
    error: 'Not Found',
    message: `Route ${req.originalUrl} not found`,
    timestamp: new Date().toISOString(),
    path: req.path,
    method: req.method
  });
};

export const asyncHandler = (fn: Function) => {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
};

// Utility function to get error name from status code
function getErrorName(statusCode: number): string {
  switch (statusCode) {
    case 400:
      return 'Bad Request';
    case 401:
      return 'Unauthorized';
    case 403:
      return 'Forbidden';
    case 404:
      return 'Not Found';
    case 409:
      return 'Conflict';
    case 422:
      return 'Unprocessable Entity';
    case 429:
      return 'Too Many Requests';
    case 500:
      return 'Internal Server Error';
    case 502:
      return 'Bad Gateway';
    case 503:
      return 'Service Unavailable';
    case 504:
      return 'Gateway Timeout';
    default:
      return 'Error';
  }
}

// Common error creators
export const createError = (message: string, statusCode: number = 500): CustomError => {
  return new CustomError(message, statusCode);
};

export const createValidationError = (message: string): CustomError => {
  return new CustomError(message, 400);
};

export const createNotFoundError = (resource: string = 'Resource'): CustomError => {
  return new CustomError(`${resource} not found`, 404);
};

export const createUnauthorizedError = (message: string = 'Unauthorized'): CustomError => {
  return new CustomError(message, 401);
};

export const createForbiddenError = (message: string = 'Forbidden'): CustomError => {
  return new CustomError(message, 403);
};

export const createConflictError = (message: string): CustomError => {
  return new CustomError(message, 409);
};

