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
