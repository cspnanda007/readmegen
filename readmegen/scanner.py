"""Project scanner — analyzes a codebase to extract metadata for README generation."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Mappings
# ---------------------------------------------------------------------------

EXTENSION_LANG = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".jsx": "React",
    ".tsx": "React/TypeScript", ".go": "Go", ".rs": "Rust", ".java": "Java",
    ".kt": "Kotlin", ".rb": "Ruby", ".php": "PHP", ".cs": "C#", ".cpp": "C++",
    ".c": "C", ".swift": "Swift", ".dart": "Dart", ".lua": "Lua", ".r": "R",
    ".R": "R", ".scala": "Scala", ".ex": "Elixir", ".exs": "Elixir",
    ".hs": "Haskell", ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".yml": "YAML", ".yaml": "YAML", ".toml": "TOML", ".sql": "SQL",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".vue": "Vue",
    ".svelte": "Svelte",
}

FRAMEWORK_DETECTORS: list[tuple[str, str, Optional[str]]] = [
    # (file_or_dir, framework_name, key_to_check_in_json)
    ("package.json", "Node.js", None),
    ("next.config.js", "Next.js", None),
    ("next.config.mjs", "Next.js", None),
    ("next.config.ts", "Next.js", None),
    ("nuxt.config.ts", "Nuxt", None),
    ("nuxt.config.js", "Nuxt", None),
    ("angular.json", "Angular", None),
    ("svelte.config.js", "SvelteKit", None),
    ("remix.config.js", "Remix", None),
    ("astro.config.mjs", "Astro", None),
    ("vite.config.ts", "Vite", None),
    ("vite.config.js", "Vite", None),
    ("Cargo.toml", "Rust/Cargo", None),
    ("go.mod", "Go Modules", None),
    ("Gemfile", "Ruby/Bundler", None),
    ("composer.json", "PHP/Composer", None),
    ("build.gradle", "Gradle", None),
    ("build.gradle.kts", "Gradle (Kotlin)", None),
    ("pom.xml", "Maven", None),
    ("pubspec.yaml", "Flutter/Dart", None),
    ("mix.exs", "Elixir/Mix", None),
    ("stack.yaml", "Haskell/Stack", None),
    ("CMakeLists.txt", "CMake", None),
    ("Makefile", "Make", None),
    ("Dockerfile", "Docker", None),
    ("docker-compose.yml", "Docker Compose", None),
    ("docker-compose.yaml", "Docker Compose", None),
    ("kubernetes", "Kubernetes", None),
    ("helm", "Helm", None),
    ("Chart.yaml", "Helm", None),
    ("terraform", "Terraform", None),
    ("serverless.yml", "Serverless", None),
    ("requirements.txt", "Python", None),
    ("setup.py", "Python/setuptools", None),
    ("pyproject.toml", "Python", None),
    ("Pipfile", "Python/Pipenv", None),
    ("poetry.lock", "Python/Poetry", None),
]

PYTHON_FRAMEWORKS = {
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
    "streamlit": "Streamlit", "pytorch": "PyTorch", "torch": "PyTorch",
    "tensorflow": "TensorFlow", "keras": "Keras", "numpy": "NumPy",
    "pandas": "Pandas", "scikit-learn": "scikit-learn", "sklearn": "scikit-learn",
    "celery": "Celery", "sqlalchemy": "SQLAlchemy", "pydantic": "Pydantic",
    "typer": "Typer", "click": "Click", "scrapy": "Scrapy",
    "pytest": "pytest", "sphinx": "Sphinx",
}

JS_FRAMEWORKS = {
    "react": "React", "vue": "Vue.js", "angular": "Angular",
    "express": "Express.js", "next": "Next.js", "nuxt": "Nuxt",
    "svelte": "Svelte", "nestjs": "NestJS", "electron": "Electron",
    "tailwindcss": "Tailwind CSS", "prisma": "Prisma", "mongoose": "Mongoose",
    "jest": "Jest", "vitest": "Vitest", "cypress": "Cypress",
    "playwright": "Playwright",
}

IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist",
    "build", ".next", ".nuxt", "target", "vendor", ".idea", ".vscode",
    "eggs", "*.egg-info", ".eggs", "htmlcov", "coverage",
}

IGNORE_FILES = {
    ".DS_Store", "Thumbs.db", ".gitignore", ".editorconfig",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
    "Pipfile.lock", "Cargo.lock", "composer.lock", "Gemfile.lock",
}

MAX_FILE_READ_BYTES = 64 * 1024  # 64 KB cap per file for scanning


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass
class ScanResult:
    """Holds everything the scanner discovers about a project."""

    project_name: str = ""
    project_path: str = ""
    languages: list[str] = field(default_factory=list)
    framework: str = ""
    dependencies: list[str] = field(default_factory=list)
    dev_dependencies: list[str] = field(default_factory=list)
    scripts: dict[str, str] = field(default_factory=dict)
    file_tree: str = ""
    total_files: int = 0
    has_tests: bool = False
    has_ci: bool = False
    has_docker: bool = False
    has_license: bool = False
    license_type: str = ""
    has_env_example: bool = False
    entry_points: list[str] = field(default_factory=list)
    sample_code: dict[str, str] = field(default_factory=dict)
    description: str = ""
    existing_readme: str = ""

    def summary_line(self) -> str:
        parts = [self.project_name]
        if self.framework:
            parts.append(self.framework)
        elif self.languages:
            parts.append(self.languages[0])
        return " — ".join(parts)

    def to_prompt_context(self) -> str:
        """Serialize scan into a text block the LLM can consume."""
        sections = [
            f"Project Name: {self.project_name}",
            f"Path: {self.project_path}",
            f"Languages: {', '.join(self.languages) if self.languages else 'Unknown'}",
            f"Framework: {self.framework or 'None detected'}",
        ]
        if self.description:
            sections.append(f"Description: {self.description}")
        if self.dependencies:
            sections.append(f"Dependencies: {', '.join(self.dependencies[:40])}")
        if self.dev_dependencies:
            sections.append(f"Dev Dependencies: {', '.join(self.dev_dependencies[:20])}")
        if self.scripts:
            sections.append("Scripts:\n" + "\n".join(
                f"  {k}: {v}" for k, v in list(self.scripts.items())[:15]
            ))
        if self.entry_points:
            sections.append(f"Entry Points: {', '.join(self.entry_points)}")
        sections.append(f"Has Tests: {self.has_tests}")
        sections.append(f"Has CI: {self.has_ci}")
        sections.append(f"Has Docker: {self.has_docker}")
        sections.append(f"License: {self.license_type or 'Not detected'}")
        sections.append(f"Has .env.example: {self.has_env_example}")
        if self.file_tree:
            sections.append(f"File Tree:\n{self.file_tree}")
        if self.sample_code:
            for fname, code in list(self.sample_code.items())[:5]:
                sections.append(f"--- {fname} ---\n{code[:2000]}")
        if self.existing_readme:
            sections.append(f"--- Existing README ---\n{self.existing_readme[:3000]}")
        return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


class ProjectScanner:
    """Walk a project directory and extract metadata."""

    def __init__(self, root: Path):
        self.root = root

    def scan(self) -> ScanResult:
        result = ScanResult(
            project_name=self.root.name,
            project_path=str(self.root),
        )

        all_files = self._collect_files()
        result.total_files = len(all_files)

        # Languages
        lang_counts: dict[str, int] = {}
        for f in all_files:
            lang = EXTENSION_LANG.get(f.suffix.lower())
            if lang and lang not in ("YAML", "TOML", "HTML", "CSS", "SCSS"):
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
        result.languages = sorted(lang_counts, key=lang_counts.get, reverse=True)  # type: ignore

        # Framework detection
        result.framework = self._detect_framework()

        # Dependencies
        self._extract_dependencies(result)

        # Flags
        result.has_tests = any(
            "test" in str(f).lower() or "spec" in str(f).lower() for f in all_files
        )
        result.has_ci = (self.root / ".github" / "workflows").is_dir() or (
            self.root / ".gitlab-ci.yml"
        ).is_file()
        result.has_docker = (self.root / "Dockerfile").is_file()
        result.has_env_example = (self.root / ".env.example").is_file() or (
            self.root / ".env.sample"
        ).is_file()

        # License
        for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "COPYING"):
            lp = self.root / name
            if lp.is_file():
                result.has_license = True
                content = lp.read_text(errors="replace")[:500].lower()
                if "mit" in content:
                    result.license_type = "MIT"
                elif "apache" in content:
                    result.license_type = "Apache-2.0"
                elif "gpl" in content:
                    result.license_type = "GPL"
                elif "bsd" in content:
                    result.license_type = "BSD"
                elif "isc" in content:
                    result.license_type = "ISC"
                else:
                    result.license_type = "Custom"
                break

        # Entry points
        result.entry_points = self._find_entry_points(all_files)

        # File tree (abbreviated)
        result.file_tree = self._build_tree(max_depth=3, max_items=60)

        # Sample code (important files)
        result.sample_code = self._read_sample_files(all_files)

        # Existing README
        for rname in ("README.md", "README.rst", "README.txt", "README"):
            rp = self.root / rname
            if rp.is_file():
                result.existing_readme = rp.read_text(errors="replace")[:3000]
                break

        # Description from pyproject.toml or package.json
        result.description = self._extract_description()

        return result

    # --- helpers ---

    def _collect_files(self) -> list[Path]:
        files: list[Path] = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
            for fn in filenames:
                if fn in IGNORE_FILES:
                    continue
                fp = Path(dirpath) / fn
                if fp.stat().st_size < 2 * 1024 * 1024:  # skip files > 2 MB
                    files.append(fp)
        return files

    def _detect_framework(self) -> str:
        for marker, name, _ in FRAMEWORK_DETECTORS:
            if (self.root / marker).exists():
                # Refine for Python
                if name == "Python":
                    return self._detect_python_framework() or "Python"
                # Refine for Node.js
                if name == "Node.js":
                    return self._detect_js_framework() or "Node.js"
                return name
        return ""

    def _detect_python_framework(self) -> str:
        for reqfile in ("requirements.txt", "Pipfile", "pyproject.toml", "setup.py"):
            rp = self.root / reqfile
            if rp.is_file():
                content = rp.read_text(errors="replace").lower()
                for key, fw in PYTHON_FRAMEWORKS.items():
                    if key in content:
                        return fw
        return ""

    def _detect_js_framework(self) -> str:
        pkg = self.root / "package.json"
        if pkg.is_file():
            try:
                data = json.loads(pkg.read_text(errors="replace"))
                all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                for key, fw in JS_FRAMEWORKS.items():
                    if key in all_deps:
                        return fw
            except (json.JSONDecodeError, KeyError):
                pass
        return ""

    def _extract_dependencies(self, result: ScanResult) -> None:
        # Python
        req = self.root / "requirements.txt"
        if req.is_file():
            lines = req.read_text(errors="replace").splitlines()
            result.dependencies = [
                l.split("==")[0].split(">=")[0].split("<=")[0].split("[")[0].strip()
                for l in lines
                if l.strip() and not l.startswith("#") and not l.startswith("-")
            ][:50]

        # Node
        pkg = self.root / "package.json"
        if pkg.is_file():
            try:
                data = json.loads(pkg.read_text(errors="replace"))
                result.dependencies = list(data.get("dependencies", {}).keys())[:50]
                result.dev_dependencies = list(data.get("devDependencies", {}).keys())[:30]
                result.scripts = dict(list(data.get("scripts", {}).items())[:15])
            except (json.JSONDecodeError, KeyError):
                pass

        # pyproject.toml (basic)
        pp = self.root / "pyproject.toml"
        if pp.is_file() and not result.dependencies:
            content = pp.read_text(errors="replace")
            if "dependencies" in content:
                # Simple extraction
                in_deps = False
                deps: list[str] = []
                for line in content.splitlines():
                    if line.strip().startswith("dependencies"):
                        in_deps = True
                        continue
                    if in_deps:
                        if line.strip().startswith("]"):
                            break
                        cleaned = line.strip().strip('",').split(">=")[0].split("==")[0].strip()
                        if cleaned:
                            deps.append(cleaned)
                result.dependencies = deps[:50]

    def _find_entry_points(self, files: list[Path]) -> list[str]:
        entries: list[str] = []
        for f in files:
            rel = str(f.relative_to(self.root))
            if f.name in ("main.py", "app.py", "server.py", "index.js", "index.ts",
                          "main.go", "main.rs", "manage.py", "wsgi.py", "asgi.py"):
                entries.append(rel)
            elif f.name == "__main__.py":
                entries.append(rel)
        return entries[:10]

    def _build_tree(self, max_depth: int = 3, max_items: int = 60) -> str:
        lines: list[str] = []
        count = 0

        def _walk(path: Path, prefix: str, depth: int):
            nonlocal count
            if depth > max_depth or count > max_items:
                return
            try:
                entries = sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
            except PermissionError:
                return
            dirs = [e for e in entries if e.is_dir() and e.name not in IGNORE_DIRS]
            files = [e for e in entries if e.is_file() and e.name not in IGNORE_FILES]
            items = dirs + files
            for i, entry in enumerate(items):
                if count > max_items:
                    lines.append(f"{prefix}└── ... ({len(items) - i} more)")
                    return
                connector = "├── " if i < len(items) - 1 else "└── "
                icon = "📁 " if entry.is_dir() else ""
                lines.append(f"{prefix}{connector}{icon}{entry.name}")
                count += 1
                if entry.is_dir():
                    extension = "│   " if i < len(items) - 1 else "    "
                    _walk(entry, prefix + extension, depth + 1)

        _walk(self.root, "", 0)
        return "\n".join(lines)

    def _read_sample_files(self, files: list[Path]) -> dict[str, str]:
        """Read key files that help the LLM understand the project."""
        priority_names = {
            "main.py", "app.py", "server.py", "index.js", "index.ts",
            "main.go", "main.rs", "lib.rs", "manage.py", "__main__.py",
            "Makefile", "Dockerfile", "docker-compose.yml",
        }
        samples: dict[str, str] = {}
        for f in files:
            if f.name in priority_names or f.name == "__init__.py":
                try:
                    content = f.read_text(errors="replace")[:MAX_FILE_READ_BYTES]
                    rel = str(f.relative_to(self.root))
                    samples[rel] = content
                except (PermissionError, OSError):
                    pass
            if len(samples) >= 6:
                break
        return samples

    def _extract_description(self) -> str:
        # package.json
        pkg = self.root / "package.json"
        if pkg.is_file():
            try:
                data = json.loads(pkg.read_text(errors="replace"))
                return data.get("description", "")
            except (json.JSONDecodeError, KeyError):
                pass
        # pyproject.toml (very basic)
        pp = self.root / "pyproject.toml"
        if pp.is_file():
            for line in pp.read_text(errors="replace").splitlines():
                if line.strip().startswith("description"):
                    return line.split("=", 1)[-1].strip().strip('"').strip("'")
        return ""
