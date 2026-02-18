const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { generate834FromRows, formatDate } = require('../src/generator');

const outFile = path.join(__dirname, '..', 'generated', 'test_output.edi');

test('generate834FromRows writes expected member loop segments and omits situational loops by default', () => {
  const rows = [
    {
      'Sender ID': 'S1',
      'Receiver ID': 'R1',
      Group: 'G1',
      'Sub Group ID': '1001',
      'Class Plan ID': '1004',
      Plan: 'P1',
      Product: 'PR1',
      'Member ID': 'SUB1',
      'Relationship Code': '18',
      'Maintenance Type Code': '21',
      'Maintenance Reason Code': 'XN',
      'Last Name': 'DOE',
      'First Name': 'JOHN',
      'Eligibility Begin Date': '01/01/2024',
      'Eligibility Date': '01/01/2024',
      'Date of Birth': '10/02/1985'
    }
  ];

  const result = generate834FromRows(rows, outFile);
  const content = fs.readFileSync(outFile, 'utf8');

  assert.equal(result.memberCount, 1);
  assert.match(content, /INS\*Y\*18\*21\*\*A\*\*\*FT\*\*N\*\*~/);
  assert.match(content, /REF\*17\*1001~/);
  assert.match(content, /REF\*QQ\*1004~/);
  assert.match(content, /DTP\*356\*D8\*01012024~/);
  assert.match(content, /DMG\*D8\*10021985\*/);
  assert.match(content, /DTP\*348\*D8\*01012024~/);
  assert.doesNotMatch(content, /DTP\*348\*D8\*01012024~[\s\S]*DTP\*348\*D8\*01012024~/);
  assert.doesNotMatch(content, /REF\*1L\*PR1~/);
  assert.doesNotMatch(content, /NM1\*P3\*/);
});

test('formatDate keeps MMDDYYYY and converts YYYYMMDD', () => {
  assert.equal(formatDate('10022025'), '10022025');
  assert.equal(formatDate('20250131'), '01312025');
  assert.equal(formatDate('2025-01-31'), '01312025');
});
