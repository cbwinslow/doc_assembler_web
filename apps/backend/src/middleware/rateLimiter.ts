import rateLimit from 'express-rate-limit';
import { Request, Response } from 'express';
import { config } from '@/config/config.js';
import { logger } from '@/utils/logger.js';

// Create a basic rate limiter
export const rateLimiter = rateLimit({
  windowMs: config.RATE_LIMIT_WINDOW_MS,
  max: config.RATE_LIMIT_MAX_REQUESTS,
  message: {
    error: 'Too Many Requests',
    message: 'Too many requests from this IP, please try again later.',
    retryAfter: Math.ceil(config.RATE_LIMIT_WINDOW_MS / 1000)
  },
  standardHeaders: true,
  legacyHeaders: false,
  skip: (req: Request): boolean => {
    // Skip rate limiting for health checks
    return req.path === '/health' || req.path === '/api/health';
  },
  keyGenerator: (req: Request): string => {
    // Use IP address as key, but consider user ID if authenticated
    return req.user?.id || req.ip;
  },
  onLimitReached: (req: Request, res: Response): void => {
    logger.warn(`Rate limit exceeded for ${req.ip}`, {
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      path: req.path,
      userId: req.user?.id
    });
  }
});

// Stricter rate limiter for authentication endpoints
export const authRateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // Limit each IP to 5 requests per windowMs
  message: {
    error: 'Too Many Authentication Attempts',
    message: 'Too many authentication attempts, please try again later.',
    retryAfter: 900 // 15 minutes
  },
  standardHeaders: true,
  legacyHeaders: false,
  skipSuccessfulRequests: true,
  onLimitReached: (req: Request, res: Response): void => {
    logger.warn(`Auth rate limit exceeded for ${req.ip}`, {
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      path: req.path,
      body: { email: req.body?.email } // Only log email, not password
    });
  }
});

// Rate limiter for file uploads
export const uploadRateLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 10, // Limit each IP to 10 uploads per minute
  message: {
    error: 'Too Many Upload Requests',
    message: 'Too many file upload requests, please try again later.',
    retryAfter: 60
  },
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: (req: Request): string => {
    return req.user?.id || req.ip;
  },
  skip: (req: Request): boolean => {
    // Skip for admins
    return req.user?.role === 'ADMIN';
  }
});

// Rate limiter for search operations
export const searchRateLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 30, // Limit each user to 30 searches per minute
  message: {
    error: 'Too Many Search Requests',
    message: 'Too many search requests, please try again later.',
    retryAfter: 60
  },
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: (req: Request): string => {
    return req.user?.id || req.ip;
  }
});

// Rate limiter for API key requests
export const apiKeyRateLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100, // Higher limit for API key usage
  message: {
    error: 'API Rate Limit Exceeded',
    message: 'API rate limit exceeded, please try again later.',
    retryAfter: 60
  },
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: (req: Request): string => {
    const apiKey = req.headers['x-api-key'] as string;
    return apiKey || req.ip;
  }
});

// Rate limiter for password reset
export const passwordResetRateLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 3, // Limit each IP to 3 password reset requests per hour
  message: {
    error: 'Too Many Password Reset Requests',
    message: 'Too many password reset requests, please try again later.',
    retryAfter: 3600
  },
  standardHeaders: true,
  legacyHeaders: false,
  skipSuccessfulRequests: false
});

// Dynamic rate limiter based on user role
export const createRoleBasedRateLimiter = (limits: Record<string, number>) => {
  return rateLimit({
    windowMs: config.RATE_LIMIT_WINDOW_MS,
    max: (req: Request): number => {
      const userRole = req.user?.role || 'GUEST';
      return limits[userRole] || limits['GUEST'] || 10;
    },
    message: {
      error: 'Rate Limit Exceeded',
      message: 'Rate limit exceeded for your user tier.',
      retryAfter: Math.ceil(config.RATE_LIMIT_WINDOW_MS / 1000)
    },
    standardHeaders: true,
    legacyHeaders: false,
    keyGenerator: (req: Request): string => {
      return req.user?.id || req.ip;
    }
  });
};

// Export configured rate limiters for different user roles
export const roleBasedRateLimiter = createRoleBasedRateLimiter({
  'ADMIN': 1000,
  'MODERATOR': 500,
  'USER': 100,
  'GUEST': 20
});

