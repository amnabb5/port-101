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

function sendFile(request, response, filePath) {
  fs.stat(filePath, (error, stats) => {
    if (error || !stats.isFile()) {
      response.writeHead(404);
      response.end('Not found');
      return;
    }
    const headers = {
      'Content-Type': MIME[path.extname(filePath).toLowerCase()] || 'application/octet-stream',
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'same-origin',
      'Accept-Ranges': 'bytes',
      'Content-Length': stats.size
    };
    const range = request.headers.range;
    if (range) {
      const match = /^bytes=(\d*)-(\d*)$/.exec(range);
      if (match) {
        const start = match[1] ? Number(match[1]) : 0;
        const requestedEnd = match[2] ? Number(match[2]) : stats.size - 1;
        const end = Math.min(requestedEnd, stats.size - 1);
        if (start <= end && start < stats.size) {
          headers['Content-Range'] = `bytes ${start}-${end}/${stats.size}`;
          headers['Content-Length'] = end - start + 1;
          response.writeHead(206, headers);
          if (request.method !== 'HEAD') fs.createReadStream(filePath, { start, end }).pipe(response);
          else response.end();
          return;
        }
      }
      response.writeHead(416, { 'Content-Range': `bytes */${stats.size}` });
      response.end();
      return;
    }
    response.writeHead(200, headers);
    if (request.method !== 'HEAD') fs.createReadStream(filePath).pipe(response);
    else response.end();
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
  sendFile(request, response, filePath);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Amine portfolio listening on port ${PORT}`);
});