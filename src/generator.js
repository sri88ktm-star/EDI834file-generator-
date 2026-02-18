const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const SEGMENT_TERM = '~';
const ELEMENT_SEP = '*';

const REQUIRED_COLUMNS = [
  'Sender ID',
  'Receiver ID',
  'Group',
  'Plan',
  'Product',
  'Member ID',
  'Relationship Code',
  'Last Name',
  'First Name'
];

function formatDate(dateValue, fallback = '01012024') {
  if (!dateValue) return fallback;

  const normalized = String(dateValue).trim().replace(/[-/]/g, '');
  if (!/^\d{8}$/.test(normalized)) return fallback;

  const firstFour = Number(normalized.slice(0, 4));
  const maybeYearFirst = firstFour >= 1900 && firstFour <= 2099;

  if (maybeYearFirst) {
    const yyyy = normalized.slice(0, 4);
    const mm = normalized.slice(4, 6);
    const dd = normalized.slice(6, 8);
    return `${mm}${dd}${yyyy}`;
  }

  return normalized;
}

function formatTime(date = new Date()) {
  return `${String(date.getHours()).padStart(2, '0')}${String(date.getMinutes()).padStart(2, '0')}`;
}

function clean(value, fallback = '') {
  if (value === null || value === undefined || value === '') return fallback;
  return String(value).trim();
}

function seg(...elements) {
  return elements.join(ELEMENT_SEP) + SEGMENT_TERM;
}

function parseCsv(text) {
  const lines = text.split(/\r?\n/).filter(Boolean);
  if (lines.length < 2) return [];
  const headers = lines[0].split(',').map((h) => h.trim());
  return lines.slice(1).map((line) => {
    const cols = line.split(',');
    const row = {};
    headers.forEach((h, i) => {
      row[h] = (cols[i] || '').trim();
    });
    return row;
  });
}

function parseXlsx(filePath) {
  const script = path.join(__dirname, 'parse_xlsx.py');
  const result = spawnSync('python3', [script, filePath], { encoding: 'utf8' });
  if (result.status !== 0) {
    throw new Error(`Failed to parse XLSX: ${result.stderr || result.stdout}`);
  }
  return JSON.parse(result.stdout);
}

function validateInputRows(rows) {
  if (!rows.length) {
    throw new Error('Input has no data rows.');
  }

  const headerKeys = new Set(Object.keys(rows[0]));
  const missingColumns = REQUIRED_COLUMNS.filter((col) => !headerKeys.has(col));

  if (missingColumns.length > 0) {
    throw new Error(`Missing required input columns: ${missingColumns.join(', ')}`);
  }
}

function buildHeader(first, controlNumber) {
  const today = new Date();
  const date = `${today.getFullYear()}${String(today.getMonth() + 1).padStart(2, '0')}${String(today.getDate()).padStart(2, '0')}`;

  return [
    seg('ISA', '00', '          ', '00', '          ', 'ZZ', clean(first['Sender ID'], 'SENDERID').padEnd(15, ' '), 'ZZ', clean(first['Receiver ID'], 'RECEIVERID').padEnd(15, ' '), date.slice(2), formatTime(today), '^', '00501', String(controlNumber).padStart(9, '0'), '0', 'P', ':'),
    seg('GS', 'BE', clean(first['Sender ID'], 'SENDERID'), clean(first['Receiver ID'], 'RECEIVERID'), date, formatTime(today), String(controlNumber), 'X', '005010X220A1'),
    seg('ST', '834', String(controlNumber).padStart(4, '0'), '005010X220A1'),
    seg('BGN', '00', clean(first['Transaction Set Purpose Code'], 'REF834'), date, formatTime(today), '', '', '', clean(first['Action Code'], '4')),
    seg('REF', '38', clean(first['Policy Number'], 'POLICY001')),
    seg('DTP', '007', 'D8', date),
    seg('N1', 'P5', clean(first['Sponsor Name'], 'DEFAULT SPONSOR'), 'FI', clean(first['Sponsor Tax ID'], '999999999')),
    seg('N1', 'IN', clean(first['Payer Name'], 'DEFAULT PAYER'), 'FI', clean(first['Payer ID'], '888888888'))
  ];
}

function includeProviderLoop(row) {
  return clean(row['Include Provider Loop'], 'N').toUpperCase() === 'Y';
}

function includeProductRef(row) {
  return clean(row['Include Product REF'], 'N').toUpperCase() === 'Y';
}

