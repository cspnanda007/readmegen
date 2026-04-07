"""Tests for the project scanner."""

import json
import tempfile
from pathlib import Path

from readmegen.scanner import ProjectScanner


def _make_project(tmp: Path, files: dict[str, str]) -> Path:
    """Create a temporary project with the given files."""
    for name, content in files.items():
        fp = tmp / name
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content)
    return tmp


def test_detect_python_project():
    with tempfile.TemporaryDirectory() as td:
        root = _make_project(Path(td), {
            "requirements.txt": "flask>=2.0\nrequests\n",
            "app.py": "from flask import Flask\napp = Flask(__name__)\n",
            "tests/test_app.py": "def test_index(): pass\n",
        })
        scanner = ProjectScanner(root)
        result = scanner.scan()

        assert "Python" in result.languages
        assert result.framework == "Flask"
        assert result.has_tests
        assert "flask" in result.dependencies
        assert "app.py" in result.entry_points


def test_detect_node_project():
    with tempfile.TemporaryDirectory() as td:
        pkg = {
            "name": "my-app",
            "description": "A test app",
            "dependencies": {"react": "^18.0", "next": "^14.0"},
            "devDependencies": {"jest": "^29.0"},
            "scripts": {"dev": "next dev", "build": "next build"},
        }
        root = _make_project(Path(td), {
            "package.json": json.dumps(pkg),
            "pages/index.tsx": "export default function Home() { return <div/>; }\n",
        })
        scanner = ProjectScanner(root)
        result = scanner.scan()

        assert result.framework in ("Next.js", "React")
        assert "react" in result.dependencies
        assert "jest" in result.dev_dependencies


def test_detect_license():
    with tempfile.TemporaryDirectory() as td:
        root = _make_project(Path(td), {
            "LICENSE": "MIT License\n\nCopyright 2024 ...",
            "main.py": "print('hello')\n",
        })
        scanner = ProjectScanner(root)
        result = scanner.scan()

        assert result.has_license
        assert result.license_type == "MIT"


def test_file_tree_generated():
    with tempfile.TemporaryDirectory() as td:
        root = _make_project(Path(td), {
            "src/main.py": "pass\n",
            "src/utils.py": "pass\n",
            "tests/test_main.py": "pass\n",
        })
        scanner = ProjectScanner(root)
        result = scanner.scan()

        assert "src" in result.file_tree
        assert "main.py" in result.file_tree


def test_summary_line():
    with tempfile.TemporaryDirectory() as td:
        root = _make_project(Path(td), {
            "requirements.txt": "django>=4.0\n",
            "manage.py": "import django\n",
        })
        scanner = ProjectScanner(root)
        result = scanner.scan()

        summary = result.summary_line()
        assert root.name in summary


def test_empty_project():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        scanner = ProjectScanner(root)
        result = scanner.scan()

        assert result.total_files == 0
        assert result.languages == []
        assert result.framework == ""
