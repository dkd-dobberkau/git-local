"""FastAPI application for git-local."""

import subprocess
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from git_local.config import REPO_BASE_PATH, APP_TITLE, HOST, PORT
from git_local.git_scanner import scan_repositories, clear_cache

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
    """HTMX partial for repository list (force refresh)."""
    repos = scan_repositories(REPO_BASE_PATH, force_refresh=True)
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
