"""Download and safely apply the latest application files from GitHub."""

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Callable, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

GITHUB_ARCHIVE_URL = "https://api.github.com/repos/Soullessrage/Clicker_and_Mouse/zipball/main"
MAX_ARCHIVE_SIZE = 64 * 1024 * 1024
ROOT_FILES = {
    "README.md",
    "requirements.txt",
    "Run_Clicker",
    "Run_Clicker.bat",
    "Run_Clicker.command",
    "run_mouse_controller",
}


class GitHubUpdater:
    """Fetch and install repository files without modifying the local venv."""

    def __init__(self, install_root: Path, on_status: Callable[[str], None]):
        self.install_root = install_root.resolve()
        self.on_status = on_status

    def update(self) -> None:
        """Download, validate, stage, and replace the latest allowlisted files."""
        self.on_status("Contacting GitHub...")
        token = self._github_token()
        if not token:
            raise RuntimeError(
                "This GitHub repository is private. Install GitHub CLI and sign in with `gh auth login`, "
                "or set NEON_MOUSE_CONTROLLER_GITHUB_TOKEN to a fine-grained token with read-only Contents access."
            )
        request = Request(
            GITHUB_ARCHIVE_URL,
            headers={
                "User-Agent": "Neon-Mouse-Controller-Updater",
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )
        try:
            with urlopen(request, timeout=45) as response:
                archive_data = response.read(MAX_ARCHIVE_SIZE + 1)
        except HTTPError as error:
            if error.code in (401, 403, 404):
                raise RuntimeError(
                    f"GitHub denied the update (HTTP {error.code}). Confirm the token can read "
                    "the private repository's Contents and main branch."
                ) from error
            raise RuntimeError(f"Could not download the update: HTTP {error.code}") from error
        except (OSError, URLError) as error:
            raise RuntimeError(f"Could not download the update: {error}") from error
        if len(archive_data) > MAX_ARCHIVE_SIZE:
            raise RuntimeError("The GitHub source archive exceeded the 64 MB safety limit.")

        with tempfile.TemporaryDirectory(prefix=".neon-update-", dir=self.install_root) as temp_name:
            temp_root = Path(temp_name)
            archive_path = temp_root / "github-main.zip"
            staged_root = temp_root / "staged"
            backup_root = temp_root / "backups"
            staged_root.mkdir()
            backup_root.mkdir()
            archive_path.write_bytes(archive_data)
            self.on_status("Checking downloaded files...")
            staged_files = self._stage_archive(archive_path, staged_root)
            if not staged_files or not (staged_root / "mouse_controller" / "main.py").is_file():
                raise RuntimeError("The downloaded archive did not contain a valid application update.")

            requirements = staged_root / "requirements.txt"
            if requirements.is_file():
                self._install_dependencies(requirements)

            self.on_status("Installing application update...")
            self._replace_files(staged_files, staged_root, backup_root)
            self._clear_bytecode_cache()

    def _stage_archive(self, archive_path: Path, staged_root: Path) -> List[Path]:
        staged_files = []
        seen_paths = set()
        try:
            with zipfile.ZipFile(archive_path) as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    archive_path_parts = PurePosixPath(member.filename).parts
                    if len(archive_path_parts) < 2 or "\\" in member.filename:
                        continue
                    relative = PurePosixPath(*archive_path_parts[1:])
                    if relative.is_absolute() or any(part in (".", "..") for part in relative.parts):
                        continue
                    if not self._is_updatable(relative):
                        continue
                    if relative in seen_paths:
                        raise RuntimeError(f"The archive contains a duplicate file: {relative}")
                    seen_paths.add(relative)
                    target = staged_root.joinpath(*relative.parts)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(member) as source, target.open("wb") as destination:
                        shutil.copyfileobj(source, destination)
                    file_mode = member.external_attr >> 16
                    if file_mode:
                        target.chmod(file_mode & 0o777)
                    staged_files.append(target)
        except zipfile.BadZipFile as error:
            raise RuntimeError("GitHub returned an invalid ZIP archive.") from error
        return staged_files

    @staticmethod
    def _is_updatable(relative: PurePosixPath) -> bool:
        if len(relative.parts) == 1:
            return relative.name in ROOT_FILES
        return (
            len(relative.parts) == 2
            and relative.parts[0] == "mouse_controller"
            and relative.suffix == ".py"
        )

    @staticmethod
    def _github_token() -> Optional[str]:
        for variable in (
            "NEON_MOUSE_CONTROLLER_GITHUB_TOKEN",
            "GH_TOKEN",
            "GITHUB_TOKEN",
        ):
            token = os.environ.get(variable, "").strip()
            if token:
                return token

        github_cli = shutil.which("gh")
        if github_cli is None:
            return None
        try:
            result = subprocess.run(
                [github_cli, "auth", "token"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if result.returncode == 0:
            return result.stdout.strip() or None
        return None

    @staticmethod
    def _install_dependencies(requirements: Path) -> None:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements)],
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RuntimeError(f"Could not prepare updated dependencies: {error}") from error
        if result.returncode != 0:
            details = (result.stderr or result.stdout).strip()[-1200:]
            raise RuntimeError(f"Dependency installation failed. {details}")

    def _replace_files(self, staged_files: List[Path], staged_root: Path, backup_root: Path) -> None:
        replaced: List[Tuple[Path, Optional[Path]]] = []
        try:
            for staged_file in staged_files:
                relative = staged_file.relative_to(staged_root)
                target = self.install_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                backup = None
                if target.exists():
                    backup = backup_root / relative
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, backup)
                os.replace(staged_file, target)
                replaced.append((target, backup))
        except OSError as error:
            for target, backup in reversed(replaced):
                if backup is None:
                    target.unlink(missing_ok=True)
                else:
                    os.replace(backup, target)
            raise RuntimeError(f"Could not install the update; the previous files were restored: {error}") from error

    def _clear_bytecode_cache(self) -> None:
        cache_directory = self.install_root / "mouse_controller" / "__pycache__"
        if not cache_directory.is_dir():
            return
        for bytecode_file in cache_directory.glob("*.pyc"):
            bytecode_file.unlink(missing_ok=True)