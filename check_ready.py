"""
Project readiness check — ASCII only (Windows cp1252 safe).
"""

import os, sys, json, time, urllib.request, urllib.error
from pathlib import Path
from urllib.request import Request

BASE = "http://localhost:8000"
ROOT = Path(__file__).parent

OK   = "[PASS]"
ERR  = "[FAIL]"
WARN = "[WARN]"

results = []

def check(label, ok, detail=""):
    tag = OK if ok else ERR
    line = f"  {tag} {label}"
    if detail:
        line += f"  ->  {detail}"
    print(line)
    results.append((label, ok))

def http_get(url, timeout=5):
    try:
        r = urllib.request.urlopen(url, timeout=timeout)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception as e:
        return None, str(e)

print()
print("=" * 60)
print("  AI Secure Code Reviewer -- Project Readiness Check")
print("=" * 60)

# ── 1. File Structure ──────────────────────────────────────────────
print("\n[1] File Structure")
required = [
    "backend/main.py",
    "backend/config.py",
    "backend/models/schemas.py",
    "backend/services/semgrep_service.py",
    "backend/services/ai_service.py",
    "backend/services/github_service.py",
    "backend/services/report_service.py",
    "backend/routers/upload.py",
    "backend/routers/scan.py",
    "backend/routers/github_api.py",
    "backend/routers/report.py",
    "backend/templates/report.html",
    "frontend/index.html",
    "frontend/style.css",
    "frontend/app.js",
    "semgrep_rules/custom_rules.yaml",
    "backend/requirements.txt",
    ".env.example",
    "start_backend.bat",
    "start_frontend.bat",
    "start_all.bat",
]
for f in required:
    check(f, (ROOT / f).exists())

# ── 2. Environment ─────────────────────────────────────────────────
print("\n[2] Environment")
check("venv/Scripts/python.exe",  (ROOT / "venv/Scripts/python.exe").exists())
check("venv/Scripts/semgrep.exe", (ROOT / "venv/Scripts/semgrep.exe").exists())
check(".env file exists",         (ROOT / ".env").exists())

has_key = False
if (ROOT / ".env").exists():
    env_text = (ROOT / ".env").read_text(encoding="utf-8")
    has_key  = "OPENAI_API_KEY=sk-" in env_text and "your-openai" not in env_text
    check(".env has real OPENAI_API_KEY", has_key,
          "Add real key for AI features" if not has_key else "")

# ── 3. Python imports ──────────────────────────────────────────────
print("\n[3] Python Package Imports")
packages = [
    "fastapi", "uvicorn", "langchain", "langchain_openai",
    "langchain_community", "openai", "semgrep", "jinja2",
    "pydantic", "requests", "aiofiles",
]
for pkg in packages:
    try:
        __import__(pkg)
        check(f"import {pkg}", True)
    except ImportError:
        check(f"import {pkg}", False, f"pip install {pkg}")

# ── 4. Server endpoints ────────────────────────────────────────────
print("\n[4] Server Endpoints")
time.sleep(2)

status, body = http_get(f"{BASE}/health")
check("GET /health -> 200", status == 200,
      f"status={body.get('status')}, version={body.get('version')}" if body else str(body))

status, _ = http_get(f"{BASE}/")
check("GET / (frontend HTML) -> 200", status == 200)

status, _ = http_get(f"{BASE}/docs")
check("GET /docs (Swagger UI) -> 200", status == 200)

# ── 5. Upload endpoint ─────────────────────────────────────────────
print("\n[5] Upload API")
boundary   = "TestBoundary9876543210"
code_bytes = b"import os\nresult = os.system('ls ' + user_input)\npassword = 'secret123'\n"
body_bytes = (
    f"--{boundary}\r\nContent-Disposition: form-data; "
    f'name="file"; filename="check.py"\r\nContent-Type: text/x-python\r\n\r\n'
).encode() + code_bytes + f"\r\n--{boundary}--\r\n".encode()

file_id = None
scan_result = None
try:
    req = Request(
        f"{BASE}/api/upload", data=body_bytes,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    r = urllib.request.urlopen(req, timeout=10)
    upload = json.loads(r.read())
    file_id = upload.get("file_id", "")
    check("POST /api/upload -> 200", r.status == 200,
          f"file_id={file_id[:8]}...")
except Exception as e:
    check("POST /api/upload -> 200", False, str(e)[:80])

# ── 6. Scan endpoint (Semgrep, no AI) ─────────────────────────────
print("\n[6] Scan API  (Semgrep only -- no OpenAI key needed)")
if file_id:
    try:
        payload = json.dumps({"file_id": file_id, "include_fix": False}).encode()
        req2 = Request(
            f"{BASE}/api/scan", data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        r2 = urllib.request.urlopen(req2, timeout=90)
        scan_result = json.loads(r2.read())
        summary  = scan_result.get("summary", {})
        findings = scan_result.get("findings", [])
        check("POST /api/scan -> 200", r2.status == 200,
              f"total={summary.get('total',0)}, errors={summary.get('errors',0)}, "
              f"warnings={summary.get('warnings',0)}")
        check("Semgrep found vulnerabilities", len(findings) > 0,
              f"{len(findings)} finding(s) detected")
        for f in findings[:5]:
            cwe = f.get("cwe") or "N/A"
            print(f"       [{f['severity']}] {f['rule_id']}  L{f['line_start']}  {cwe}")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:120]
        check("POST /api/scan -> 200", False, f"HTTP {e.code}: {detail}")
    except Exception as e:
        check("POST /api/scan -> 200", False, str(e)[:100])
else:
    check("POST /api/scan -> 200", False, "Skipped -- upload failed")

# ── 7. Report generation ───────────────────────────────────────────
print("\n[7] Report Generation")
if scan_result:
    try:
        payload3 = json.dumps(scan_result).encode()
        req3 = Request(
            f"{BASE}/api/report?format=html", data=payload3,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        r3 = urllib.request.urlopen(req3, timeout=15)
        rep = json.loads(r3.read())
        check("POST /api/report -> 200", r3.status == 200,
              f"url={rep.get('report_url')}")
    except Exception as e:
        check("POST /api/report -> 200", False, str(e)[:100])
else:
    check("POST /api/report -> 200", False, "Skipped -- scan failed")

# ── Summary ────────────────────────────────────────────────────────
total  = len(results)
passed = sum(1 for _, ok in results if ok)
failed = total - passed

print()
print("=" * 60)
if failed == 0:
    print(f"  ALL {total} CHECKS PASSED -- Project is READY!")
elif failed == 1 and not has_key:
    print(f"  {passed}/{total} checks passed.")
    print("  Core scanning pipeline is READY.")
    print("  Only missing: real OPENAI_API_KEY in .env (needed for AI explain/fix).")
else:
    print(f"  {failed}/{total} checks FAILED -- see details above.")
print("=" * 60)
print()
