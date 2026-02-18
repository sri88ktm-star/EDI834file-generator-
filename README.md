# EDI 834 File Creator (Node.js + Playwright Workflow)

This project provides a backend Node.js tool and simple browser UI for generating EDI 834 enrollment files from Excel-compatible input files.

## What it does

- Generates an EDI 834 transaction envelope (`ISA/GS/ST ... SE/GE/IEA`).
- Builds required loops and segment families requested:
  - Header Loop `1000A` and `1000B`
  - Loop `2000` member-level detail
  - Loop `2100A/B/C` member name/address/contact/demographic
  - Loop `2300` health coverage
  - Loop `2310` provider information
- Supports subscriber and dependent records.
- Uses default values when situational fields are missing.
- Adds `REF*17` (Sub Group ID) and `REF*QQ` (Class Plan ID) in member loop.
- Omits situational product/provider loops unless explicitly enabled in input (`Include Product REF=Y`, `Include Provider Loop=Y`).
- Runs SNIP-like structural checks before generating output.

## Input format

Primary supported input: `.xlsx` (first worksheet)
Also supported: `.csv` (Excel-export friendly)

Minimum required columns:

- `Sender ID`
- `Receiver ID`
- `Group`
- `Plan`
- `Product`
- `Member ID`
- `Relationship Code`
- `Last Name`
- `First Name`

Recommended additional columns:

- `Sub Group ID` (emits `REF*17`)
- `Class Plan ID` (emits `REF*QQ`)
- `Include Product REF` (`Y` to emit `REF*1L*<Product>` in coverage loop)
- `Include Provider Loop` (`Y` to emit Loop 2310 provider segments)

Sample input file is included at `samples/enrollment_input.csv`.

## Run

```bash
npm start
```

Open:

```text
http://localhost:3000
```

## Generate via API

```bash
curl -X POST http://localhost:3000/api/generate-from-path \
  -H "Content-Type: application/json" \
  -d '{
    "excelPath":"/workspace/EDI--File-Creator-CODEX/samples/enrollment_input.csv",
    "outputPath":"/workspace/EDI--File-Creator-CODEX/generated/enrollment.edi"
  }'
```


### Output path behavior

- If `outputPath` is a directory (for example `D:\TEST\output`), the service auto-creates a file inside that directory named like `enrollment_<timestamp>.edi`.
- If `outputPath` has no extension, `.edi` is appended automatically.
- If `outputPath` is omitted, output is written to `generated/enrollment_<timestamp>.edi`.

## Validation and compliance note

The generator enforces practical SNIP-like checks (required IDs, member naming, relationship-linking for dependents, value-domain checks) and creates consistent 834 structures with defaults. Full payer-specific companion guide certification still requires payer-specific rule tuning and external validation/testing.

## Test

```bash
npm test
```
