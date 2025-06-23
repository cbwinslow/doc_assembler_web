import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { PrismaClient } from '@prisma/client';
import { config, jwtConfig } from '@/config/config.js';
import { logger } from '@/utils/logger.js';

const prisma = new PrismaClient();

// Extend Express Request interface to include user
declare global {
  namespace Express {
    interface Request {
      user?: {
        id: string;
        email: string;
        role: string;
        isVerified: boolean;
      };
      token?: string;
    }
  }
}

interface JwtPayload {
  userId: string;
  email: string;
  role: string;
  sessionId?: string;
  iat: number;
  exp: number;
}

export const authMiddleware = async (
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    // Extract token from Authorization header
    const authHeader = req.headers.authorization;
    if (!authHeader?.startsWith('Bearer ')) {
      res.status(401).json({
        error: 'Unauthorized',
        message: 'No valid authorization token provided'
      });
      return;
    }

    const token = authHeader.substring(7); // Remove 'Bearer ' prefix
    req.token = token;

    // Verify JWT token
    const decoded = jwt.verify(token, jwtConfig.secret) as JwtPayload;
    
    // Check if user exists and is active
    const user = await prisma.user.findUnique({
      where: { id: decoded.userId },
      select: {
        id: true,
        email: true,
        role: true,
        isVerified: true,
        isActive: true
      }
    });

    if (!user) {
      res.status(401).json({
        error: 'Unauthorized',
        message: 'User not found'
      });
      return;
    }

    if (!user.isActive) {
      res.status(401).json({
        error: 'Unauthorized',
        message: 'User account is deactivated'
      });
      return;
    }

    // Check if session exists (if sessionId provided in token)
    if (decoded.sessionId) {
      const session = await prisma.session.findUnique({
        where: { id: decoded.sessionId }
      });

      if (!session || session.expiresAt < new Date()) {
        res.status(401).json({
          error: 'Unauthorized',
          message: 'Session expired'
        });
        return;
      }
    }

    // Add user to request object
    req.user = {
      id: user.id,
      email: user.email,
      role: user.role,
      isVerified: user.isVerified
    };

    next();
  } catch (error) {
    logger.error('Authentication error:', error);
    
    if (error instanceof jwt.JsonWebTokenError) {
      res.status(401).json({
        error: 'Unauthorized',
        message: 'Invalid token'
      });
      return;
    }

    if (error instanceof jwt.TokenExpiredError) {
      res.status(401).json({
        error: 'Unauthorized',
        message: 'Token expired'
      });
      return;
    }

    res.status(500).json({
      error: 'Internal Server Error',
      message: 'Authentication failed'
    });
  }
};

export const optionalAuthMiddleware = async (
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader?.startsWith('Bearer ')) {
      next();
      return;
    }

    // If token exists, validate it
    await authMiddleware(req, res, next);
  } catch (error) {
    // If optional auth fails, continue without user
    next();
  }
};

export const requireRole = (roles: string | string[]) => {
  const roleArray = Array.isArray(roles) ? roles : [roles];
  
  return (req: Request, res: Response, next: NextFunction): void => {
    if (!req.user) {
      res.status(401).json({
        error: 'Unauthorized',
        message: 'Authentication required'
      });
      return;
    }

    if (!roleArray.includes(req.user.role)) {
      res.status(403).json({
        error: 'Forbidden',
        message: 'Insufficient permissions'
      });
      return;
    }

    next();
  };
};

export const requireVerified = (req: Request, res: Response, next: NextFunction): void => {
  if (!req.user) {
    res.status(401).json({
      error: 'Unauthorized',
      message: 'Authentication required'
    });
    return;
  }

  if (!req.user.isVerified) {
    res.status(403).json({
      error: 'Forbidden',
      message: 'Email verification required'
    });
    return;
  }

  next();
};

export const requireOwnership = (entityIdParam: string = 'id') => {
  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    if (!req.user) {
      res.status(401).json({
        error: 'Unauthorized',
        message: 'Authentication required'
      });
      return;
    }

    const entityId = req.params[entityIdParam];
    if (!entityId) {
      res.status(400).json({
        error: 'Bad Request',
        message: 'Entity ID required'
      });
      return;
    }

    try {
      // Check ownership based on the route
      const path = req.route?.path || req.path;
      let entity;

      if (path.includes('/documents')) {
        entity = await prisma.document.findUnique({
          where: { id: entityId },
          select: { userId: true }
        });
      } else if (path.includes('/projects')) {
        entity = await prisma.project.findUnique({
          where: { id: entityId },
          select: { userId: true }
        });
      } else if (path.includes('/templates')) {
        entity = await prisma.template.findUnique({
          where: { id: entityId },
          select: { userId: true }
        });
      }

      if (!entity) {
        res.status(404).json({
          error: 'Not Found',
          message: 'Entity not found'
        });
        return;
      }

      // Allow access if user is owner or admin
      if (entity.userId !== req.user.id && req.user.role !== 'ADMIN') {
        res.status(403).json({
          error: 'Forbidden',
          message: 'Access denied'
        });
        return;
      }

      next();
    } catch (error) {
      logger.error('Ownership check error:', error);
      res.status(500).json({
        error: 'Internal Server Error',
        message: 'Failed to verify ownership'
      });
    }
  };
};

export const apiKeyAuth = async (
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const apiKey = req.headers['x-api-key'] as string;
    if (!apiKey) {
      res.status(401).json({
        error: 'Unauthorized',
        message: 'API key required'
      });
      return;
    }

    const keyRecord = await prisma.apiKey.findUnique({
      where: { key: apiKey },
      include: { user: true }
    });

    if (!keyRecord || !keyRecord.isActive) {
      res.status(401).json({
        error: 'Unauthorized',
        message: 'Invalid API key'
      });
      return;
    }

    if (keyRecord.expiresAt && keyRecord.expiresAt < new Date()) {
      res.status(401).json({
        error: 'Unauthorized',
        message: 'API key expired'
      });
      return;
    }

    if (!keyRecord.user.isActive) {
      res.status(401).json({
        error: 'Unauthorized',
        message: 'User account is deactivated'
      });
      return;
    }

    // Update last used timestamp
    await prisma.apiKey.update({
      where: { id: keyRecord.id },
      data: { lastUsedAt: new Date() }
    });

    // Add user to request object
    req.user = {
      id: keyRecord.user.id,
      email: keyRecord.user.email,
      role: keyRecord.user.role,
      isVerified: keyRecord.user.isVerified
    };

    next();
  } catch (error) {
    logger.error('API key authentication error:', error);
    res.status(500).json({
      error: 'Internal Server Error',
      message: 'Authentication failed'
    });
  }
};

