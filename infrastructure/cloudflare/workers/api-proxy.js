/**
 * DocAssembler API Proxy Worker
 * 
 * This Cloudflare Worker provides:
 * - API request proxying and load balancing
 * - Intelligent caching for GET requests
 * - Rate limiting and security
 * - Request/response transformation
 * - Analytics and monitoring
 */

// Configuration
const CONFIG = {
  // Backend servers
  BACKEND_SERVERS: [
    'https://backend-1.internal.docassembler.com:5000',
    'https://backend-2.internal.docassembler.com:5000'
  ],
  
  // Cache settings
  CACHE_TTL: {
    'GET /api/documents': 300,      // 5 minutes
    'GET /api/analytics': 600,      // 10 minutes
    'GET /api/health': 60,          // 1 minute
    'default': 0                    // No cache
  },
  
  // Rate limiting
  RATE_LIMITS: {
    'POST /api/auth/login': { limit: 5, window: 900 },    // 5 per 15 minutes
    'POST /api/documents/upload': { limit: 10, window: 60 }, // 10 per minute
    'default': { limit: 100, window: 60 }                 // 100 per minute
  },
  
  // CORS settings
  CORS_ORIGINS: [
    'https://app.docassembler.com',
    'https://www.docassembler.com',
    'http://localhost:3000', // Development
    'http://localhost:5173'  // Vite dev server
  ]
};

// Main request handler
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

/**
 * Main request handler
 */
async function handleRequest(request) {
  try {
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return handleCORS(request);
    }

    // Extract request info
    const url = new URL(request.url);
    const method = request.method;
    const path = url.pathname;
    const routeKey = `${method} ${path}`;
    
    // Check rate limits
    const rateLimitResponse = await checkRateLimit(request, routeKey);
    if (rateLimitResponse) {
      return rateLimitResponse;
    }

    // Check cache for GET requests
    if (method === 'GET') {
      const cachedResponse = await getCachedResponse(request);
      if (cachedResponse) {
        return addCORSHeaders(cachedResponse);
      }
    }

    // Select backend server
    const backendUrl = await selectBackendServer();
    
    // Create proxied request
    const proxyRequest = new Request(backendUrl + path + url.search, {
      method: request.method,
      headers: request.headers,
      body: request.body
    });

    // Add internal headers
    proxyRequest.headers.set('X-Forwarded-For', request.headers.get('CF-Connecting-IP'));
    proxyRequest.headers.set('X-Forwarded-Proto', 'https');
    proxyRequest.headers.set('X-Real-IP', request.headers.get('CF-Connecting-IP'));

    // Forward request to backend
    const response = await fetch(proxyRequest);

    // Transform response
    const transformedResponse = await transformResponse(response, request);

    // Cache GET responses
    if (method === 'GET' && response.ok) {
      await cacheResponse(request, transformedResponse.clone());
    }

    // Add CORS headers and return
    return addCORSHeaders(transformedResponse);

  } catch (error) {
    console.error('Worker error:', error);
    return new Response(JSON.stringify({
      error: 'Internal Server Error',
      message: 'An unexpected error occurred'
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...getCORSHeaders()
      }
    });
  }
}

/**
 * Handle CORS preflight requests
 */
function handleCORS(request) {
  const origin = request.headers.get('Origin');
  
  if (CONFIG.CORS_ORIGINS.includes(origin)) {
    return new Response(null, {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': origin,
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Max-Age': '86400'
      }
    });
  }

  return new Response('CORS not allowed', { status: 403 });
}

/**
 * Get CORS headers for response
 */
function getCORSHeaders(request = null) {
  const origin = request?.headers.get('Origin') || CONFIG.CORS_ORIGINS[0];
  
  return {
    'Access-Control-Allow-Origin': CONFIG.CORS_ORIGINS.includes(origin) ? origin : CONFIG.CORS_ORIGINS[0],
    'Access-Control-Allow-Credentials': 'true',
    'Access-Control-Expose-Headers': 'X-Total-Count, X-Page-Count'
  };
}

/**
 * Add CORS headers to response
 */
function addCORSHeaders(response, request = null) {
  const newResponse = new Response(response.body, response);
  
  Object.entries(getCORSHeaders(request)).forEach(([key, value]) => {
    newResponse.headers.set(key, value);
  });

  return newResponse;
}

/**
 * Check rate limits
 */
