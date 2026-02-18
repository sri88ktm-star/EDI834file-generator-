const resultEl = document.getElementById('result');

function showResult(data) {
  resultEl.textContent = JSON.stringify(data, null, 2);
}

document.getElementById('generatePath').addEventListener('click', async () => {
  const excelPath = document.getElementById('excelPath').value;
  const outputPath = document.getElementById('outputPath').value;

  const res = await fetch('/api/generate-from-path', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ excelPath, outputPath })
  });

  showResult(await res.json());
});
