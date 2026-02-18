#!/usr/bin/env python3
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = {
    'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'rel': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
}


def col_to_index(cell_ref: str) -> int:
    match = re.match(r'([A-Z]+)', cell_ref)
    if not match:
        return 0
    col = match.group(1)
    idx = 0
    for ch in col:
        idx = idx * 26 + (ord(ch) - ord('A') + 1)
    return idx - 1


def load_shared_strings(zf):
    if 'xl/sharedStrings.xml' not in zf.namelist():
        return []
    root = ET.fromstring(zf.read('xl/sharedStrings.xml'))
    out = []
    for si in root.findall('main:si', NS):
        text_parts = []
        t = si.find('main:t', NS)
        if t is not None and t.text:
            text_parts.append(t.text)
        for run in si.findall('main:r', NS):
            rt = run.find('main:t', NS)
            if rt is not None and rt.text:
                text_parts.append(rt.text)
        out.append(''.join(text_parts))
    return out


def first_sheet_path(zf):
    wb = ET.fromstring(zf.read('xl/workbook.xml'))
    first_sheet = wb.find('main:sheets/main:sheet', NS)
    rel_id = first_sheet.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')

    rels = ET.fromstring(zf.read('xl/_rels/workbook.xml.rels'))
    for rel in rels:
        if rel.attrib.get('Id') == rel_id:
            target = rel.attrib.get('Target')
            return 'xl/' + target.replace('\\', '/')
    return 'xl/worksheets/sheet1.xml'


def cell_value(cell, shared_strings):
    cell_type = cell.attrib.get('t')
    value_el = cell.find('main:v', NS)
    if value_el is None:
        inline = cell.find('main:is/main:t', NS)
        return inline.text if inline is not None and inline.text else ''
    raw = value_el.text or ''
    if cell_type == 's':
        try:
            return shared_strings[int(raw)]
        except Exception:
            return ''
    return raw


def parse_xlsx(path):
    with zipfile.ZipFile(path, 'r') as zf:
        shared = load_shared_strings(zf)
        sheet = ET.fromstring(zf.read(first_sheet_path(zf)))

        rows = []
        for row in sheet.findall('.//main:sheetData/main:row', NS):
            values = {}
            max_idx = 0
            for cell in row.findall('main:c', NS):
                ref = cell.attrib.get('r', 'A1')
                idx = col_to_index(ref)
                values[idx] = cell_value(cell, shared)
                max_idx = max(max_idx, idx)
            out_row = [values.get(i, '') for i in range(max_idx + 1)]
            rows.append(out_row)

        if not rows:
            return []

        headers = [str(h).strip() for h in rows[0]]
        data = []
        for row in rows[1:]:
            if not any(str(v).strip() for v in row):
                continue
            obj = {}
            for i, header in enumerate(headers):
                if not header:
                    continue
                obj[header] = row[i] if i < len(row) else ''
            data.append(obj)

        return data


if __name__ == '__main__':
    result = parse_xlsx(sys.argv[1])
    print(json.dumps(result))
