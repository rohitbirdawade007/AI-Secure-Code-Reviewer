# 🔐 AI Secure Code Reviewer

An AI-powered static code analysis tool that combines **Semgrep** with **LangChain + OpenAI/Llama** to detect vulnerabilities in Python code, explain them in plain English, suggest secure fixes, and generate a downloadable security report.

> Built with Qualcomm-aligned security engineering practices in mind.

---

## ✨ Features

- 📁 **Upload Python code** — drag-and-drop file or paste code directly
- 🔗 **GitHub Integration** — fetch code from any public GitHub repository URL
- 🔍 **Semgrep Static Analysis** — detects CWE/CVE patterns, OWASP Top 10 issues
- 🤖 **AI-Powered Explanations** — LangChain + GPT-4o explains each vulnerability in plain English
- 🛠️ **Secure Fix Suggestions** — AI proposes corrected, hardened code snippets
- 📄 **Security Report Generation** — export findings as HTML or PDF report

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI |
| AI Engine | LangChain, OpenAI GPT-4o / Ollama Llama3 |
| Scanner | Semgrep |
| GitHub | PyGitHub / GitHub REST API |
| Report | Jinja2, WeasyPrint |
| Frontend | HTML, CSS (Dark Cyberpunk UI), Vanilla JS |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [Semgrep](https://semgrep.dev/docs/getting-started/) installed (`pip install semgrep`)
- OpenAI API key **or** [Ollama](https://ollama.com/) running locally

### Installation

```bash
# Clone the repository
git clone https://github.com/rohitbirdawade007/AI-Secure-Code-Reviewer.git
cd AI-Secure-Code-Reviewer

# Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and GITHUB_TOKEN
```

### Run the App

```bash
uvicorn backend.main:app --reload --port 8000
```

Open your browser at: **http://localhost:8000**

---

## 📁 Project Structure

```
AI-Secure-Code-Reviewer/
├── backend/
│   ├── main.py               # FastAPI app entry point
│   ├── config.py             # Settings & env vars
│   ├── routers/              # API route handlers
│   │   ├── upload.py         # File upload endpoint
│   │   ├── scan.py           # Scan orchestration endpoint
│   │   ├── github_api.py     # GitHub fetch endpoint
│   │   └── report.py         # Report generation endpoint
│   ├── services/             # Core business logic
│   │   ├── semgrep_service.py
│   │   ├── ai_service.py
│   │   ├── github_service.py
│   │   └── report_service.py
│   ├── models/
│   │   └── schemas.py        # Pydantic data models
│   └── requirements.txt
├── frontend/
│   ├── index.html            # Main SPA
│   ├── style.css             # Premium dark UI
│   └── app.js                # UI logic & API calls
├── semgrep_rules/
│   └── custom_rules.yaml     # Custom detection rules
├── reports/                  # Generated reports
├── uploads/                  # Temp uploaded files
├── .env.example
└── README.md
```

---

## 🛡️ Security Checks Covered

- SQL Injection (CWE-89)
- Command Injection (CWE-78)
- Path Traversal (CWE-22)
- Hardcoded Secrets / Credentials (CWE-798)
- Insecure Deserialization (CWE-502)
- XSS / Template Injection (CWE-79)
- Weak Cryptography (CWE-327)
- Insecure Random (CWE-338)
- And more via Semgrep's auto ruleset

---

## 📸 Screenshots

> _Coming soon — UI under active development_

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙋 Author

**Rohit Birdawade**  
GitHub: [@rohitbirdawade007](https://github.com/rohitbirdawade007)
