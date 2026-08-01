/* ═══════════════════════════════════════════════════════════════════
   app.js — AI Secure Code Reviewer frontend logic
   ═══════════════════════════════════════════════════════════════════ */

const API = '';          // same-origin; change to e.g. 'http://localhost:8000' if serving separately
let currentScanResult = null;
let currentMode = 'upload';       // 'upload' | 'github'
let uploadedFileId  = null;

/* ── Tab switching ──────────────────────────────────────────────── */
function switchTab(mode) {
  currentMode = mode;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.getElementById(`tab-${mode}`).classList.add('active');
  document.getElementById(`panel-${mode}`).classList.add('active');
}

/* ── Drag-and-drop handlers ─────────────────────────────────────── */
function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('dropZone').classList.add('drag-over');
}
function handleDragLeave(e) {
  document.getElementById('dropZone').classList.remove('drag-over');
}
function handleDrop(e) {
  e.preventDefault();
  document.getElementById('dropZone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) processFile(file);
}
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) processFile(file);
}

function processFile(file) {
  if (!file.name.endsWith('.py')) {
    showToast('Only Python (.py) files are supported.');
    return;
  }
  const hint = document.getElementById('dropHint');
  hint.textContent = `✅ ${file.name} (${(file.size/1024).toFixed(1)} KB)`;
  hint.className = 'drop-hint success';
  document.querySelector('.drop-title').textContent = 'File ready to scan';
  // Store reference for upload
  document.getElementById('fileInput')._selectedFile = file;
}

/* ── Main scan entry point ──────────────────────────────────────── */
async function startScan() {
  if (currentMode === 'upload') {
    await scanUploadedFile();
  } else {
    await scanGitHubUrl();
  }
}

async function scanUploadedFile() {
  const fileInput = document.getElementById('fileInput');
  const file = fileInput._selectedFile || fileInput.files[0];
  if (!file) {
    showToast('Please select a .py file first.');
    return;
  }

  setScanningState(true);
  setProgress(10, 'Uploading file…', 1);

  // Step 1: Upload
  const formData = new FormData();
  formData.append('file', file);
  let uploadRes;
  try {
    const res = await fetch(`${API}/api/upload`, { method: 'POST', body: formData });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }
    uploadRes = await res.json();
    uploadedFileId = uploadRes.file_id;
  } catch (err) {
    setScanningState(false);
    showToast(`Upload error: ${err.message}`);
    return;
  }

  setProgress(35, 'Running Semgrep static analysis…', 2);
  await runScan({ file_id: uploadedFileId, ai_model: getSelectedModel(), include_fix: true }, file.name);
}

async function scanGitHubUrl() {
  const url = document.getElementById('githubUrl').value.trim();
  if (!url) {
    showToast('Please enter a GitHub URL.');
    return;
  }

  setScanningState(true);
  setProgress(20, 'Fetching file from GitHub…', 1);
  setProgress(40, 'Running Semgrep + AI analysis…', 2);

  try {
    const res = await fetch(`${API}/api/github`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: url, ai_model: getSelectedModel() }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'GitHub scan failed');
    }
    const scanResult = await res.json();
    setProgress(90, 'Building results…', 3);
    await delay(500);
    showResults(scanResult, url.split('/').pop());
  } catch (err) {
    setScanningState(false);
    showToast(`GitHub scan error: ${err.message}`);
  }
}

async function runScan(payload, filename) {
  try {
    setProgress(55, 'AI is analysing vulnerabilities…', 3);
    const res = await fetch(`${API}/api/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Scan failed');
    }
    const scanResult = await res.json();
    setProgress(90, 'Finalising results…', 4);
    await delay(400);
    showResults(scanResult, filename);
  } catch (err) {
    setScanningState(false);
    showToast(`Scan error: ${err.message}`);
  }
}

/* ── Download report ────────────────────────────────────────────── */
async function downloadReport(format) {
  if (!currentScanResult) return;
  try {
    const res = await fetch(`${API}/api/report?format=${format}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(currentScanResult),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Report generation failed');
    }
    const { report_url } = await res.json();
    window.open(report_url, '_blank');
  } catch (err) {
    showToast(`Report error: ${err.message}`);
  }
}

/* ── Render results ─────────────────────────────────────────────── */
function showResults(scanResult, filename) {
  currentScanResult = scanResult;

  // Hide progress, show results
  document.getElementById('progressSection').style.display = 'none';
  const resultsSection = document.getElementById('results');
  resultsSection.style.display = 'block';
  resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

  document.getElementById('resultFilename').textContent = filename || scanResult.filename;
  document.getElementById('scanBtn').disabled = false;

  // Summary cards
  const s = scanResult.summary;
  const colors = { total: '#00d4ff', errors: '#ff4d6d', warnings: '#ffb703', info: '#4cc9f0' };
  document.getElementById('summaryGrid').innerHTML = `
    ${summaryCard(s.total,    'Total Issues',    colors.total)}
    ${summaryCard(s.errors,   'Critical',        colors.errors)}
    ${summaryCard(s.warnings, 'Warnings',        colors.warnings)}
    ${summaryCard(s.info,     'Informational',   colors.info)}
  `;

  // Findings
  const list = document.getElementById('findingsList');
  if (!scanResult.findings || scanResult.findings.length === 0) {
    list.innerHTML = `
      <div class="no-findings">
        <div class="no-findings-icon">✅</div>
        <h3>No vulnerabilities detected</h3>
        <p style="margin-top:8px;color:#64748b;">
          Semgrep found no issues with the configured ruleset.
        </p>
      </div>`;
    return;
  }

  list.innerHTML = scanResult.findings.map((f, i) => findingCard(f, i)).join('');
}

