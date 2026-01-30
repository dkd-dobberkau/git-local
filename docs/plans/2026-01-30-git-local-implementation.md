# git-local Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local GitLab-style web app to browse and manage Git repositories in `/Users/olivier/Versioncontrol/local`

**Architecture:** FastAPI backend scans directory for Git repos, extracts status info via GitPython, serves Jinja2 templates with HTMX for dynamic updates. Letter-style monochrome CSS.

**Tech Stack:** Python 3.11+, FastAPI, Jinja2, HTMX, GitPython, uv

---

## Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `src/git_local/__init__.py`
- Create: `README.md`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "git-local"
version = "0.1.0"
description = "Local GitLab-style overview for Git repositories"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "jinja2>=3.1.0",
    "gitpython>=3.1.0",
    "python-multipart>=0.0.9",
]

[project.scripts]
git-local = "git_local.main:run"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Step 2: Create package init**

```python
# src/git_local/__init__.py
"""git-local: Local GitLab-style overview for Git repositories."""
```

**Step 3: Create README**

```markdown
# git-local

Local GitLab-style overview for Git repositories.

## Quick Start

```bash
uv run fastapi dev src/git_local/main.py
```

Open http://localhost:8000
```

**Step 4: Verify uv can resolve dependencies**

Run: `cd /Users/olivier/Versioncontrol/local/git-local && uv sync`
Expected: Dependencies installed successfully

**Step 5: Commit**

```bash
git add pyproject.toml src/git_local/__init__.py README.md uv.lock
git commit -m "feat: project setup with dependencies"
```

---

## Task 2: Git Scanner Module

**Files:**
- Create: `src/git_local/git_scanner.py`
- Create: `tests/test_git_scanner.py`

**Step 1: Write failing test for scan_repositories**

```python
# tests/test_git_scanner.py
import tempfile
import os
from pathlib import Path

from git import Repo

from git_local.git_scanner import scan_repositories, RepoInfo


def test_scan_repositories_finds_git_repos():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a git repo
        repo_path = Path(tmpdir) / "test-repo"
        repo_path.mkdir()
        repo = Repo.init(repo_path)

        # Create initial commit
        readme = repo_path / "README.md"
        readme.write_text("# Test")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")

        # Create non-git directory
        non_git = Path(tmpdir) / "not-a-repo"
        non_git.mkdir()

        # Scan
        repos = scan_repositories(tmpdir)

        assert len(repos) == 1
        assert repos[0].name == "test-repo"
        assert repos[0].branch == "master" or repos[0].branch == "main"


def test_repo_info_detects_dirty_state():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "dirty-repo"
        repo_path.mkdir()
        repo = Repo.init(repo_path)

        # Initial commit
        readme = repo_path / "README.md"
        readme.write_text("# Test")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")

        # Make it dirty
        readme.write_text("# Modified")

        repos = scan_repositories(tmpdir)

        assert repos[0].is_dirty is True
        assert repos[0].dirty_count >= 1
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/olivier/Versioncontrol/local/git-local && uv run pytest tests/test_git_scanner.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Write git_scanner implementation**

```python
# src/git_local/git_scanner.py
"""Git repository scanner and info extractor."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from git import Repo, InvalidGitRepositoryError


@dataclass
class RepoInfo:
    """Information about a Git repository."""

    name: str
    path: str
    branch: str
    is_dirty: bool
    dirty_count: int
    branch_count: int
    last_commit_message: str
    last_commit_date: datetime
    last_commit_relative: str
    remote_url: str | None


def get_relative_time(dt: datetime) -> str:
    """Convert datetime to relative time string (German)."""
    now = datetime.now()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return "gerade eben"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"vor {minutes} Min."
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"vor {hours} Std."
    elif seconds < 604800:
        days = int(seconds / 86400)
        if days == 1:
            return "gestern"
        return f"vor {days} Tagen"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        if weeks == 1:
            return "vor 1 Woche"
        return f"vor {weeks} Wochen"
    else:
        months = int(seconds / 2592000)
        if months == 1:
            return "vor 1 Monat"
        return f"vor {months} Monaten"


def get_repo_info(repo_path: Path) -> RepoInfo | None:
    """Extract information from a Git repository."""
    try:
        repo = Repo(repo_path)
    except InvalidGitRepositoryError:
        return None

    # Current branch
    try:
        branch = repo.active_branch.name
    except TypeError:
        branch = "HEAD detached"

    # Dirty state
    is_dirty = repo.is_dirty(untracked_files=True)
    dirty_count = len(repo.index.diff(None)) + len(repo.untracked_files)

    # Branch count
    branch_count = len(repo.branches)

    # Last commit
    try:
        last_commit = repo.head.commit
        last_commit_message = last_commit.message.strip().split("\n")[0][:60]
        last_commit_date = datetime.fromtimestamp(last_commit.committed_date)
        last_commit_relative = get_relative_time(last_commit_date)
    except ValueError:
        last_commit_message = "No commits"
        last_commit_date = datetime.now()
        last_commit_relative = "-"

    # Remote URL
    remote_url = None
    try:
        if repo.remotes:
            remote_url = repo.remotes.origin.url
    except AttributeError:
        pass

    return RepoInfo(
        name=repo_path.name,
        path=str(repo_path),
        branch=branch,
        is_dirty=is_dirty,
        dirty_count=dirty_count,
        branch_count=branch_count,
        last_commit_message=last_commit_message,
        last_commit_date=last_commit_date,
        last_commit_relative=last_commit_relative,
        remote_url=remote_url,
    )


def scan_repositories(base_path: str) -> list[RepoInfo]:
    """Scan directory for Git repositories."""
    base = Path(base_path)
    repos = []

    for item in sorted(base.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            repo_info = get_repo_info(item)
            if repo_info:
                repos.append(repo_info)

    # Sort by last commit date (newest first)
    repos.sort(key=lambda r: r.last_commit_date, reverse=True)

    return repos
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/olivier/Versioncontrol/local/git-local && uv run pytest tests/test_git_scanner.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/git_local/git_scanner.py tests/test_git_scanner.py
git commit -m "feat: git scanner module with repo info extraction"
```

---

## Task 3: FastAPI App Structure

**Files:**
- Create: `src/git_local/main.py`
- Create: `src/git_local/config.py`

**Step 1: Create config module**

```python
# src/git_local/config.py
"""Application configuration."""

from pathlib import Path

# Default scan path
REPO_BASE_PATH = "/Users/olivier/Versioncontrol/local"

# App settings
APP_TITLE = "GIT LOCAL"
HOST = "127.0.0.1"
PORT = 8000
```

**Step 2: Create main FastAPI app**

```python
# src/git_local/main.py
"""FastAPI application for git-local."""

import subprocess
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from git_local.config import REPO_BASE_PATH, APP_TITLE, HOST, PORT
from git_local.git_scanner import scan_repositories, get_repo_info

app = FastAPI(title=APP_TITLE)

# Setup paths
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main page with repository list."""
    repos = scan_repositories(REPO_BASE_PATH)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": APP_TITLE,
            "repos": repos,
            "repo_count": len(repos),
        },
    )


@app.get("/partials/repos", response_class=HTMLResponse)
async def repos_partial(request: Request):
    """HTMX partial for repository list."""
    repos = scan_repositories(REPO_BASE_PATH)
    return templates.TemplateResponse(
        "components/repo_list.html",
        {
            "request": request,
            "repos": repos,
            "repo_count": len(repos),
        },
    )


@app.post("/api/open/vscode/{repo_name}")
async def open_vscode(repo_name: str):
    """Open repository in VS Code."""
    repo_path = Path(REPO_BASE_PATH) / repo_name
    if repo_path.exists():
        subprocess.Popen(["code", str(repo_path)])
        return {"status": "ok"}
    return {"status": "error", "message": "Repository not found"}


@app.post("/api/open/terminal/{repo_name}")
async def open_terminal(repo_name: str):
    """Open repository in Terminal."""
    repo_path = Path(REPO_BASE_PATH) / repo_name
    if repo_path.exists():
        subprocess.Popen(
            ["open", "-a", "Terminal", str(repo_path)]
        )
        return {"status": "ok"}
    return {"status": "error", "message": "Repository not found"}


@app.post("/api/open/finder/{repo_name}")
async def open_finder(repo_name: str):
    """Open repository in Finder."""
    repo_path = Path(REPO_BASE_PATH) / repo_name
    if repo_path.exists():
        subprocess.Popen(["open", str(repo_path)])
        return {"status": "ok"}
    return {"status": "error", "message": "Repository not found"}


def run():
    """Run the application."""
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
```

**Step 3: Create directories for templates and static**

Run: `mkdir -p /Users/olivier/Versioncontrol/local/git-local/src/git_local/templates/components /Users/olivier/Versioncontrol/local/git-local/src/git_local/static`

**Step 4: Commit**

```bash
git add src/git_local/main.py src/git_local/config.py
git commit -m "feat: FastAPI app with routes for pages and actions"
```

---

## Task 4: Base Template

**Files:**
- Create: `src/git_local/templates/base.html`

**Step 1: Create base template**

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title }}</title>
  <link rel="stylesheet" href="/static/style.css">
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
</head>
<body>
  <div id="app">
    {% block content %}{% endblock %}
  </div>
</body>
</html>
```

**Step 2: Commit**

```bash
git add src/git_local/templates/base.html
git commit -m "feat: base HTML template with HTMX"
```

---

## Task 5: Index Page Template

**Files:**
- Create: `src/git_local/templates/index.html`
- Create: `src/git_local/templates/components/repo_list.html`

**Step 1: Create index template**

```html
{% extends "base.html" %}

{% block content %}
<header class="header">
  <div class="header-title">{{ title }}</div>
  <div class="header-actions">
    <button
      class="header-icon"
      hx-get="/partials/repos"
      hx-target="#repo-list"
      hx-swap="innerHTML"
      title="Aktualisieren"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/>
        <path d="M21 3v5h-5"/>
      </svg>
    </button>
  </div>
</header>

<main class="main">
  <div class="repo-count">{{ repo_count }} Repositories</div>

  <div id="repo-list">
    {% include "components/repo_list.html" %}
  </div>
</main>
{% endblock %}
```

**Step 2: Create repo list component**

```html
<div class="repo-list">
  {% for repo in repos %}
  <div class="repo-item">
    <div class="repo-item-content">
      <div class="repo-item-name">{{ repo.name }}</div>
      <div class="repo-item-meta">
        <span class="repo-item-branch">{{ repo.branch }}</span>
        <span class="repo-item-status {% if repo.is_dirty %}dirty{% endif %}">
          {% if repo.is_dirty %}{{ repo.dirty_count }} uncommitted{% else %}clean{% endif %}
        </span>
        <span class="repo-item-branches">{{ repo.branch_count }} branch{% if repo.branch_count != 1 %}es{% endif %}</span>
      </div>
      <div class="repo-item-commit">
        "{{ repo.last_commit_message }}" · {{ repo.last_commit_relative }}
      </div>
    </div>
    <div class="repo-item-actions">
      <button
        class="action-btn"
        hx-post="/api/open/finder/{{ repo.name }}"
        hx-swap="none"
        title="Im Finder öffnen"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        </svg>
      </button>
      <button
        class="action-btn"
        hx-post="/api/open/vscode/{{ repo.name }}"
        hx-swap="none"
        title="In VS Code öffnen"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="16 18 22 12 16 6"/>
          <polyline points="8 6 2 12 8 18"/>
        </svg>
      </button>
      <button
        class="action-btn"
        hx-post="/api/open/terminal/{{ repo.name }}"
        hx-swap="none"
        title="Terminal öffnen"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="4 17 10 11 4 5"/>
          <line x1="12" y1="19" x2="20" y2="19"/>
        </svg>
      </button>
    </div>
  </div>
  {% endfor %}

  {% if not repos %}
  <div class="empty-state">Keine Repositories gefunden.</div>
  {% endif %}
</div>
```

**Step 3: Commit**

```bash
git add src/git_local/templates/index.html src/git_local/templates/components/repo_list.html
git commit -m "feat: index page and repo list templates"
```

---

## Task 6: CSS Styling (Letter-Style)

**Files:**
- Create: `src/git_local/static/style.css`

**Step 1: Create Letter-style CSS**

