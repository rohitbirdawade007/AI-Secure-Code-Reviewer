from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class AIModel(str, Enum):
    GPT4O = "gpt-4o"
    GPT35 = "gpt-3.5-turbo"
    LLAMA3 = "ollama/llama3"


# ── Request schemas ──────────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    file_id: str
    ai_model: Optional[AIModel] = AIModel.GPT4O
    include_fix: bool = True


class GitHubFetchRequest(BaseModel):
    repo_url: str = Field(
        ...,
        example="https://github.com/owner/repo/blob/main/path/to/file.py"
    )
    ai_model: Optional[AIModel] = AIModel.GPT4O


# ── Response schemas ─────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    file_id: str
    filename: str
    size_bytes: int
    message: str


class VulnerabilityFinding(BaseModel):
    rule_id: str
    severity: Severity
    message: str
    cwe: Optional[str] = None
    owasp: Optional[str] = None
    file: str
    line_start: int
    line_end: int
    code_snippet: str
    # AI-generated fields
    ai_explanation: Optional[str] = None
    ai_fix: Optional[str] = None
    references: Optional[List[str]] = []


class ScanSummary(BaseModel):
    total: int
    errors: int
    warnings: int
    info: int


class ScanResult(BaseModel):
    scan_id: str
    filename: str
    status: str                       # "completed" | "error"
    summary: ScanSummary
    findings: List[VulnerabilityFinding]
    scanned_at: str


class ReportResponse(BaseModel):
    scan_id: str
    report_url: str
    format: str                       # "html" | "pdf"
