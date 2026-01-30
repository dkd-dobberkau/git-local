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