function buildMemberLoops(row, index) {
  const relationship = clean(row['Relationship Code'], '18');
  const isSubscriber = relationship === '18';
  const segments = [
    seg('INS', isSubscriber ? 'Y' : 'N', relationship, clean(row['Maintenance Type Code'], '21'), '', clean(row['Benefit Status Code'], 'A'), '', '', clean(row['Employment Status'], 'FT'), '', clean(row['Handicap Indicator'], 'N'), '', ''),
    seg('REF', '0F', clean(row['Subscriber Number'], clean(row['Member ID'], `MID${index}`))),
    seg('REF', '1L', clean(row['Group'], 'DEFAULT_GROUP')),
    seg('REF', '17', clean(row['Sub Group ID'], '1001')),
    seg('REF', 'QQ', clean(row['Class Plan ID'], '1004')),
    seg('DTP', '356', 'D8', formatDate(row['Eligibility Begin Date'], '01012024')),
    seg('NM1', 'IL', '1', clean(row['Last Name'], 'DOE'), clean(row['First Name'], 'JOHN'), clean(row['Middle Name'], ''), clean(row['Name Suffix'], ''), '', '34', clean(row['Member ID'], `MID${index}`)),
    seg('PER', 'IP', clean(row['Contact Name'], `${clean(row['First Name'], 'JOHN')} ${clean(row['Last Name'], 'DOE')}`), 'TE', clean(row['Phone'], '9999999999'), 'EM', clean(row['Email'], 'noemail@example.com')),
    seg('N3', clean(row['Address 1'], '123 DEFAULT ST'), clean(row['Address 2'], '')),
    seg('N4', clean(row['City'], 'DEFAULTCITY'), clean(row['State'], 'TX'), clean(row['Zip'], '75001')),
    seg('DMG', 'D8', formatDate(row['Date of Birth'], '01011980'), clean(row['Gender'], 'U')),
    seg('DTP', '348', 'D8', formatDate(row['Eligibility Date'], formatDate(row['Eligibility Begin Date'], '01012024'))),
    seg('HD', clean(row['Maintenance Type Code'], '21'), clean(row['Maintenance Reason Code'], 'XN'), clean(row['Insurance Line Code'], 'HLT'), clean(row['Plan'], 'DEFAULTPLAN'), clean(row['Coverage Level Code'], 'EMP'))
  ];

  if (includeProductRef(row)) {
    segments.push(seg('REF', '1L', clean(row['Product'], 'DEFAULTPRODUCT')));
  }

  if (includeProviderLoop(row)) {
    segments.push(
      seg('LX', String(index)),
      seg('NM1', 'P3', '2', clean(row['Provider Name'], 'DEFAULT PROVIDER'), '', '', '', '', 'XX', clean(row['Provider NPI'], '1999999999')),
      seg('N3', clean(row['Provider Address 1'], '1 PROVIDER WAY'), clean(row['Provider Address 2'], '')),
      seg('N4', clean(row['Provider City'], 'AUSTIN'), clean(row['Provider State'], 'TX'), clean(row['Provider Zip'], '73301'))
    );
  }

  return segments;
}

function buildTrailer(segmentCount, controlNumber) {
  return [
    seg('SE', String(segmentCount + 1), String(controlNumber).padStart(4, '0')),
    seg('GE', '1', String(controlNumber)),
    seg('IEA', '1', String(controlNumber).padStart(9, '0'))
  ];
}

function validateSnipLikeRules(rows) {
  const errors = [];
  rows.forEach((row, idx) => {
    const line = idx + 2;
    if (!clean(row['Member ID'])) errors.push(`Row ${line}: Member ID is required.`);
    if (!clean(row['Last Name'])) errors.push(`Row ${line}: Last Name is required.`);
    if (!clean(row['First Name'])) errors.push(`Row ${line}: First Name is required.`);
    if (!clean(row['Relationship Code'])) errors.push(`Row ${line}: Relationship Code is required.`);

    const gender = clean(row['Gender'], 'U');
    if (!['M', 'F', 'U'].includes(gender)) errors.push(`Row ${line}: Gender must be M/F/U.`);

    if (clean(row['Relationship Code']) !== '18' && !clean(row['Subscriber Number'])) {
      errors.push(`Row ${line}: Dependent rows require Subscriber Number.`);
    }
  });
  return errors;
}

function parseInput(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === '.csv') return parseCsv(fs.readFileSync(filePath, 'utf8'));
  if (ext === '.xlsx') return parseXlsx(filePath);
  throw new Error('Unsupported input format. Use .xlsx or .csv.');
}

function generate834FromRows(rows, outputPath) {
  const snipErrors = validateSnipLikeRules(rows);
  if (snipErrors.length) throw new Error(`SNIP-like validation failed:\n${snipErrors.join('\n')}`);

  const controlNumber = Math.floor(Math.random() * 900000) + 100000;
  const segments = [];
  segments.push(...buildHeader(rows[0], controlNumber));
  rows.forEach((row, idx) => segments.push(...buildMemberLoops(row, idx + 1)));
  segments.push(...buildTrailer(segments.length, controlNumber));

  const content = segments.join('\n') + '\n';
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, content, 'utf8');

  return { outputPath, segmentCount: segments.length, memberCount: rows.length, controlNumber };
}

function generate834FromExcel(excelPath, outputPath) {
  const rows = parseInput(excelPath);
  validateInputRows(rows);
  return generate834FromRows(rows, outputPath);
}

module.exports = { parseInput, generate834FromRows, generate834FromExcel, validateSnipLikeRules, formatDate };
