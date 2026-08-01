"""
report_service.py
-----------------
Generates a styled HTML security report from a ScanResult and optionally
exports it as a PDF using WeasyPrint.
"""

import os
import logging
from pathlib import Path
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape

from backend.config import get_settings
from backend.models.schemas import ScanResult

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_jinja_env() -> Environment:
    templates_path = Path(settings.templates_dir)
    if not templates_path.exists():
        # Fallback: look relative to this file
        templates_path = Path(__file__).parent.parent / "templates"
    return Environment(
        loader=FileSystemLoader(str(templates_path)),
        autoescape=select_autoescape(["html"]),
    )


def generate_html_report(scan_result: ScanResult) -> str:
    """
    Render a Jinja2 HTML report from ScanResult and save to reports/ dir.

    Returns:
        Absolute path to the generated HTML file.
    """
    env = _get_jinja_env()
    template = env.get_template("report.html")

    report_html = template.render(
        scan=scan_result,
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        severity_colors={
            "ERROR": "#ff4d6d",
            "WARNING": "#ffb703",
            "INFO": "#4cc9f0",
        },
    )

    output_path = Path(settings.reports_dir) / f"{scan_result.scan_id}.html"
    os.makedirs(settings.reports_dir, exist_ok=True)
    output_path.write_text(report_html, encoding="utf-8")
    logger.info("HTML report saved: %s", output_path)
    return str(output_path)


def generate_pdf_report(scan_result: ScanResult) -> str:
    """
    Generate a PDF report from the HTML report using WeasyPrint.

    Returns:
        Absolute path to the generated PDF file.

    Raises:
        RuntimeError: If WeasyPrint is not installed.
    """
    try:
        from weasyprint import HTML
    except ImportError:
        raise RuntimeError(
            "WeasyPrint is not installed. Run: pip install weasyprint"
        )

    html_path = generate_html_report(scan_result)
    pdf_path  = html_path.replace(".html", ".pdf")

    HTML(filename=html_path).write_pdf(pdf_path)
    logger.info("PDF report saved: %s", pdf_path)
    return pdf_path
