"""
routers/github_api.py
---------------------
POST /api/github — fetch a Python file from GitHub by URL, save it, then run
the full scan pipeline and return ScanResult.
"""

import uuid
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.config import get_settings
from backend.models.schemas import GitHubFetchRequest, ScanResult, ScanSummary, Severity
from backend.services.github_service import fetch_github_file
from backend.services.semgrep_service import run_semgrep
from backend.services.ai_service import explain_and_fix

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/github", response_model=ScanResult)
async def scan_github_file(request: GitHubFetchRequest):
    """
    Fetch a Python file from GitHub and run a full security scan.

    Accepts GitHub blob URLs:
      https://github.com/owner/repo/blob/branch/path/to/file.py

    Returns the same `ScanResult` as `POST /api/scan`.
    """
    # ── Fetch from GitHub ─────────────────────────────────────────────────────
    try:
        content, filename = fetch_github_file(request.repo_url)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected GitHub fetch error: %s", exc)
        raise HTTPException(status_code=500, detail=f"GitHub fetch error: {exc}")

    # ── Save locally ──────────────────────────────────────────────────────────
    file_id = str(uuid.uuid4())
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
    file_path = Path(settings.uploads_dir) / f"{file_id}.py"
    file_path.write_text(content, encoding="utf-8")

    scan_id = str(uuid.uuid4())
    logger.info("GitHub scan [%s] on %s (%d chars)", scan_id, filename, len(content))

    # ── Semgrep ───────────────────────────────────────────────────────────────
    try:
        findings = run_semgrep(str(file_path))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Semgrep error: {exc}")

    # ── AI enrichment ─────────────────────────────────────────────────────────
    ai_model = request.ai_model.value if request.ai_model else settings.ai_model
    for finding in findings:
        try:
            explanation, fix, refs = await explain_and_fix(
                rule_id=finding.rule_id,
                severity=finding.severity.value,
                message=finding.message,
                code_snippet=finding.code_snippet,
                cwe=finding.cwe or "N/A",
                ai_model=ai_model,
            )
            finding.ai_explanation = explanation
            finding.ai_fix         = fix
            finding.references     = refs
        except Exception as exc:
            logger.warning("AI enrichment skipped for %s: %s", finding.rule_id, exc)
            finding.ai_explanation = f"AI unavailable: {exc}"

    summary = ScanSummary(
        total=len(findings),
        errors=sum(1 for f in findings if f.severity == Severity.ERROR),
        warnings=sum(1 for f in findings if f.severity == Severity.WARNING),
        info=sum(1 for f in findings if f.severity == Severity.INFO),
    )

    return ScanResult(
        scan_id=scan_id,
        filename=filename,
        status="completed",
        summary=summary,
        findings=findings,
        scanned_at=datetime.utcnow().isoformat() + "Z",
    )
