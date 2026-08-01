"""
ai_service.py
-------------
LangChain-powered AI service that:
  1. Explains a detected vulnerability in plain English.
  2. Suggests a secure, corrected version of the vulnerable code.
  3. Provides relevant references (CWE links, OWASP docs).

Supports both OpenAI (GPT-4o / GPT-3.5) and local Ollama (Llama3).
"""

import logging
import re
from typing import Tuple, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from backend.config import get_settings
from backend.models.schemas import AIModel

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Prompt Templates ──────────────────────────────────────────────────────────

EXPLAIN_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a senior application security engineer. Your role is to explain
code vulnerabilities clearly to developers who may not be security experts.
Be concise, accurate, and constructive. Always explain:
1. What the vulnerability is
2. Why it is dangerous
3. How an attacker could exploit it
Keep your explanation under 150 words.""",
    ),
    (
        "human",
        """Vulnerability detected by Semgrep:
Rule ID: {rule_id}
Severity: {severity}
CWE: {cwe}
Semgrep message: {message}

Vulnerable code snippet:
```python
{code_snippet}
```

Explain this vulnerability in plain English.""",
    ),
])

FIX_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a senior application security engineer. Your role is to provide
secure, drop-in replacement code that fixes the given vulnerability.
Rules:
- Provide ONLY the fixed Python code block, no extra explanation.
- Preserve the original logic and function signatures.
- Add a brief inline comment where the fix was applied.""",
    ),
    (
        "human",
        """Vulnerability:
Rule ID: {rule_id}
CWE: {cwe}
Message: {message}

Original vulnerable code:
```python
{code_snippet}
```

Provide a secure fixed version of this code.""",
    ),
])

REFERENCES_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a security expert. Return only a JSON array of 2-3 relevant URLs "
        "(strings) — CWE pages, OWASP docs, or official Python docs — for the given "
        "vulnerability. No explanation, just the JSON array.",
    ),
    (
        "human",
        "Vulnerability: {rule_id}, CWE: {cwe}, Message: {message}",
    ),
])


# ── LLM factory ───────────────────────────────────────────────────────────────

def _get_llm(model: str):
    """Return the appropriate LangChain LLM based on model string."""
    if model.startswith("ollama/"):
        from langchain_ollama import ChatOllama
        ollama_model = model.split("/", 1)[1]
        return ChatOllama(
            model=ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.2,
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            api_key=settings.openai_api_key,
            temperature=0.2,
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_references(raw: str) -> List[str]:
    """Parse a JSON array of URLs from the LLM output."""
    try:
        import json
        # Find JSON array in response
        match = re.search(r"\[.*?\]", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return []


def _extract_code_block(raw: str) -> str:
    """Strip markdown code fences from AI fix output."""
    match = re.search(r"```(?:python)?\n?(.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw.strip()


# ── Main public function ──────────────────────────────────────────────────────

async def explain_and_fix(
    rule_id: str,
    severity: str,
    message: str,
    code_snippet: str,
    cwe: str = "N/A",
    ai_model: str = "gpt-4o",
) -> Tuple[str, str, List[str]]:
    """
    Ask the LLM to:
      - Explain the vulnerability in plain English.
      - Provide a secure fixed code snippet.
      - Return relevant reference URLs.

    Returns:
        Tuple of (explanation, fixed_code, references)
    """
    llm = _get_llm(ai_model)
    parser = StrOutputParser()

    context = {
        "rule_id": rule_id,
        "severity": severity,
        "message": message,
        "code_snippet": code_snippet or "(no snippet available)",
        "cwe": cwe or "N/A",
    }

    # Build chains
    explain_chain = EXPLAIN_PROMPT | llm | parser
    fix_chain     = FIX_PROMPT     | llm | parser
    ref_chain     = REFERENCES_PROMPT | llm | parser

    try:
        explanation_raw = await explain_chain.ainvoke(context)
        fix_raw         = await fix_chain.ainvoke(context)
        refs_raw        = await ref_chain.ainvoke(context)
    except Exception as exc:
        logger.error("AI service error for rule %s: %s", rule_id, exc)
        return (
            f"AI explanation unavailable: {exc}",
            "(fix not generated)",
            [],
        )

    explanation = explanation_raw.strip()
    fixed_code  = _extract_code_block(fix_raw)
    references  = _extract_references(refs_raw)

    return explanation, fixed_code, references