```css
/* ==========================================================================
   git-local - Monochrome Design System (Letter-Style)
   ========================================================================== */

/* --------------------------------------------------------------------------
   CSS Variables
   -------------------------------------------------------------------------- */
:root {
  --black: #000;
  --gray-900: #111;
  --gray-800: #222;
  --gray-700: #333;
  --gray-600: #555;
  --gray-500: #777;
  --gray-400: #999;
  --gray-300: #bbb;
  --gray-200: #ddd;
  --gray-100: #f5f5f5;
  --white: #fff;

  --color-bg: var(--white);
  --color-bg-elevated: var(--white);
  --color-bg-muted: var(--gray-100);
  --color-fg: var(--black);
  --color-fg-muted: var(--gray-600);
  --color-fg-subtle: var(--gray-500);
  --color-fg-faint: var(--gray-400);
  --color-border: var(--gray-200);
  --color-border-strong: var(--gray-400);

  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;

  --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --font-size-xs: 11px;
  --font-size-sm: 13px;
  --font-size-base: 15px;

  --line-height: 1.5;
  --border: 1px solid var(--color-border);
  --transition: 150ms ease;
}

/* --------------------------------------------------------------------------
   Dark Mode
   -------------------------------------------------------------------------- */
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: #0d0d0d;
    --color-bg-elevated: #1a1a1a;
    --color-bg-muted: #252525;
    --color-fg: #f0f0f0;
    --color-fg-muted: #b0b0b0;
    --color-fg-subtle: #888;
    --color-fg-faint: #666;
    --color-border: #333;
    --color-border-strong: #555;
  }
}

/* --------------------------------------------------------------------------
   Reset
   -------------------------------------------------------------------------- */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-size: 16px;
  -webkit-text-size-adjust: 100%;
}

body {
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  line-height: var(--line-height);
  color: var(--color-fg);
  background: var(--color-bg);
  -webkit-font-smoothing: antialiased;
}

/* --------------------------------------------------------------------------
   App Container
   -------------------------------------------------------------------------- */
#app {
  max-width: 100%;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--color-bg);
}

.main {
  max-width: 720px;
  margin: 0 auto;
  padding: var(--space-lg);
}

/* --------------------------------------------------------------------------
   Header
   -------------------------------------------------------------------------- */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg);
  border-bottom: var(--border);
  background: var(--color-bg-elevated);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-title {
  font-size: var(--font-size-sm);
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
}

.header-actions {
  display: flex;
  gap: var(--space-xs);
}

.header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  color: var(--color-fg);
  background: none;
  border: none;
  cursor: pointer;
  transition: opacity var(--transition);
}

.header-icon:hover {
  opacity: 0.6;
}

/* --------------------------------------------------------------------------
   Repo Count
   -------------------------------------------------------------------------- */
.repo-count {
  font-size: var(--font-size-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-fg-faint);
  margin-bottom: var(--space-lg);
}

/* --------------------------------------------------------------------------
   Repo List
   -------------------------------------------------------------------------- */
.repo-list {
  display: flex;
  flex-direction: column;
}

.repo-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-md) 0;
  border-bottom: var(--border);
}

.repo-item:first-child {
  border-top: var(--border);
}

.repo-item-content {
  flex: 1;
  min-width: 0;
}

.repo-item-name {
  font-size: var(--font-size-base);
  font-weight: 600;
  margin-bottom: var(--space-xs);
}

.repo-item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  font-size: var(--font-size-xs);
  color: var(--color-fg-subtle);
  margin-bottom: var(--space-xs);
}

.repo-item-meta span::after {
  content: " ·";
  margin-left: var(--space-xs);
}

.repo-item-meta span:last-child::after {
  content: "";
}

.repo-item-branch {
  font-weight: 500;
}

.repo-item-status.dirty {
  color: var(--color-fg);
  font-weight: 500;
}

.repo-item-commit {
  font-size: var(--font-size-xs);
  color: var(--color-fg-faint);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* --------------------------------------------------------------------------
   Repo Actions
   -------------------------------------------------------------------------- */
.repo-item-actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  color: var(--color-fg-muted);
  background: var(--color-bg-muted);
  border: none;
  cursor: pointer;
  transition: all var(--transition);
}

.action-btn:hover {
  background: var(--color-border);
  color: var(--color-fg);
}

/* --------------------------------------------------------------------------
   Empty State
   -------------------------------------------------------------------------- */
.empty-state {
  padding: var(--space-2xl) var(--space-md);
  text-align: center;
  color: var(--color-fg-faint);
  font-size: var(--font-size-sm);
}

/* --------------------------------------------------------------------------
   HTMX Loading States
   -------------------------------------------------------------------------- */
.htmx-request .header-icon svg {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* --------------------------------------------------------------------------
   Responsive
   -------------------------------------------------------------------------- */
@media (max-width: 480px) {
  .header {
    padding: var(--space-md);
  }

  .main {
    padding: var(--space-md);
  }

  .repo-item {
    flex-direction: column;
    gap: var(--space-sm);
  }

  .repo-item-actions {
    align-self: flex-end;
  }
}
```

**Step 2: Commit**

```bash
git add src/git_local/static/style.css
git commit -m "feat: Letter-style CSS with dark mode support"
```

---

## Task 7: Test Application

**Step 1: Run the application**

Run: `cd /Users/olivier/Versioncontrol/local/git-local && uv run fastapi dev src/git_local/main.py`
Expected: Server starts on http://127.0.0.1:8000

**Step 2: Test in browser**

- Open http://localhost:8000
- Verify repo list displays
- Click refresh button
- Click VS Code button on a repo
- Click Finder button on a repo

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete git-local v1.0 - local GitLab-style overview"
```

---

## Summary

| Task | Description |
|------|-------------|
| 1 | Project setup (pyproject.toml, uv) |
| 2 | Git scanner module with tests |
| 3 | FastAPI app structure |
| 4 | Base HTML template |
| 5 | Index page + repo list component |
| 6 | Letter-style CSS |
| 7 | Integration test |
