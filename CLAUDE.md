# CLAUDE.md — cli-favorites

Project-specific guidance for Claude. Common and Python rules are linked at the
end; this file captures only what is unique to this project.

## What this project is

Tiny Windows CLI that reads `%USERPROFILE%\.favoritedirs` and lets the user
`pushd` to a chosen entry. Three commands plus an installer:

- `fav <filter>` — filter, auto-pick if single match, otherwise menu, print
  resolved path on **stdout**. The bat wrapper captures stdout and `pushd`'s.
- `fav-add` — append CWD as new entry, prompts for name (or `--name`).
- `fav-del <filter>` — filter, pick, remove entry.
- `fav-install-global` — write the three bats into a PATH directory (default `C:\cmdtools`).

## Architectural choices

- **stdlib only** at runtime. Dev deps: `pytest`, `ruff`, `mypy`.
- **Path capture trick**: only `fav.bat` is "capture" style (`for /f` + `pushd`).
  `fav-add.bat` / `fav-del.bat` are plain wrappers. Python diagnostics go to
  **stderr**; only the chosen path goes to stdout.
- **Atomic file writes**: `tempfile.mkstemp` + `os.replace` in
  `FavoritesRepository._atomic_write` to avoid corrupting `.favoritedirs`.
- **Path expansion**: only `~` (via `os.path.expanduser`). No env-var or
  custom placeholder expansion. Unresolvable paths fail loudly at `pushd` time.
- **Filter scope**: name only, case-insensitive substring. Paths are not searched.

## Module map

```
app/
├── constants.py             # FIELD_SEPARATOR, env var names, file name
├── config/settings.py       # Settings.from_env() — favorites_path, log_level
├── logging_setup.py         # configure_logging → stderr
├── favorites/
│   ├── entry.py             # Favorite dataclass, validate_name, InvalidFavoriteError
│   ├── repository.py        # FavoritesRepository (load/save/append/remove_at)
│   ├── filter.py            # match(favs, query)
│   └── path_resolver.py     # resolve(raw), collapse_home(path)
├── ui/menu.py               # print_menu, prompt_index, auto_pick_or_prompt
└── cli/
    ├── _common.py           # exit codes, bootstrap()
    ├── fav.py               # main: filter → menu → print stdout
    ├── fav_add.py           # main: prompt name, append
    ├── fav_del.py           # main: filter → menu → remove
    └── install_global.py    # render+write bat wrappers
```

## Conventions specific to this project

- All UI output (menu, prompts, confirmations, errors) → **stderr** (via
  `logging` for diagnostics, direct `sys.stderr.write` for prompts).
- Never write to **stdout** except the final resolved path in `fav.py`.
- When constructing favorite paths to write to file, call
  `path_resolver.collapse_home(...)` so portable `~`-form is preferred.
- Exit codes: 0 ok, 1 failure, 2 usage error.

## Testing

- Unit tests in `tests/`, integration in `tests/integration/`.
- Integration tests spawn `python -m app.cli.<x>` via `subprocess` and use a
  per-test `.favoritedirs` via the `FAV_FILE` env var.
- `tools\run_tests.bat` runs unit only (excludes `tests/integration`).
- `tools\run_integration_tests.bat` runs the integration suite.

## Build / dev commands

```bat
install.bat                                  :: uv sync + unit tests
tools\run_tests.bat
tools\run_integration_tests.bat
update.bat                                   :: lock --upgrade + sync + ruff + mypy + tests
```

## When adding features

- Keep modules under 300 lines; split by responsibility.
- Add unit tests **before** implementation (TDD).
- New CLI commands: add a thin `app/cli/<name>.py`, register a console script
  in `pyproject.toml`, add a bat wrapper, register it in `install_global.BAT_FILES`.
- New string constants → `app/constants.py`. Never inline `"|"` or
  `".favoritedirs"` literals elsewhere.

## External rules referenced

- `D:\GIT\BenjaminKobjolke\claude-code\coding-rules\COMMON_RULES.md`
- `D:\GIT\BenjaminKobjolke\claude-code\coding-rules\PYTHON_RULES.md`

Rules deliberately skipped because they don't apply: Jinja2 (no HTML),
python-localization (English-only CLI; tiny string surface), SQLAlchemy
(no DB), Pydantic (file format is trivial; custom parser is clearer),
asyncio (no I/O concurrency).
