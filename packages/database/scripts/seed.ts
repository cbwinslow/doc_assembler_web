import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';
import { v4 as uuidv4 } from 'uuid';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Starting database seed...');

  // Clean existing data (in development only)
  if (process.env.NODE_ENV === 'development') {
    console.log('🧹 Cleaning existing data...');
    await prisma.activity.deleteMany();
    await prisma.processingJob.deleteMany();
    await prisma.document.deleteMany();
    await prisma.template.deleteMany();
    await prisma.project.deleteMany();
    await prisma.teamMember.deleteMany();
    await prisma.team.deleteMany();
    await prisma.tag.deleteMany();
    await prisma.apiKey.deleteMany();
    await prisma.session.deleteMany();
    await prisma.refreshToken.deleteMany();
    await prisma.user.deleteMany();
  }

  // Create admin user
  console.log('👤 Creating admin user...');
  const adminPassword = await bcrypt.hash('Temp1234!', 10);
  const adminUser = await prisma.user.create({
    data: {
      email: 'admin@docassembler.dev',
      username: 'admin',
      firstName: 'Admin',
      lastName: 'User',
      password: adminPassword,
      role: 'ADMIN',
      isVerified: true,
      bio: 'System Administrator',
      company: 'Doc Assembler',
      jobTitle: 'System Administrator',
      preferences: {
        theme: 'dark',
        notifications: true,
        language: 'en'
      }
    }
  });

  // Create demo user
  console.log('👤 Creating demo user...');
  const demoPassword = await bcrypt.hash('demo123', 10);
  const demoUser = await prisma.user.create({
    data: {
      email: 'demo@docassembler.dev',
      username: 'demo',
      firstName: 'Demo',
      lastName: 'User',
      password: demoPassword,
      role: 'USER',
      isVerified: true,
      bio: 'Demo user for testing the platform',
      company: 'Demo Corp',
      jobTitle: 'Content Manager',
      preferences: {
        theme: 'light',
        notifications: true,
        language: 'en'
      }
    }
  });

  // Create sample team
  console.log('👥 Creating sample team...');
  const team = await prisma.team.create({
    data: {
      name: 'Content Team',
      description: 'Team responsible for document creation and management',
      settings: {
        allowExternalSharing: true,
        requireApproval: false
      }
    }
  });

  // Add users to team
  await prisma.teamMember.createMany({
    data: [
      {
        userId: adminUser.id,
        teamId: team.id,
        role: 'OWNER'
      },
      {
        userId: demoUser.id,
        teamId: team.id,
        role: 'MEMBER'
      }
    ]
  });

  // Create sample project
  console.log('📁 Creating sample project...');
  const project = await prisma.project.create({
    data: {
      name: 'Documentation Portal',
      description: 'Comprehensive documentation for our platform',
      userId: adminUser.id,
      teamId: team.id,
      settings: {
        isPublic: false,
        allowComments: true,
        autoProcess: true
      },
      metadata: {
        priority: 'high',
        deadline: '2025-12-31'
      }
    }
  });

  // Create sample tags
  console.log('🏷️ Creating sample tags...');
  const tags = await prisma.tag.createMany({
    data: [
      { name: 'documentation', color: '#3B82F6' },
      { name: 'api', color: '#10B981' },
      { name: 'tutorial', color: '#F59E0B' },
      { name: 'reference', color: '#8B5CF6' },
      { name: 'draft', color: '#6B7280' },
      { name: 'review', color: '#EF4444' }
    ]
  });

  // Get created tags for documents
  const createdTags = await prisma.tag.findMany({
    where: {
      name: { in: ['documentation', 'api', 'tutorial'] }
    }
  });

  // Create sample documents
  console.log('📄 Creating sample documents...');
  const documents = await prisma.document.createMany({
    data: [
      {
        title: 'API Documentation',
        description: 'Complete API reference for developers',
        type: 'MARKDOWN',
        status: 'COMPLETED',
        filename: 'api-docs.md',
        originalName: 'API Documentation.md',
        mimeType: 'text/markdown',
        size: 15420,
        checksum: 'sha256:abc123',
        storageProvider: 'CLOUDFLARE_R2',
        storagePath: '/docs/api-docs.md',
        content: '# API Documentation\n\nThis is a comprehensive API reference...',
        extractedText: 'API Documentation This is a comprehensive API reference...',
        summary: 'API documentation covering all endpoints and authentication methods',
        metadata: {
          wordCount: 1542,
          readingTime: '7 minutes',
          lastReviewed: '2025-06-23'
        },
        aiMetadata: {
          topics: ['api', 'authentication', 'endpoints'],
          sentiment: 'neutral',
          complexity: 'intermediate'
        },
        userId: adminUser.id,
        projectId: project.id
      },
      {
        title: 'User Guide',
        description: 'Getting started guide for new users',
        type: 'PDF',
        status: 'PROCESSING',
        filename: 'user-guide.pdf',
        originalName: 'User Guide.pdf',
        mimeType: 'application/pdf',
        size: 2480000,
        checksum: 'sha256:def456',
        storageProvider: 'CLOUDFLARE_R2',
        storagePath: '/docs/user-guide.pdf',
        metadata: {
          pages: 24,
          version: '2.1'
        },
        userId: demoUser.id,
        projectId: project.id
      }
    ]
  });

  // Create sample templates
  console.log('📋 Creating sample templates...');
  await prisma.template.createMany({
    data: [
      {
        name: 'Project Report Template',
        description: 'Standard template for project status reports',
        type: 'DOCUMENT',
        category: 'Reports',
        content: {
          sections: [
            { name: 'Executive Summary', required: true },
            { name: 'Project Status', required: true },
            { name: 'Key Metrics', required: true },
            { name: 'Next Steps', required: true }
          ],
          layout: 'standard'
        },
        schema: {
          properties: {
            projectName: { type: 'string', required: true },
            reportDate: { type: 'date', required: true },
            status: { type: 'enum', values: ['on-track', 'at-risk', 'delayed'] }
          }
        },
        variables: [
          'projectName',
          'reportDate',
          'status',
          'metrics'
        ],
        isPublic: true,
        userId: adminUser.id,
        projectId: project.id
      },
      {
        name: 'Meeting Notes Template',
        description: 'Template for capturing meeting notes and action items',
        type: 'DOCUMENT',
        category: 'Meetings',
        content: {
          sections: [
            { name: 'Meeting Info', required: true },
            { name: 'Attendees', required: true },
            { name: 'Agenda', required: true },
            { name: 'Notes', required: true },
            { name: 'Action Items', required: true }
          ],
          layout: 'structured'
        },
        schema: {
          properties: {
            meetingTitle: { type: 'string', required: true },
            date: { type: 'date', required: true },
            attendees: { type: 'array', required: true }
          }
        },
        variables: [
          'meetingTitle',
          'date',
          'attendees',
          'agenda'
        ],
        isPublic: true,
        userId: demoUser.id
      }
    ]
  });

  // Create sample processing jobs
  console.log('⚙️ Creating sample processing jobs...');
  const sampleDocument = await prisma.document.findFirst({
    where: { title: 'User Guide' }
  });

  if (sampleDocument) {
    await prisma.processingJob.createMany({
      data: [
        {
          documentId: sampleDocument.id,
          type: 'TEXT_EXTRACTION',
          status: 'COMPLETED',
          input: { extractText: true, preserveFormatting: false },
          output: { textLength: 15420, success: true },
          progress: 100,
          queueId: uuidv4(),
          priority: 5,
          attempts: 1,
          startedAt: new Date(Date.now() - 300000), // 5 minutes ago
          completedAt: new Date(Date.now() - 240000) // 4 minutes ago
        },
        {
          documentId: sampleDocument.id,
          type: 'EMBEDDING_GENERATION',
          status: 'IN_PROGRESS',
          input: { model: 'text-embedding-ada-002', chunkSize: 1000 },
          output: {},
          progress: 60,
          queueId: uuidv4(),
          priority: 3,
          attempts: 1,
          startedAt: new Date(Date.now() - 120000) // 2 minutes ago
        }
      ]
    });
  }

  // Create sample analytics data
  console.log('📊 Creating sample analytics...');
  const now = new Date();
  const analyticsData = [];
  
  for (let i = 0; i < 30; i++) {
    const date = new Date(now.getTime() - (i * 24 * 60 * 60 * 1000));
    analyticsData.push(
      {
        metric: 'documents_uploaded',
        value: Math.floor(Math.random() * 10) + 1,
        dimensions: { date: date.toISOString().split('T')[0] },
        timestamp: date
      },
      {
        metric: 'processing_jobs_completed',
        value: Math.floor(Math.random() * 20) + 5,
        dimensions: { date: date.toISOString().split('T')[0] },
        timestamp: date
      },
      {
        metric: 'active_users',
        value: Math.floor(Math.random() * 50) + 10,
        dimensions: { date: date.toISOString().split('T')[0] },
        timestamp: date
      }
    );
  }

  await prisma.analytics.createMany({
    data: analyticsData
  });

  // Create sample webhook
  console.log('🔗 Creating sample webhook...');
  await prisma.webhook.create({
    data: {
      url: 'https://api.example.com/webhooks/documents',
      events: ['document.created', 'document.processed', 'document.failed'],
      secret: 'webhook_secret_key_123',
      isActive: true
    }
  });

  // Create sample activities
  console.log('📝 Creating sample activities...');
  await prisma.activity.createMany({
    data: [
      {
        userId: adminUser.id,
        type: 'AUTH',
        action: 'login',
        metadata: { method: 'password' },
        ipAddress: '127.0.0.1',
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      },
      {
        userId: adminUser.id,
        type: 'PROJECT',
        action: 'created',
        entity: 'project',
        entityId: project.id,
        metadata: { projectName: 'Documentation Portal' }
      },
      {
        userId: demoUser.id,
        type: 'DOCUMENT',
        action: 'uploaded',
        entity: 'document',
        entityId: sampleDocument?.id,
        metadata: { filename: 'user-guide.pdf', size: 2480000 }
      }
    ]
  });

  console.log('✅ Database seeding completed successfully!');
  console.log('\n📊 Summary:');
  console.log(`👤 Users: ${await prisma.user.count()}`);
  console.log(`👥 Teams: ${await prisma.team.count()}`);
  console.log(`📁 Projects: ${await prisma.project.count()}`);
  console.log(`📄 Documents: ${await prisma.document.count()}`);
  console.log(`📋 Templates: ${await prisma.template.count()}`);
  console.log(`🏷️ Tags: ${await prisma.tag.count()}`);
  console.log(`⚙️ Processing Jobs: ${await prisma.processingJob.count()}`);
  console.log(`📊 Analytics Records: ${await prisma.analytics.count()}`);
  console.log(`🔗 Webhooks: ${await prisma.webhook.count()}`);
  console.log(`📝 Activities: ${await prisma.activity.count()}`);

  console.log('\n🔑 Default Login Credentials:');
  console.log('Admin: admin@docassembler.dev / Temp1234!');
  console.log('Demo: demo@docassembler.dev / demo123');
}

main()
  .catch((e) => {
    console.error('❌ Error during seed:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });

