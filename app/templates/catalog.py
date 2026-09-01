"""
Starter Code and Component Template Catalog for Project FORGE.
"""

# --- 1. Base Project Templates ---

HTML_WEBSITE_BASE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body class="{{body_class}}">
    <header class="site-header">
        <nav class="navbar" aria-label="Main Navigation">
            <a href="#" class="nav-brand">{{brand_name}}</a>
            <div class="nav-links">
                <a href="#about">About</a>
                <a href="#projects">Projects</a>
                <a href="#contact">Contact</a>
            </div>
            <button id="theme-toggle" class="btn btn-secondary" aria-label="Toggle Dark Mode">🌓 Toggle Theme</button>
        </nav>
    </header>

    <main id="main-content">
        <section id="hero" class="hero-section">
            <div class="hero-content">
                <h1 class="hero-title">{{hero_title}}</h1>
                <p class="hero-subtitle">{{hero_subtitle}}</p>
                <div class="hero-actions">
                    <a href="#projects" class="btn btn-primary">View Projects</a>
                    <a href="#contact" class="btn btn-outline">Get In Touch</a>
                </div>
            </div>
        </section>

        <section id="about" class="section">
            <div class="container">
                <h2>About</h2>
                <p>{{about_description}}</p>
            </div>
        </section>

        <section id="projects" class="section">
            <div class="container">
                <h2>Projects</h2>
                <div class="grid cards-grid">
                    <article class="card">
                        <h3>Project Alpha</h3>
                        <p>High performance distributed systems and autonomous tooling.</p>
                    </article>
                    <article class="card">
                        <h3>Project Beta</h3>
                        <p>Modern full-stack web applications and microservices.</p>
                    </article>
                </div>
            </div>
        </section>

        <section id="contact" class="section">
            <div class="container">
                <h2>Contact</h2>
                <form id="contact-form" class="contact-form">
                    <div class="form-group">
                        <label for="name">Name</label>
                        <input type="text" id="name" name="name" required placeholder="Your Name">
                    </div>
                    <div class="form-group">
                        <label for="email">Email</label>
                        <input type="email" id="email" name="email" required placeholder="Your Email">
                    </div>
                    <div class="form-group">
                        <label for="message">Message</label>
                        <textarea id="message" name="message" rows="4" required placeholder="Your message..."></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">Send Message</button>
                </form>
            </div>
        </section>
    </main>

    <footer class="site-footer">
        <div class="container">
            <p>&copy; 2026 {{brand_name}}. Built with Project FORGE.</p>
        </div>
    </footer>

    <script src="app.js"></script>
</body>
</html>
"""

CSS_BASE = """:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f8f9fa;
    --text-primary: #1a202c;
    --text-secondary: #4a5568;
    --accent-color: #3182ce;
    --border-color: #e2e8f0;
    --card-bg: #ffffff;
    --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

[data-theme="dark"], body.dark-mode {
    --bg-primary: #1a202c;
    --bg-secondary: #2d3748;
    --text-primary: #f7fafc;
    --text-secondary: #cbd5e0;
    --accent-color: #63b3ed;
    --border-color: #4a5568;
    --card-bg: #2d3748;
    --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background-color: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    transition: background-color 0.3s ease, color 0.3s ease;
}

.container {
    max-width: 1100px;
    margin: 0 auto;
    padding: 0 1.5rem;
}

/* Header & Navbar */
.site-header {
    background-color: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    position: sticky;
    top: 0;
    z-index: 100;
}

.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1100px;
    margin: 0 auto;
    padding: 1rem 1.5rem;
}

.nav-brand {
    font-weight: 700;
    font-size: 1.25rem;
    color: var(--text-primary);
    text-decoration: none;
}

.nav-links {
    display: flex;
    gap: 1.5rem;
}

.nav-links a {
    color: var(--text-secondary);
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s;
}

.nav-links a:hover {
    color: var(--accent-color);
}

