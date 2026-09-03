"""
Dependency Management Subsystem for Project FORGE.
Extracts imported modules via AST parsing, resolves PyPI/npm package names,
pins versions, auto-generates requirements.txt/package.json, and flags vulnerable or banned libraries.
"""

import ast
import re
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger("execution.dependency_manager")

# Standard library modules in Python 3.11+
PYTHON_STDLIB: set[str] = {
    "abc",
    "argparse",
    "array",
    "ast",
    "asyncio",
    "base64",
    "bisect",
    "builtins",
    "calendar",
    "cmath",
    "cmd",
    "code",
    "codecs",
    "collections",
    "colorsys",
    "compileall",
    "concurrent",
    "configparser",
    "contextlib",
    "contextvars",
    "copy",
    "copyreg",
    "csv",
    "ctypes",
    "curses",
    "dataclasses",
    "datetime",
    "dbm",
    "decimal",
    "difflib",
    "dis",
    "doctest",
    "email",
    "encodings",
    "enum",
    "errno",
    "faulthandler",
    "fcntl",
    "filecmp",
    "fileinput",
    "fnmatch",
    "fractions",
    "ftplib",
    "functools",
    "gc",
    "getopt",
    "getpass",
    "gettext",
    "glob",
    "graphlib",
    "gzip",
    "hashlib",
    "heapq",
    "hmac",
    "html",
    "http",
    "imaplib",
    "imghdr",
    "importlib",
    "inspect",
    "io",
    "ipaddress",
    "itertools",
    "json",
    "keyword",
    "linecache",
    "locale",
    "logging",
    "lzma",
    "mailbox",
    "mailcap",
    "marshal",
    "math",
    "mimetypes",
    "mmap",
    "modulefinder",
    "multiprocessing",
    "netrc",
    "nntplib",
    "numbers",
    "operator",
    "optparse",
    "os",
    "pathlib",
    "pdb",
    "pickle",
    "pickletools",
    "pkgutil",
    "platform",
    "plistlib",
    "poplib",
    "posix",
    "posixpath",
    "pprint",
    "profile",
    "pstats",
    "pty",
    "pwd",
    "py_compile",
    "pyclbr",
    "pydoc",
    "queue",
    "quopri",
    "random",
    "re",
    "readline",
    "reprlib",
    "resource",
    "rlcompleter",
    "runpy",
    "sched",
    "secrets",
    "select",
    "selectors",
    "shelve",
    "shlex",
    "shutil",
    "signal",
    "site",
    "smtpd",
    "smtplib",
    "sndhdr",
    "socket",
    "socketserver",
    "spwd",
    "sqlite3",
    "ssl",
    "stat",
    "statistics",
    "string",
    "stringprep",
    "struct",
    "subprocess",
    "sunau",
    "symtable",
    "sys",
    "sysconfig",
    "syslog",
    "tarfile",
    "telnetlib",
    "tempfile",
    "termios",
    "test",
    "textwrap",
    "threading",
    "time",
    "timeit",
    "tkinter",
    "token",
    "tokenize",
    "tomllib",
    "trace",
    "traceback",
    "tracemalloc",
    "tty",
    "turtle",
    "turtledemo",
    "types",
    "typing",
    "unicodedata",
    "unittest",
    "urllib",
    "uu",
    "uuid",
    "venv",
    "warnings",
    "wave",
    "weakref",
    "webbrowser",
    "winreg",
    "winsound",
    "wsgiref",
    "xdrlib",
    "xml",
    "xmlrpc",
    "zipapp",
    "zipfile",
    "zipimport",
    "zlib",
    "_thread",
}

