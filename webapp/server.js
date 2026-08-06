const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3000;
const PUBLIC_DIR = __dirname;
const BACKEND_URL = (process.env.BACKEND_URL || 'https://web-production-23ff3.up.railway.app').replace(/\/+$/, '');

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

async function getRequestBody(req) {
  return await new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

async function proxyRequest(req, res) {
  try {
    // Handle CORS preflight quickly
    if (req.method === 'OPTIONS') {
      res.writeHead(204, {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Max-Age': '86400'
      });
      return res.end();
    }

    const target = BACKEND_URL + req.url;

    const bodyBuf = await getRequestBody(req);

    // Copy headers but avoid host
    const headers = Object.assign({}, req.headers);
    delete headers.host;

    // If body is empty, don't pass it to fetch
    const fetchOptions = {
      method: req.method,
      headers,
      redirect: 'manual'
    };
    if (bodyBuf && bodyBuf.length) fetchOptions.body = bodyBuf;

    const pres = await fetch(target, fetchOptions);

    // propagate status and headers
    const outHeaders = {};
    pres.headers.forEach((v, k) => { outHeaders[k] = v; });
    // allow CORS
    outHeaders['access-control-allow-origin'] = '*';

    res.writeHead(pres.status, outHeaders);
    // stream body
    const arrayBuffer = await pres.arrayBuffer();
    res.end(Buffer.from(arrayBuffer));
  } catch (e) {
    console.error('Proxy error', e);
    res.writeHead(502, { 'Content-Type': 'text/plain', 'Access-Control-Allow-Origin': '*' });
    res.end('Bad gateway');
  }
}

const server = http.createServer(async (req, res) => {
  try {
    let reqPath = decodeURI(req.url.split('?')[0]);

    // Proxy API endpoints to backend to avoid CORS
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
