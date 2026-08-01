"""
routers/report.py
-----------------
GET  /api/report/{scan_id}?format=html  — return HTML report file
GET  /api/report/{scan_id}?format=pdf   — return PDF report file
POST /api/report                        — generate report from ScanResult JSON body
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from backend.config import get_settings
from backend.models.schemas import ScanResult, ReportResponse
from backend.services.report_service import generate_html_report, generate_pdf_report

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/report", response_model=ReportResponse)
async def create_report(
    scan_result: ScanResult,
    format: str = Query(default="html", pattern="^(html|pdf)$"),
):
    """
    Generate a security report from a ScanResult.

    Pass the full ScanResult JSON (returned by `/api/scan` or `/api/github`)
    in the request body. Returns the report download URL.
    """
    try:
        if format == "pdf":
            report_path = generate_pdf_report(scan_result)
        else:
            report_path = generate_html_report(scan_result)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.error("Report generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Report generation error: {exc}")

    report_filename = Path(report_path).name
    report_url = f"/reports/{report_filename}"

    return ReportResponse(
        scan_id=scan_result.scan_id,
        report_url=report_url,
        format=format,
    )


@router.get("/report/{scan_id}")
async def download_report(
    scan_id: str,
    format: str = Query(default="html", pattern="^(html|pdf)$"),
):
    """
    Download a previously generated report by scan_id.

    Requires that the report was already created via `POST /api/report`.
    """
    ext = "pdf" if format == "pdf" else "html"
    report_path = Path(settings.reports_dir) / f"{scan_id}.{ext}"

    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Report not found for scan_id '{scan_id}'. "
                   "Generate it first via POST /api/report.",
        )

    media_type = "application/pdf" if format == "pdf" else "text/html"
    return FileResponse(
        path=str(report_path),
        media_type=media_type,
        filename=f"security_report_{scan_id}.{ext}",
    )