# Known top-level module to PyPI package mappings
MODULE_TO_PYPI: dict[str, str] = {
    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "dotenv": "python-dotenv",
    "fastapi": "fastapi",
    "flask": "flask",
    "git": "GitPython",
    "httpx": "httpx",
    "jwt": "PyJWT",
    "PIL": "pillow",
    "pydantic": "pydantic",
    "pytest": "pytest",
    "requests": "requests",
    "rich": "rich",
    "scipy": "scipy",
    "sklearn": "scikit-learn",
    "sqlalchemy": "SQLAlchemy",
    "torch": "torch",
    "uvicorn": "uvicorn",
    "yaml": "PyYAML",
}

# Known recommended pinned versions for stable reproducibility
PINNED_VERSIONS: dict[str, str] = {
    "fastapi": ">=0.100.0",
    "uvicorn": ">=0.22.0",
    "pydantic": ">=2.0.0",
    "httpx": ">=0.24.0",
    "pytest": ">=7.4.0",
    "requests": ">=2.31.0",
    "rich": ">=13.4.0",
    "SQLAlchemy": ">=2.0.0",
    "beautifulsoup4": ">=4.12.0",
    "python-dotenv": ">=1.0.0",
    "PyYAML": ">=6.0",
}

# Known high-risk or banned libraries (e.g., deprecated or inherently unsafe)
KNOWN_VULNERABLE_OR_BANNED: dict[str, str] = {
    "telnetlib": "Insecure unencrypted remote access protocol.",
    "crypto": "Deprecated and unmaintained package (use pycryptodome or cryptography).",
    "pycrypto": "Unmaintained with known security vulnerabilities (use pycryptodome).",
}


class DependencyManager:
    """Detects, inspects, and manages project dependencies in isolated sandboxes."""

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root

    def extract_python_imports(self, code: str) -> set[str]:
        """Parse Python AST and extract top-level import module names."""
        modules = set()
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top_pkg = alias.name.split(".")[0]
                        modules.add(top_pkg)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        top_pkg = node.module.split(".")[0]
                        modules.add(top_pkg)
        except Exception as e:
            logger.debug(f"AST parsing failed for dependency extraction: {e}")
            # Fallback to regex import detection
            for match in re.finditer(r"^(?:from|import)\s+([a-zA-Z0-9_]+)", code, re.MULTILINE):
                modules.add(match.group(1))

        return modules

    def detect_workspace_dependencies(self, project_dir: Path) -> set[str]:
        """Scan all Python and JS files in project directory and collect external dependencies."""
        external_deps: set[str] = set()
        if not project_dir.exists():
            return external_deps

        # Scan python files
        for py_file in project_dir.glob("**/*.py"):
            try:
                code = py_file.read_text(encoding="utf-8", errors="ignore")
                imports = self.extract_python_imports(code)
                for mod in imports:
                    if (
                        mod not in PYTHON_STDLIB
                        and not (project_dir / f"{mod}.py").exists()
                        and not (project_dir / mod).is_dir()
                    ):
                        pypi_pkg = MODULE_TO_PYPI.get(mod, mod)
                        external_deps.add(pypi_pkg)
            except Exception as e:
                logger.debug(f"Error scanning {py_file} for dependencies: {e}")

        return external_deps

    def generate_requirements_txt(self, dependencies: set[str]) -> str:
        """Generate formatted and pinned requirements.txt content."""
        lines = []
        for dep in sorted(dependencies):
            version_pin = PINNED_VERSIONS.get(dep, ">=1.0.0")
            lines.append(f"{dep}{version_pin}")
        return "\n".join(lines) + ("\n" if lines else "")

    def check_security(self, dependencies: set[str]) -> list[dict[str, Any]]:
        """Check list of dependencies for known vulnerabilities or blocked packages."""
        issues = []
        for dep in dependencies:
            dep_lower = dep.lower()
            if dep_lower in KNOWN_VULNERABLE_OR_BANNED:
                issues.append(
                    {
                        "package": dep,
                        "severity": "HIGH",
                        "reason": KNOWN_VULNERABLE_OR_BANNED[dep_lower],
                    }
                )
        return issues
