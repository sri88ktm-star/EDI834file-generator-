const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { resolveOutputPath } = require('../src/server');

test('resolveOutputPath appends filename when directory path is supplied', () => {
  const dir = path.join(__dirname, '..', 'generated');
  fs.mkdirSync(dir, { recursive: true });
  const resolved = resolveOutputPath(dir);

  assert.equal(path.dirname(resolved), dir);
  assert.ok(path.basename(resolved).startsWith('enrollment_'));
  assert.equal(path.extname(resolved), '.edi');
});

test('resolveOutputPath appends .edi when extension missing', () => {
  const out = resolveOutputPath(path.join(__dirname, '..', 'generated', 'my_output'));
  assert.equal(path.extname(out), '.edi');
  assert.ok(out.endsWith('my_output.edi'));
});
