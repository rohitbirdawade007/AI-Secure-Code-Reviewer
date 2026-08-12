import subprocess, json, sys
from pathlib import Path

semgrep = str(Path(sys.executable).parent / "semgrep.exe")

# Test 1: Custom local rules
print("--- Test: Custom Rules (offline) ---")
r = subprocess.run(
    [semgrep, "--config", "semgrep_rules/custom_rules.yaml",
     "--json", "--no-git-ignore", "--disable-version-check", "test_vulnerable.py"],
    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120
)
try:
    data = json.loads(r.stdout)
    findings = data.get("results", [])
    print(f"Findings: {len(findings)}")
    for f in findings:
        print(f"  [{f['extra']['severity']}] {f['check_id']}  L{f['start']['line']}")
except Exception as e:
    print("Parse error:", e)
    print("STDOUT:", r.stdout[:300])
    print("STDERR:", r.stderr[:300])

# Test 2: Auto rules (needs internet first time)
print("\n--- Test: Auto Rules (needs internet) ---")
r2 = subprocess.run(
    [semgrep, "--config", "auto", "--json", "--no-git-ignore", "test_vulnerable.py"],
    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90
)
try:
    data2 = json.loads(r2.stdout)
    findings2 = data2.get("results", [])
    print(f"Findings: {len(findings2)}")
    for f in findings2[:5]:
        print(f"  [{f['extra']['severity']}] {f['check_id']}  L{f['start']['line']}")
except Exception as e:
    print("Parse error:", e)
    print("STDOUT:", r2.stdout[:300])
    print("STDERR:", r2.stderr[:300])
