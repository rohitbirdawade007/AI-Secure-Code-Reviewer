"""
semgrep_service.py
------------------
Runs Semgrep as a subprocess against an uploaded file and parses the JSON
output into structured VulnerabilityFinding objects.
"""

import json
import subprocess
import logging
import sys
from pathlib import Path
from typing import List

from backend.config import get_settings
from backend.models.schemas import VulnerabilityFinding, Severity

logger = logging.getLogger(__name__)
settings = get_settings()


def _extract_cwe(metadata: dict) -> str | None:
    """Pull CWE string from Semgrep rule metadata."""
    cwe = metadata.get("cwe") or metadata.get("cwe2022-top25")
    if isinstance(cwe, list):
        return cwe[0] if cwe else None
    return cwe


def _extract_owasp(metadata: dict) -> str | None:
    """Pull OWASP category from Semgrep rule metadata."""
    owasp = metadata.get("owasp")
    if isinstance(owasp, list):
        return owasp[0] if owasp else None
    return owasp


def _map_severity(raw: str) -> Severity:
    mapping = {
        "ERROR": Severity.ERROR,
        "WARNING": Severity.WARNING,
        "INFO": Severity.INFO,
    }
    return mapping.get(raw.upper(), Severity.INFO)


def run_semgrep(file_path: str) -> List[VulnerabilityFinding]:
    """
    Execute Semgrep on *file_path* and return a list of VulnerabilityFinding.

    Args:
        file_path: Absolute path to the Python source file to scan.

    Returns:
        List of structured findings (empty list if no issues found).

    Raises:
        RuntimeError: If Semgrep is not installed or crashes unexpectedly.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Resolve the semgrep binary from the same venv as the running Python.
    # On Windows the binary has a .exe extension.
    venv_bin = Path(sys.executable).parent
    semgrep_exe = venv_bin / ("semgrep.exe" if sys.platform == "win32" else "semgrep")
    semgrep_path = str(semgrep_exe) if semgrep_exe.exists() else "semgrep"

    cmd = [
        semgrep_path,
        "--config", settings.semgrep_config,
        "--json",
        "--timeout", str(settings.semgrep_timeout),
        "--no-git-ignore",
        "--disable-version-check",   # skip slow network version check on every run
        str(path),
    ]

    logger.info("Running Semgrep: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=settings.semgrep_timeout + 120,  # extra headroom for first-run rule download
        )
    except FileNotFoundError:
        raise RuntimeError(
            "Semgrep is not installed. Install it with: pip install semgrep"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Semgrep scan timed out.")

    # Semgrep exits 1 when findings are detected — that's normal
    if result.returncode not in (0, 1):
        logger.error("Semgrep stderr: %s", result.stderr)
        raise RuntimeError(f"Semgrep failed (exit {result.returncode}): {result.stderr[:500]}")

    if not result.stdout.strip():
        logger.warning("Semgrep returned empty output.")
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse Semgrep JSON output: {exc}")

    findings: List[VulnerabilityFinding] = []
    for match in data.get("results", []):
        meta = match.get("extra", {}).get("metadata", {})
        start = match.get("start", {})
        end   = match.get("end",   {})

        # Extract code snippet
        lines = match.get("extra", {}).get("lines", "")

        finding = VulnerabilityFinding(
            rule_id=match.get("check_id", "unknown"),
            severity=_map_severity(match.get("extra", {}).get("severity", "INFO")),
            message=match.get("extra", {}).get("message", "No message provided."),
            cwe=_extract_cwe(meta),
            owasp=_extract_owasp(meta),
            file=match.get("path", str(path)),
            line_start=start.get("line", 0),
            line_end=end.get("line", 0),
            code_snippet=lines.strip() if lines else "",
        )
        findings.append(finding)

    logger.info("Semgrep found %d finding(s).", len(findings))
    return findings
