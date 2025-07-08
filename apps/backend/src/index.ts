import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import compression from 'compression';
import { createServer } from 'http';
import { Server } from 'socket.io';
import dotenv from 'dotenv';
import swaggerJsdoc from 'swagger-jsdoc';
import swaggerUi from 'swagger-ui-express';

import { config } from '@/config/config.js';
import { logger } from '@/utils/logger.js';
import { errorHandler } from '@/middleware/errorHandler.js';
import { authMiddleware } from '@/middleware/auth.js';
import { rateLimiter } from '@/middleware/rateLimiter.js';

// Routes
import authRoutes from '@/routes/auth.js';
import userRoutes from '@/routes/users.js';
import documentRoutes from '@/routes/documents.js';
import searchRoutes from '@/routes/search.js';
import analyticsRoutes from '@/routes/analytics.js';
import ragRoutes from '@/routes/rag.js';

// Load environment variables
dotenv.config();

// Create Express app
const app = express();
const httpServer = createServer(app);

// Initialize Socket.IO
const io = new Server(httpServer, {
  cors: {
    origin: config.CLIENT_URL,
    methods: ['GET', 'POST']
  }
});

// Swagger configuration
const swaggerOptions = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Document Assembler API',
      version: '1.0.0',
      description: 'Modern document assembly platform with AI capabilities',
    },
    servers: [
      {
        url: `http://localhost:${config.PORT}`,
        description: 'Development server',
      },
      {
        url: config.API_URL,
        description: 'Production server',
      },
    ],
    components: {
      securitySchemes: {
        bearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT',
        },
      },
    },
  },
  apis: ['./src/routes/*.ts', './src/controllers/*.ts'],
};

const swaggerSpecs = swaggerJsdoc(swaggerOptions);

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: [\"'self'\"],
      styleSrc: [\"'self'\", \"'unsafe-inline'\", 'https://fonts.googleapis.com'],
      fontSrc: [\"'self'\", 'https://fonts.gstatic.com'],
      imgSrc: [\"'self'\", 'data:', 'https:'],
      scriptSrc: [\"'self'\"],
    },
  },
}));

// CORS middleware
app.use(cors({
  origin: config.CLIENT_URL,
  credentials: true,
  optionsSuccessStatus: 200
}));

// Compression middleware
app.use(compression());

// Logging middleware
app.use(morgan('combined', {
  stream: { write: (message) => logger.info(message.trim()) }
}));

// Body parsing middleware
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Rate limiting
app.use(rateLimiter);

// API Documentation
app.use('/api/docs', swaggerUi.serve, swaggerUi.setup(swaggerSpecs, {
  explorer: true,
  customCss: '.swagger-ui .topbar { display: none }',
  customSiteTitle: 'Document Assembler API Documentation'
}));

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'OK',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: config.NODE_ENV,
    version: process.env.npm_package_version || '1.0.0'
  });
});

// API Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', authMiddleware, userRoutes);
app.use('/api/documents', authMiddleware, documentRoutes);
app.use('/api/search', authMiddleware, searchRoutes);
app.use('/api/analytics', authMiddleware, analyticsRoutes);
app.use('/api/rag', authMiddleware, ragRoutes);

// Socket.IO connection handling
io.on('connection', (socket) => {
  logger.info(`Socket connected: ${socket.id}`);
  
  socket.on('join_room', (room) => {
    socket.join(room);
    logger.info(`Socket ${socket.id} joined room: ${room}`);
  });
  
  socket.on('leave_room', (room) => {
    socket.leave(room);
    logger.info(`Socket ${socket.id} left room: ${room}`);
  });
  
  socket.on('disconnect', () => {
    logger.info(`Socket disconnected: ${socket.id}`);
  });
});

// Make io available to routes
app.set('io', io);

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Route ${req.originalUrl} not found`,
    timestamp: new Date().toISOString()
  });
});

// Global error handler
app.use(errorHandler);

// Graceful shutdown
const gracefulShutdown = (signal: string) => {
  logger.info(`Received ${signal}. Starting graceful shutdown...`);
  
  httpServer.close(() => {
    logger.info('HTTP server closed');
    process.exit(0);
  });
  
  setTimeout(() => {
    logger.error('Could not close connections in time, forcefully shutting down');
    process.exit(1);
  }, 10000);
};

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// Start server
const PORT = config.PORT || 3001;
httpServer.listen(PORT, () => {
  logger.info(`🚀 Server running on port ${PORT}`);
  logger.info(`📚 API Documentation: http://localhost:${PORT}/api/docs`);
  logger.info(`🏥 Health check: http://localhost:${PORT}/health`);
  logger.info(`🌍 Environment: ${config.NODE_ENV}`);
});

export default app;