/* Buttons */
.btn {
    display: inline-block;
    padding: 0.6rem 1.2rem;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    border: none;
    transition: all 0.2s ease;
}

.btn-primary {
    background-color: var(--accent-color);
    color: #ffffff;
}

.btn-primary:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}

.btn-secondary {
    background-color: var(--bg-primary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
}

.btn-outline {
    background-color: transparent;
    color: var(--accent-color);
    border: 1px solid var(--accent-color);
}

/* Hero Section */
.hero-section {
    padding: 4rem 1.5rem;
    text-align: center;
    background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
}

.hero-title {
    font-size: 2.75rem;
    margin-bottom: 1rem;
    color: var(--text-primary);
}

.hero-subtitle {
    font-size: 1.25rem;
    color: var(--text-secondary);
    max-width: 700px;
    margin: 0 auto 2rem;
}

.hero-actions {
    display: flex;
    justify-content: center;
    gap: 1rem;
}

/* Sections */
.section {
    padding: 3.5rem 0;
}

.section h2 {
    font-size: 2rem;
    margin-bottom: 1.5rem;
    text-align: center;
}

/* Cards Grid */
.cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-top: 1.5rem;
}

.card {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: var(--shadow);
}

.card h3 {
    margin-bottom: 0.75rem;
    color: var(--text-primary);
}

/* Forms */
.contact-form {
    max-width: 600px;
    margin: 0 auto;
    background-color: var(--card-bg);
    padding: 2rem;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow);
}

.form-group {
    margin-bottom: 1.25rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-secondary);
}

.form-group input,
.form-group textarea {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    background-color: var(--bg-primary);
    color: var(--text-primary);
    font-family: inherit;
}

/* Footer */
.site-footer {
    background-color: var(--bg-secondary);
    border-top: 1px solid var(--border-color);
    padding: 2rem 0;
    text-align: center;
    color: var(--text-secondary);
    margin-top: 3rem;
}
"""

JS_BASE = """document.addEventListener("DOMContentLoaded", () => {
    // Theme toggle functionality
    const themeToggleBtn = document.getElementById("theme-toggle");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

    // Initialize theme from localStorage or system preference
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark" || (!savedTheme && prefersDark)) {
        document.body.classList.add("dark-mode");
        document.documentElement.setAttribute("data-theme", "dark");
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            const isDark = document.body.classList.toggle("dark-mode");
            document.documentElement.setAttribute("data-theme", isDark ? "dark" : "light");
            localStorage.setItem("theme", isDark ? "dark" : "light");
        });
    }

    // Contact form submission handler
    const contactForm = document.getElementById("contact-form");
    if (contactForm) {
        contactForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const formData = new FormData(contactForm);
            const data = Object.fromEntries(formData.entries());
            console.log("Contact form submitted:", data);
            alert("Thank you for your message! We will get back to you soon.");
            contactForm.reset();
        });
    }
});
"""

# --- 2. CLI Project Template ---

PYTHON_CLI_BASE = '''"""
{{cli_name}}: {{cli_description}}
Generated by Project FORGE.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_DB_FILE = Path("data.json")


class StorageManager:
    """Manages JSON file persistence."""
    def __init__(self, filepath: Path = DEFAULT_DB_FILE):
        self.filepath = filepath

    def load(self) -> List[Dict[str, Any]]:
        if not self.filepath.exists():
            return []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save(self, items: List[Dict[str, Any]]) -> None:
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)


def handle_add(args: argparse.Namespace, storage: StorageManager) -> int:
    items = storage.load()
    new_item = {
        "id": len(items) + 1,
        "title": args.title,
        "completed": False,
    }
    items.append(new_item)
    storage.save(items)
    print(f"Added item #{new_item['id']}: {new_item['title']}")
    return 0


