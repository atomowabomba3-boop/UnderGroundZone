const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3000;
const PUBLIC_DIR = __dirname;
const BACKEND_URL = process.env.BACKEND_URL || 'https://web-production-23ff3.up.railway.app';

const mime = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.txt': 'text/plain'
};

function sendFile(res, filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const type = mime[ext] || 'application/octet-stream';
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.statusCode = 404;
      res.setHeader('Content-Type', 'text/plain');
      res.end('Not found');
      return;
    }
    res.statusCode = 200;
    res.setHeader('Content-Type', type);
    res.end(data);
  });
}

function proxyRequest(req, res) {
  const target = BACKEND_URL.replace(/\/$/, '') + req.url;
  const isHttps = target.startsWith('https://');
  const client = isHttps ? https : http;

  // handle preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type,Authorization',
      'Access-Control-Max-Age': '86400'
    });
    return res.end();
  }

  const parsed = new URL(target);
  const headers = Object.assign({}, req.headers);
  // remove host to avoid host mismatch
  delete headers.host;

  const opts = {
    protocol: parsed.protocol,
    hostname: parsed.hostname,
    port: parsed.port || (parsed.protocol === 'https:' ? 443 : 80),
    path: parsed.pathname + parsed.search,
    method: req.method,
    headers
  };

  const proxy = client.request(opts, (pres) => {
    res.writeHead(pres.statusCode, Object.assign({}, pres.headers, { 'Access-Control-Allow-Origin': '*' }));
    pres.pipe(res, { end: true });
  });

  proxy.on('error', (e) => {
    console.error('Proxy error', e);
    res.writeHead(502, { 'Content-Type': 'text/plain' });
    res.end('Bad gateway');
  });

  req.pipe(proxy, { end: true });
}

const server = http.createServer((req, res) => {
  try {
    let reqPath = decodeURI(req.url.split('?')[0]);

    // If request targets API endpoints, proxy to backend to avoid CORS
    if (/^\/(me|ebooks|giveaway|ranking|admin|download)($|\/)/.test(reqPath)) {
      return proxyRequest(req, res);
    }

    if (reqPath === '/' || reqPath === '') reqPath = '/index.html';
    const safePath = path.normalize(reqPath).replace(/^\.+/, '');
    const filePath = path.join(PUBLIC_DIR, safePath);
    if (!filePath.startsWith(PUBLIC_DIR)) {
      res.statusCode = 400; res.end('Bad request'); return;
    }
    fs.stat(filePath, (err, stats) => {
      if (!err && stats.isFile()) return sendFile(res, filePath);
      const alt = path.join(filePath, 'index.html');
      fs.stat(alt, (e2, s2) => {
        if (!e2 && s2.isFile()) return sendFile(res, alt);
        res.statusCode = 404; res.setHeader('Content-Type','text/plain'); res.end('Not found');
      });
    });
  } catch (e) {
    console.error('Server error', e);
    res.statusCode = 500; res.setHeader('Content-Type','text/plain'); res.end('Server error');
  }
});

server.listen(PORT, () => {
  console.log(`Static/proxy server listening on port ${PORT}, proxy -> ${BACKEND_URL}`);
});
