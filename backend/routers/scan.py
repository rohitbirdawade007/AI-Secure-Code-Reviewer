"""
routers/scan.py
---------------
POST /api/scan — orchestrates the full pipeline:
  1. Validate file_id → resolve uploaded file path
  2. Run Semgrep static analysis
  3. For each finding, call AI service to get explanation + fix
  4. Return structured ScanResult JSON
"""

import uuid
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.config import get_settings
from backend.models.schemas import ScanRequest, ScanResult, ScanSummary, Severity
from backend.services.semgrep_service import run_semgrep
from backend.services.ai_service import explain_and_fix

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/scan", response_model=ScanResult)
async def scan_code(request: ScanRequest):
    """
    Run a full security scan on an uploaded file.

    Steps:
    1. Locate the uploaded `.py` file via `file_id`.
    2. Execute Semgrep with the configured ruleset.
    3. Enrich each finding with AI-generated explanation and secure fix.
    4. Return the full `ScanResult`.
    """
    # Resolve file path
    file_path = Path(settings.uploads_dir) / f"{request.file_id}.py"
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No uploaded file found for file_id '{request.file_id}'. "
                   "Please upload a file first via POST /api/upload.",
        )

    filename = file_path.name
    scan_id  = str(uuid.uuid4())

    logger.info("Starting scan [%s] on file: %s", scan_id, file_path)

    # ── Step 1: Semgrep ───────────────────────────────────────────────────────
    try:
        findings = run_semgrep(str(file_path))
    except Exception as exc:
        logger.error("Semgrep failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Semgrep error: {exc}")

    # ── Step 2: AI enrichment ─────────────────────────────────────────────────
    if request.include_fix and findings:
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
                logger.warning("AI enrichment failed for %s: %s", finding.rule_id, exc)
                finding.ai_explanation = f"AI unavailable: {exc}"

    # ── Step 3: Build summary ─────────────────────────────────────────────────
    summary = ScanSummary(
        total=len(findings),
        errors=sum(1 for f in findings if f.severity == Severity.ERROR),
        warnings=sum(1 for f in findings if f.severity == Severity.WARNING),
        info=sum(1 for f in findings if f.severity == Severity.INFO),
    )

    result = ScanResult(
        scan_id=scan_id,
        filename=filename,
        status="completed",
        summary=summary,
        findings=findings,
        scanned_at=datetime.utcnow().isoformat() + "Z",
    )

    logger.info(
        "Scan [%s] complete: %d findings (%d errors, %d warnings, %d info)",
        scan_id, summary.total, summary.errors, summary.warnings, summary.info,
    )
    return result
