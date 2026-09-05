const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = __dirname;
const PORT = Number(process.env.PORT || 10000);
const ADMIN_USER = process.env.ADMIN_USER;
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD;

if (!ADMIN_USER || !ADMIN_PASSWORD) {
  console.error('Missing ADMIN_USER or ADMIN_PASSWORD environment variable.');
  process.exit(1);
}

const MIME = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.pdf': 'application/pdf',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2',
  '.mp4': 'video/mp4',
  '.wasm': 'application/wasm'
};

function unauthorized(response) {
  response.writeHead(401, {
    'WWW-Authenticate': 'Basic realm="Amine Portfolio Admin", charset="UTF-8"',
    'Cache-Control': 'no-store'
  });
  response.end('Authentication required');
}

function isAdmin(request) {
  const value = request.headers.authorization || '';
  if (!value.startsWith('Basic ')) return false;
  let decoded;
  try {
    decoded = Buffer.from(value.slice(6), 'base64').toString('utf8');
  } catch {
    return false;
  }
  const separator = decoded.indexOf(':');
  if (separator < 0) return false;
  const user = Buffer.from(decoded.slice(0, separator));
  const password = Buffer.from(decoded.slice(separator + 1));
  const expectedUser = Buffer.from(ADMIN_USER);
  const expectedPassword = Buffer.from(ADMIN_PASSWORD);
  return user.length === expectedUser.length &&
    password.length === expectedPassword.length &&
    crypto.timingSafeEqual(user, expectedUser) &&
    crypto.timingSafeEqual(password, expectedPassword);
}

function sendFile(response, filePath) {
  fs.stat(filePath, (error, stats) => {
    if (error || !stats.isFile()) {
      response.writeHead(404);
      response.end('Not found');
      return;
    }
    response.writeHead(200, {
      'Content-Type': MIME[path.extname(filePath).toLowerCase()] || 'application/octet-stream',
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'same-origin'
    });
    fs.createReadStream(filePath).pipe(response);
  });
}

const server = http.createServer((request, response) => {
  const requestPath = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
  if (requestPath === '/admin.html') {
    if (!isAdmin(request)) {
      unauthorized(response);
      return;
    }
  }
  if (requestPath.endsWith('.py') || requestPath.startsWith('/scripts/') || requestPath.startsWith('/.')) {
    response.writeHead(404);
    response.end('Not found');
    return;
  }
  const relativePath = requestPath === '/' ? 'index.html' : requestPath.slice(1);
  const filePath = path.resolve(ROOT, relativePath);
  if (filePath !== ROOT && !filePath.startsWith(ROOT + path.sep)) {
    response.writeHead(400);
    response.end('Bad request');
    return;
  }
  sendFile(response, filePath);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Amine portfolio listening on port ${PORT}`);
});