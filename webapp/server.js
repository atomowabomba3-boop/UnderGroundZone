const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3000;
const PUBLIC_DIR = __dirname;

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

const server = http.createServer((req, res) => {
  try {
    let reqPath = decodeURI(req.url.split('?')[0]);
    if (reqPath === '/') reqPath = '/index.html';
    // prevent directory traversal
    const safePath = path.normalize(reqPath).replace(/^\.+/, '');
    const filePath = path.join(PUBLIC_DIR, safePath);
    if (!filePath.startsWith(PUBLIC_DIR)) {
      res.statusCode = 400; res.end('Bad request'); return;
    }
    fs.stat(filePath, (err, stats) => {
      if (!err && stats.isFile()) return sendFile(res, filePath);
      // try index.html fallback for directories
      const alt = path.join(filePath, 'index.html');
      fs.stat(alt, (e2, s2) => {
        if (!e2 && s2.isFile()) return sendFile(res, alt);
        res.statusCode = 404; res.setHeader('Content-Type','text/plain'); res.end('Not found');
      });
    });
  } catch (e) {
    res.statusCode = 500; res.setHeader('Content-Type','text/plain'); res.end('Server error');
  }
});

server.listen(PORT, () => {
  console.log(`Static server listening on port ${PORT}`);
});