def handle_list(args: argparse.Namespace, storage: StorageManager) -> int:
    items = storage.load()
    if not items:
        print("No items found.")
        return 0

    print(f"--- {args.filter.capitalize() if hasattr(args, 'filter') and args.filter else 'All'} Items ({len(items)}) ---")
    for item in items:
        status = "[X]" if item.get("completed") else "[ ]"
        print(f"#{item['id']} {status} {item['title']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="{{cli_name}}",
        description="{{cli_description}}",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    add_parser = subparsers.add_parser("add", help="Add a new item")
    add_parser.add_argument("title", help="Title or description of the item")

    list_parser = subparsers.add_parser("list", help="List all items")
    list_parser.add_argument("--filter", choices=["all", "pending", "done"], default="all", help="Filter items")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    storage = StorageManager()

    if args.command == "add":
        return handle_add(args, storage)
    elif args.command == "list":
        return handle_list(args, storage)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
'''

PYTHON_CLI_TEST_BASE = '''"""
Unit tests for {{cli_name}}.
"""

import os
from pathlib import Path
import pytest
from main import StorageManager, build_parser, main


@pytest.fixture
def temp_storage(tmp_path: Path):
    db_file = tmp_path / "test_data.json"
    storage = StorageManager(filepath=db_file)
    return storage


def test_storage_add_and_load(temp_storage: StorageManager):
    items = temp_storage.load()
    assert len(items) == 0

    temp_storage.save([{"id": 1, "title": "Buy groceries", "completed": False}])
    loaded = temp_storage.load()
    assert len(loaded) == 1
    assert loaded[0]["title"] == "Buy groceries"


def test_cli_help(capsys):
    ret = main(["--help"])
    assert ret == 0


def test_cli_add_and_list(tmp_path: Path, monkeypatch):
    test_file = tmp_path / "data.json"
    monkeypatch.setattr("main.DEFAULT_DB_FILE", test_file)

    ret_add = main(["add", "Write documentation"])
    assert ret_add == 0

    ret_list = main(["list"])
    assert ret_list == 0
'''

# --- 3. FastAPI Service Template ---

FASTAPI_APP_BASE = '''"""
{{api_name}}: {{api_description}}
Generated by Project FORGE.
"""

from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="{{api_title}}",
    description="{{api_description}}",
    version="1.0.0",
)


class Item(BaseModel):
    id: Optional[int] = None
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    completed: bool = False


# In-memory storage
ITEMS_DB: Dict[int, Item] = {}
ID_COUNTER: int = 1


@app.get("/health", summary="Health Check")
def health():
    return {
        "status": "healthy",
        "service": "{{api_name}}",
        "version": "1.0.0",
    }


@app.get("/items", response_model=List[Item], summary="List all items")
def list_items():
    return list(ITEMS_DB.values())


@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED, summary="Create a new item")
def create_item(item: Item):
    global ID_COUNTER
    item.id = ID_COUNTER
    ITEMS_DB[ID_COUNTER] = item
    ID_COUNTER += 1
    return item


@app.get("/items/{item_id}", response_model=Item, summary="Get item by ID")
def get_item(item_id: int):
    if item_id not in ITEMS_DB:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return ITEMS_DB[item_id]


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete item")
def delete_item(item_id: int):
    if item_id not in ITEMS_DB:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    del ITEMS_DB[item_id]
    return None
'''

FASTAPI_TEST_BASE = '''"""
Integration tests for {{api_title}}.
"""

from fastapi.testclient import TestClient
from main import app, ITEMS_DB

client = TestClient(app)


def setup_function():
    ITEMS_DB.clear()


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"


def test_create_and_get_item():
    res = client.post("/items", json={"title": "Test Task", "description": "Verify endpoint"})
    assert res.status_code == 201
    created = res.json()
    assert created["id"] is not None
    assert created["title"] == "Test Task"

    get_res = client.get(f"/items/{created['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Test Task"


def test_get_nonexistent_item():
    res = client.get("/items/9999")
    assert res.status_code == 404
'''
