import os
import subprocess
import tempfile
import threading
from pathlib import Path
from urllib.parse import urlparse, urlunparse, quote

# Overleaf configuration
OVERLEAF_GIT_URL = os.environ.get("OVERLEAF_GIT_URL")
OVERLEAF_TOKEN = os.environ.get("OVERLEAF_TOKEN")
OVERLEAF_EMAIL = os.environ.get("OVERLEAF_EMAIL")

# Cached repo path — set after first clone so subsequent calls just pull
_cached_repo: Path | None = None
_clone_lock = threading.Lock()


def run(cmd, cwd=None):
    """
    Run a shell command and capture stderr/stdout so we can see git errors.
    """
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\n"
            f"returncode: {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    return result


def get_git_email() -> str:
    """
    Return email to use for git commits.
    """
    return OVERLEAF_EMAIL or "overleaf-mcp@example.com"


def _build_auth_url() -> str:
    """Build the authenticated git URL from env vars."""
    parsed = urlparse(OVERLEAF_GIT_URL)
    if not parsed.hostname:
        raise RuntimeError(f"Invalid OVERLEAF_GIT_URL: {OVERLEAF_GIT_URL}")

    user = "git"
    password = quote(OVERLEAF_TOKEN, safe="")

    host = parsed.hostname
    netloc = f"{user}:{password}@{host}"
    if parsed.port:
        netloc += f":{parsed.port}"

    return urlunparse(parsed._replace(netloc=netloc))


def clone_overleaf_repo(pull: bool = False) -> Path:
    """
    Clone or return the cached Overleaf Git repository.

    First call: clones into a persistent temp directory.
    Subsequent calls: returns the cached repo immediately.

    Parameters
    ----------
    pull : bool
        If True, run 'git pull' to fetch latest changes (used before writes).
        If False (default), return the cached repo without network access.
    """
    global _cached_repo

    if not OVERLEAF_GIT_URL or not OVERLEAF_TOKEN:
        raise RuntimeError(
            "Missing Overleaf configuration. Set OVERLEAF_GIT_URL and "
            "OVERLEAF_TOKEN environment variables."
        )

    if not OVERLEAF_GIT_URL.startswith("https://"):
        raise RuntimeError("OVERLEAF_GIT_URL must start with https://")

    with _clone_lock:
        # If we already have a cached clone, return it (optionally pull)
        if _cached_repo is not None and _cached_repo.exists():
            if pull:
                run(["git", "checkout", "."], cwd=_cached_repo)
                run(["git", "pull", "--ff-only"], cwd=_cached_repo)
            return _cached_repo

        # First call — clone into a persistent temp directory
        tmpdir = tempfile.mkdtemp(prefix="overleaf_mcp_")
        repo_dir = Path(tmpdir) / "project"

        auth_url = _build_auth_url()
        run(["git", "clone", auth_url, str(repo_dir)])

        _cached_repo = repo_dir
        return repo_dir
