# 📝 ReadmeGen

**AI-powered README generator for any codebase** — scan your project, get a polished README in seconds.

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

Stop spending hours writing documentation. ReadmeGen scans your codebase — detecting languages, frameworks, dependencies, and project structure — then uses AI to generate a comprehensive, professional README tailored to your project.

## ✨ Features

- **Smart Project Scanning** — Automatically detects 30+ languages, 40+ frameworks, dependencies, entry points, CI/CD, Docker, and more
- **Multiple AI Providers** — Works with OpenAI (GPT-4o) and Anthropic (Claude) — bring your own API key
- **Configurable Output** — Markdown or reStructuredText, three writing styles, toggleable sections
- **Badges** — Auto-generates relevant shields.io badges
- **Table of Contents** — Optional auto-generated TOC
- **API Documentation** — Extracts and documents public APIs
- **Contributing Guide** — Generates a contributing section based on your project setup
- **Config File Support** — Drop a `.readmegen.yml` in your project for persistent settings
- **Dry Run Mode** — Preview the generated README before writing to disk

## 🚀 Quick Start

### Installation

```bash
pip install readmegen
```

### Usage

```bash
# Set your API key
export OPENAI_API_KEY="sk-..."
# or
export ANTHROPIC_API_KEY="sk-ant-..."

# Generate README for current directory
readmegen .

# Generate for a specific project
readmegen /path/to/your/project

# Preview without writing
readmegen . --dry-run

# Use Anthropic Claude
readmegen . --provider anthropic

# Minimal style, no badges
readmegen . --style minimal --no-badges

# Output as reStructuredText
readmegen . --format rst --output README.rst
```

## ⚙️ Configuration

Create a `.readmegen.yml` in your project root:

```yaml
# AI Provider: "openai" or "anthropic"
provider: openai

# Writing style: "professional", "casual", or "minimal"
style: professional

# Output settings
output: README.md
format: md

# Sections to include
badges: true
toc: true
api_docs: true
contributing: true
license: true
```

CLI flags override config file settings.

## 🎯 CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--provider, -p` | AI provider (`openai` / `anthropic`) | Auto-detect |
| `--model, -m` | Model name | `gpt-4o` / `claude-sonnet-4-20250514` |
| `--output, -o` | Output filename | `README.md` |
| `--format, -f` | Output format (`md` / `rst`) | `md` |
| `--style` | Writing style (`professional` / `casual` / `minimal`) | `professional` |
| `--badges / --no-badges` | Include badges | `true` |
| `--toc / --no-toc` | Table of contents | `true` |
| `--api-docs / --no-api-docs` | API documentation | `true` |
| `--contributing / --no-contributing` | Contributing section | `true` |
| `--dry-run` | Preview without writing | `false` |

## 🔍 What It Detects

ReadmeGen scans your project and extracts:

- **Languages** — Python, JavaScript, TypeScript, Go, Rust, Java, C++, and 25+ more
- **Frameworks** — Django, Flask, FastAPI, React, Next.js, Vue, Express, and 30+ more
- **Dependencies** — From requirements.txt, package.json, pyproject.toml, Cargo.toml, go.mod
- **Project Structure** — Entry points, test directories, CI/CD configs
- **Infrastructure** — Docker, Kubernetes, Helm, Terraform, Serverless
- **License** — MIT, Apache, GPL, BSD auto-detection

## 📋 Requirements

- Python 3.9+
- An OpenAI or Anthropic API key

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
