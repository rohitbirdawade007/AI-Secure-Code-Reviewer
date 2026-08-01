import requests, json

BASE = 'http://localhost:8000'

# 1. Upload the vulnerable test file
with open('test_vulnerable.py', 'rb') as f:
    r = requests.post(f'{BASE}/api/upload', files={'file': ('test_vulnerable.py', f, 'text/x-python')})

print('=== UPLOAD ===')
print('Status:', r.status_code)
upload = r.json()
print(json.dumps(upload, indent=2))

if r.status_code != 200:
    print('Upload failed, stopping.')
    exit(1)

# 2. Scan (include_fix=False skips OpenAI, so no API key needed)
file_id = upload['file_id']
r2 = requests.post(f'{BASE}/api/scan', json={'file_id': file_id, 'include_fix': False})

print('\n=== SCAN ===')
print('Status:', r2.status_code)
scan = r2.json()
print('Summary:', json.dumps(scan.get('summary'), indent=2))
findings = scan.get('findings', [])
print(f'Total findings: {len(findings)}')
for finding in findings:
    sev  = finding['severity']
    rule = finding['rule_id']
    line = finding['line_start']
    cwe  = finding.get('cwe', 'N/A')
    msg  = finding['message'][:80]
    print(f'  [{sev}] {rule} | L{line} | {cwe}')
    print(f'         {msg}')

print('\n=== ALL CHECKS PASSED ===')