function summaryCard(count, label, color) {
  return `
    <div class="sum-card">
      <div class="sum-count" style="color:${color}">${count}</div>
      <div class="sum-label">${label}</div>
    </div>`;
}

function findingCard(f, i) {
  const id = `finding-${i}`;
  const refs = (f.references || []).map(r =>
    `<a class="ref-tag" href="${esc(r)}" target="_blank" rel="noopener" title="${esc(r)}">${esc(r)}</a>`
  ).join('');

  return `
  <div class="finding-card">
    <div class="finding-hdr" onclick="toggleFinding('${id}')">
      <span class="finding-rule">${esc(f.rule_id)}</span>
      <div class="finding-hdr-right">
        <span class="sev-badge sev-${f.severity}">${f.severity}</span>
        <span class="expand-icon" id="${id}-icon">▼</span>
      </div>
    </div>
    <div class="finding-body" id="${id}">

      <div class="meta-chips">
        ${f.cwe   ? `<span class="meta-chip">🔖 ${esc(f.cwe)}</span>` : ''}
        ${f.owasp ? `<span class="meta-chip">⚠️ ${esc(f.owasp)}</span>` : ''}
        <span class="meta-chip">📄 ${esc(f.file)}</span>
        <span class="meta-chip">📍 Lines ${f.line_start}–${f.line_end}</span>
      </div>

      <div class="finding-msg">${esc(f.message)}</div>

      ${f.code_snippet ? `
        <div class="sub-label">🚨 Vulnerable Code</div>
        <pre class="code-block">${esc(f.code_snippet)}</pre>
      ` : ''}

      ${f.ai_explanation ? `
        <div class="sub-label">🤖 AI Explanation</div>
        <div class="ai-box">${esc(f.ai_explanation)}</div>
      ` : ''}

      ${f.ai_fix ? `
        <div class="sub-label">✅ Secure Fix</div>
        <pre class="code-block fix-block">${esc(f.ai_fix)}</pre>
      ` : ''}

      ${refs ? `
        <div class="sub-label">📚 References</div>
        <div class="refs">${refs}</div>
      ` : ''}

    </div>
  </div>`;
}

function toggleFinding(id) {
  const body = document.getElementById(id);
  const icon = document.getElementById(`${id}-icon`);
  body.classList.toggle('open');
  icon.classList.toggle('open');
}

/* ── Progress helpers ───────────────────────────────────────────── */
function setProgress(pct, msg, step) {
  document.getElementById('progressBar').style.width = pct + '%';
  document.getElementById('progressMsg').textContent = msg;
  // Update steps
  for (let i = 1; i <= 4; i++) {
    const el = document.getElementById(`pstep-${i}`);
    el.className = 'pstep' + (i < step ? ' done' : i === step ? ' active' : '');
  }
}

function setScanningState(scanning) {
  const btn = document.getElementById('scanBtn');
  btn.disabled = scanning;
  document.getElementById('progressSection').style.display = scanning ? 'block' : 'none';
  document.getElementById('results').style.display = 'none';
  if (scanning) {
    document.getElementById('progressSection').scrollIntoView({ behavior: 'smooth' });
    document.getElementById('progressBar').style.width = '0%';
  }
}

/* ── Utilities ──────────────────────────────────────────────────── */
function getSelectedModel() {
  return document.getElementById('modelSelect').value;
}

function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

function showToast(msg) {
  document.getElementById('toastMsg').textContent = msg;
  const t = document.getElementById('errorToast');
  t.style.display = 'flex';
  setTimeout(() => { t.style.display = 'none'; }, 6000);
}
function closeToast() {
  document.getElementById('errorToast').style.display = 'none';
}

function resetUI() {
  currentScanResult = null;
  uploadedFileId = null;
  document.getElementById('results').style.display = 'none';
  document.getElementById('progressSection').style.display = 'none';
  document.getElementById('fileInput').value = '';
  document.getElementById('fileInput')._selectedFile = null;
  document.getElementById('dropHint').textContent = 'Max 10 MB · Python files only';
  document.getElementById('dropHint').className = 'drop-hint';
  document.querySelector('.drop-title').textContent = 'Drag & drop your .py file here';
  document.getElementById('githubUrl').value = '';
  document.getElementById('scanBtn').disabled = false;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