async function checkRateLimit(request, routeKey) {
  const clientIP = request.headers.get('CF-Connecting-IP');
  const rateLimit = CONFIG.RATE_LIMITS[routeKey] || CONFIG.RATE_LIMITS.default;
  
  const key = `rate_limit:${clientIP}:${routeKey}`;
  const currentCount = await API_CACHE.get(key);
  
  if (currentCount && parseInt(currentCount) >= rateLimit.limit) {
    return new Response(JSON.stringify({
      error: 'Rate Limit Exceeded',
      message: `Too many requests. Limit: ${rateLimit.limit} per ${rateLimit.window} seconds`
    }), {
      status: 429,
      headers: {
        'Content-Type': 'application/json',
        'Retry-After': rateLimit.window.toString(),
        ...getCORSHeaders()
      }
    });
  }

  // Increment counter
  const newCount = currentCount ? parseInt(currentCount) + 1 : 1;
  await API_CACHE.put(key, newCount.toString(), { expirationTtl: rateLimit.window });
  
  return null;
}

/**
 * Get cached response
 */
async function getCachedResponse(request) {
  const cacheKey = await getCacheKey(request);
  const cached = await API_CACHE.get(cacheKey);
  
  if (cached) {
    const cachedData = JSON.parse(cached);
    return new Response(cachedData.body, {
      status: cachedData.status,
      headers: {
        ...cachedData.headers,
        'X-Cache': 'HIT',
        'X-Cache-Age': Math.floor((Date.now() - cachedData.timestamp) / 1000).toString()
      }
    });
  }
  
  return null;
}

/**
 * Cache response
 */
async function cacheResponse(request, response) {
  const url = new URL(request.url);
  const routeKey = `${request.method} ${url.pathname}`;
  const ttl = CONFIG.CACHE_TTL[routeKey] || CONFIG.CACHE_TTL.default;
  
  if (ttl > 0) {
    const cacheKey = await getCacheKey(request);
    const responseBody = await response.text();
    
    const cacheData = {
      body: responseBody,
      status: response.status,
      headers: Object.fromEntries(response.headers.entries()),
      timestamp: Date.now()
    };
    
    await API_CACHE.put(cacheKey, JSON.stringify(cacheData), { expirationTtl: ttl });
  }
}

/**
 * Generate cache key
 */
async function getCacheKey(request) {
  const url = new URL(request.url);
  const keyData = `${request.method}:${url.pathname}:${url.search}`;
  
  const encoder = new TextEncoder();
  const data = encoder.encode(keyData);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  
  return `cache:${hashHex}`;
}

/**
 * Select backend server (simple round-robin)
 */
async function selectBackendServer() {
  const counter = await API_CACHE.get('backend_counter') || '0';
  const serverIndex = parseInt(counter) % CONFIG.BACKEND_SERVERS.length;
  
  await API_CACHE.put('backend_counter', (parseInt(counter) + 1).toString(), { expirationTtl: 3600 });
  
  return CONFIG.BACKEND_SERVERS[serverIndex];
}

/**
 * Transform response (add custom headers, modify content, etc.)
 */
async function transformResponse(response, request) {
  const newResponse = new Response(response.body, response);
  
  // Add security headers
  newResponse.headers.set('X-Content-Type-Options', 'nosniff');
  newResponse.headers.set('X-Frame-Options', 'DENY');
  newResponse.headers.set('X-XSS-Protection', '1; mode=block');
  newResponse.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  
  // Add cache control for static assets
  const url = new URL(request.url);
  if (url.pathname.includes('/assets/') || url.pathname.includes('/static/')) {
    newResponse.headers.set('Cache-Control', 'public, max-age=2592000'); // 30 days
  }
  
  // Add API version header
  newResponse.headers.set('X-API-Version', '1.0');
  newResponse.headers.set('X-Powered-By', 'Cloudflare Workers');
  
  return newResponse;
}

/**
 * Health check endpoint
 */
async function handleHealthCheck() {
  const healthData = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    region: 'global',
    uptime: Date.now()
  };
  
  return new Response(JSON.stringify(healthData), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      ...getCORSHeaders()
    }
  });
}

/**
 * Analytics and monitoring
 */
async function logRequest(request, response, startTime) {
  const endTime = Date.now();
  const duration = endTime - startTime;
  
  const logData = {
    timestamp: new Date().toISOString(),
    method: request.method,
    url: request.url,
    status: response.status,
    duration,
    userAgent: request.headers.get('User-Agent'),
    ip: request.headers.get('CF-Connecting-IP'),
    country: request.headers.get('CF-IPCountry'),
    cacheStatus: response.headers.get('X-Cache') || 'MISS'
  };
  
  // Store in KV for analytics (with TTL to prevent storage buildup)
  const logKey = `log:${Date.now()}:${Math.random().toString(36).substr(2, 9)}`;
  await API_CACHE.put(logKey, JSON.stringify(logData), { expirationTtl: 86400 }); // 24 hours
}

