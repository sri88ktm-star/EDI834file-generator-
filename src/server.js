const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { URL } = require('node:url');
const { generate834FromExcel } = require('./generator');

const port = Number(process.env.PORT || 3000);

function serveStatic(res, filePath, contentType = 'text/html') {
  if (!fs.existsSync(filePath)) {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not found' }));
    return;
  }
  res.writeHead(200, { 'Content-Type': contentType });
  res.end(fs.readFileSync(filePath));
}

function readJson(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', (chunk) => {
      body += chunk;
    });
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch (error) {
        reject(error);
      }
    });
    req.on('error', reject);
  });
}

function resolveOutputPath(outputPath) {
  const defaultName = `enrollment_${Date.now()}.edi`;

  if (!outputPath) {
    return path.join(__dirname, '..', 'generated', defaultName);
  }

  const resolved = path.resolve(outputPath);

  if (fs.existsSync(resolved) && fs.statSync(resolved).isDirectory()) {
    return path.join(resolved, defaultName);
  }

  if (/[\\/]$/.test(outputPath)) {
    return path.join(resolved, defaultName);
  }

  if (!path.extname(resolved)) {
    return `${resolved}.edi`;
  }

  return resolved;
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  if (req.method === 'GET' && url.pathname === '/') {
    return serveStatic(res, path.join(__dirname, '..', 'public', 'index.html'));
  }

  if (req.method === 'GET' && url.pathname === '/app.js') {
    return serveStatic(res, path.join(__dirname, '..', 'public', 'app.js'), 'application/javascript');
  }

  if (req.method === 'POST' && url.pathname === '/api/generate-from-path') {
    try {
      const { excelPath, outputPath } = await readJson(req);
      if (!excelPath) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'excelPath is required' }));
        return;
      }

      const absoluteOutput = resolveOutputPath(outputPath);
      const result = generate834FromExcel(path.resolve(excelPath), absoluteOutput);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ message: 'EDI 834 generated successfully', ...result }));
    } catch (error) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: error.message }));
    }
    return;
  }

  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Route not found' }));
});

if (require.main === module) {
  server.listen(port, () => {
    console.log(`EDI 834 generator running on http://localhost:${port}`);
  });
}

module.exports = { server, resolveOutputPath };
