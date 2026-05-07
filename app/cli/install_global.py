"""Install the cli-favorites bat wrappers into a PATH-listed directory."""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from app.cli._common import EXIT_FAILURE, EXIT_OK, EXIT_USAGE
from app.config.settings import Settings
from app.constants import LOG_NAME
from app.logging_setup import configure_logging

DEFAULT_TARGET = Path(r"C:\cmdtools")
PROJECT_ROOT = Path(__file__).resolve().parents[2]

log = logging.getLogger(LOG_NAME)


@dataclass(frozen=True)
class BatSpec:
    filename: str
    module: str
    capture_path: bool


BAT_FILES: tuple[BatSpec, ...] = (
    BatSpec("fav.bat", "app.cli.fav", capture_path=True),
    BatSpec("fav-add.bat", "app.cli.fav_add", capture_path=False),
    BatSpec("fav-del.bat", "app.cli.fav_del", capture_path=False),
)


class InstallError(Exception):
    """Raised when bat installation fails for a domain reason."""


def render_capture_bat(project_root: Path, module: str) -> str:
    """Wrapper that hands off the chosen path via a temp file, then cd's into it."""
    root_str = str(project_root).replace("/", "\\")
    return (
        "@echo off\r\n"
        "setlocal\r\n"
        f'set "PROJECT_ROOT={root_str}\\"\r\n'
        'set "PYTHONPATH=%PROJECT_ROOT%"\r\n'
        'set "FAV_TARGET_FILE=%TEMP%\\fav_target_%RANDOM%_%RANDOM%.txt"\r\n'
        'if exist "%FAV_TARGET_FILE%" del /q "%FAV_TARGET_FILE%"\r\n'
        f'"%PROJECT_ROOT%.venv\\Scripts\\python.exe" -m {module} %*\r\n'
        'set "TARGET="\r\n'
        'if exist "%FAV_TARGET_FILE%" (\r\n'
        '    set /p TARGET=<"%FAV_TARGET_FILE%"\r\n'
        '    del /q "%FAV_TARGET_FILE%"\r\n'
        ")\r\n"
        'endlocal & if not "%TARGET%"=="" cd /d "%TARGET%"\r\n'
    )


def render_plain_bat(project_root: Path, module: str) -> str:
    """Wrapper that runs the python entry point and exits with its code."""
    root_str = str(project_root).replace("/", "\\")
    return (
        "@echo off\r\n"
        "setlocal\r\n"
        f'set "PROJECT_ROOT={root_str}\\"\r\n'
        'set "PYTHONPATH=%PROJECT_ROOT%"\r\n'
        f'"%PROJECT_ROOT%.venv\\Scripts\\python.exe" -m {module} %*\r\n'
        "exit /b %ERRORLEVEL%\r\n"
    )


def render_bat(project_root: Path, spec: BatSpec) -> str:
    if spec.capture_path:
        return render_capture_bat(project_root, spec.module)
    return render_plain_bat(project_root, spec.module)


def install_bats(project_root: Path, target_dir: Path, overwrite: bool) -> list[Path]:
    if not target_dir.exists():
        raise InstallError(f"target directory does not exist: {target_dir}")
    if not target_dir.is_dir():
        raise InstallError(f"target is not a directory: {target_dir}")

    if not overwrite:
        existing = [
            target_dir / spec.filename
            for spec in BAT_FILES
            if (target_dir / spec.filename).exists()
        ]
        if existing:
            joined = ", ".join(p.name for p in existing)
            raise InstallError(f"these files already exist in {target_dir}: {joined}")

    written: list[Path] = []
    for spec in BAT_FILES:
        path = target_dir / spec.filename
        path.write_text(render_bat(project_root, spec), encoding="utf-8", newline="")
        written.append(path)
    return written


def _read_target_from_stdin() -> Path:
    sys.stderr.write(f"Install target directory [{DEFAULT_TARGET}]: ")
    sys.stderr.flush()
    raw = sys.stdin.readline().strip()
    return Path(raw) if raw else DEFAULT_TARGET


def _confirm_overwrite(existing_names: list[str]) -> bool:
    sys.stderr.write("These files already exist:\n")
    for name in existing_names:
        sys.stderr.write(f"  - {name}\n")
    sys.stderr.write("Overwrite? [y/N]: ")
    sys.stderr.flush()
    answer = sys.stdin.readline().strip().lower()
    return answer == "y"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="fav-install-global",
        description="Install fav.bat / fav-add.bat / fav-del.bat into a directory on your PATH.",
    )
    parser.add_argument(
        "target",
        type=Path,
        nargs="?",
        help="Target directory. If omitted, you will be prompted.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files without prompting.",
    )
    return parser.parse_args(argv)


def main() -> int:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    try:
        args = _parse_args(sys.argv[1:])
    except SystemExit as err:
        return int(err.code) if isinstance(err.code, int) else EXIT_USAGE

    target: Path = args.target if args.target is not None else _read_target_from_stdin()

    try:
        written = install_bats(PROJECT_ROOT, target, overwrite=args.force)
    except InstallError as err:
        if "already exist" in str(err) and not args.force:
            existing = [spec.filename for spec in BAT_FILES if (target / spec.filename).exists()]
            if not _confirm_overwrite(existing):
                log.error("aborted; nothing installed")
                return EXIT_FAILURE
            try:
                written = install_bats(PROJECT_ROOT, target, overwrite=True)
            except InstallError as err2:
                log.error("%s", err2)
                return EXIT_FAILURE
        else:
            log.error("%s", err)
            return EXIT_FAILURE

    sys.stderr.write(f"Installed {len(written)} bat wrapper(s) in {target}:\n")
    for path in written:
        sys.stderr.write(f"  - {path.name}\n")
    sys.stderr.write(f"Project root referenced by the wrappers: {PROJECT_ROOT}\n")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
