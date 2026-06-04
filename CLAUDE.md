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

- **One runtime dep**: `colorama` (cross-platform color; handles legacy Windows
  consoles). Everything else is stdlib. Dev deps: `pytest`, `ruff`, `mypy`.
- **Path capture trick**: only `fav.bat` is "capture" style (`for /f` + `pushd`).
  `fav-add.bat` / `fav-del.bat` are plain wrappers. Python diagnostics go to
  **stderr**; only the chosen path goes to stdout.
- **Atomic file writes**: `tempfile.mkstemp` + `os.replace` in
  `io_utils.atomic_write_text`, shared by `FavoritesRepository` and `UsageStore`,
  to avoid corrupting `.favoritedirs` / its `.usage` sidecar.
- **Path expansion**: only `~` (via `os.path.expanduser`). No env-var or
  custom placeholder expansion. Unresolvable paths fail loudly at `pushd` time.
- **Filter scope**: name **and** raw path, case-insensitive substring; multi-token
  = AND. Tab joiner prevents a token straddling the name/path boundary. The
  searchable field list is owned by `Favorite.searchable_fields()`.
- **Frecency**: `fav` / `fav-del` sort matches by usage frecency (count × recency
  weight) before showing the menu; the top result is highlighted. Counts live in
  a JSON sidecar `<favorites_path>.usage` keyed by `"name|raw_path"`. `fav`
  records a pick; `fav-del` prunes the deleted entry. Missing/corrupt sidecar →
  treated as empty (unsorted fall back to file order). Recency buckets live in
  `constants.RECENCY_WEIGHTS`.
- **Color**: emitted only to stderr menus when stderr is a TTY. `NO_COLOR`
  disables; `FAV_COLOR` (truthy/falsy) forces. Logic in `ui/colors.py`.

## Module map

```
app/
├── constants.py             # FIELD_SEPARATOR, env vars, file names, RECENCY_WEIGHTS
├── io_utils.py              # atomic_write_text(path, body)
├── config/settings.py       # Settings.from_env() — favorites_path, usage_path, log_level
├── logging_setup.py         # configure_logging → stderr
├── favorites/
│   ├── entry.py             # Favorite dataclass, validate_name, InvalidFavoriteError
│   ├── repository.py        # FavoritesRepository (load/save/append/remove_at)
│   ├── usage.py             # UsageStore (frecency sidecar: score/sort/record/remove)
│   ├── filter.py            # match(favs, query)
│   └── path_resolver.py     # resolve(raw), collapse_home(path)
├── ui/
│   ├── menu.py              # print_menu, prompt_index, auto_pick_or_prompt
│   └── colors.py            # should_color, highlight, dim, init_color
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

## Code Analysis

After implementing new features or making significant changes, run the code analysis:

```bash
powershell -Command "cd 'D:\GIT\BenjaminKobjolke\cli-favorites'; cmd /c '.\tools\analyze_code.bat'"
```

Auto-fix what Ruff can (`tools\fix_ruff_issues.bat`; preview with
`tools\fix_ruff_issues_dry_run.bat`). Rules in `code_analysis_rules.json`.
Local analyzer path lives in `tools\analyze_code_config.bat` (gitignored; copy
from `analyze_code_config.example.bat`). Fix any reported issues before committing.

## When adding features

- Keep modules under 300 lines; split by responsibility.
- Add unit tests **before** implementation (TDD).
- New CLI commands: add a thin `app/cli/<name>.py`, register a console script
  in `pyproject.toml`, add a bat wrapper, register it in `install_global.BAT_FILES`.
- New string constants → `app/constants.py`. Never inline `"|"` or
  `".favoritedirs"` literals elsewhere.

## Coding rules (synced from coding-rules/)

Source of truth lives in the external files below; this is the applicable
subset, embedded so it is enforced here. Keep this section in sync when the
source files change.

### Common rules (apply)

- **TDD**: write tests first, watch them fail, implement, watch them pass. For
  refactors, pin current behavior with a characterization test first.
- **Integration tests** in addition to unit tests; both have runner bats
  (`tools\run_tests.bat`, `tools\run_integration_tests.bat`).
- **DRY**: extract shared logic (e.g. `io_utils.atomic_write_text`); constants
  for repeated values.
- **String constants** centralized in `app/constants.py` — never scatter raw
  strings (`"|"`, `".favoritedirs"`, env-var names).
- **Type-safe values**: typed objects/enums over stringly-typed data. No
  bag-of-keys dict/array returns across module boundaries — return a dataclass
  (e.g. `Favorite`, `Settings`). Reuse existing models before inventing shapes.
- **Centralized logging**: structured `logging` (never `print`); levels
  debug/info/warning/error with context. UI prompts via `sys.stderr.write`.
- **Input validation at boundaries**: validate external/user/file data, fail
  fast with clear errors (e.g. `validate_name`, `Favorite.from_line`).
- **Max file length 300 lines**; split by responsibility. **No god classes**
  (>5 public methods / >4 ctor deps / mixed domains → split).
- **Naming**: files `snake_case`, classes `PascalCase`, functions/vars
  `snake_case`, constants `UPPER_SNAKE_CASE`.
- **Security baseline**: never commit secrets; keep deps updated; validate
  input at boundaries.
- **Confirm dependency versions** with the user before adding a package.
- **README.md mandatory** (name, setup, usage, deps).
- **Self-describing classes**: behavior over fields (search/serialize/display)
  declared via the class (Protocol/ABC or dataclass field metadata), not
  hardcoded field lists in consumers.
- **Reusable tooling**: before building project infra scripts, check the
  language's `*_setup_files/` folder for an existing equivalent.

### Python rules (apply)

- **`pyproject.toml` is the single source of truth**; commit `uv.lock`; pin
  Python (`>=3.11,<3.13`); manage deps via `uv add`.
- **Enforce ruff + mypy**: `ruff check`, `ruff format --check`, `mypy` (strict).
- **Type hints on all public APIs** (params + returns); use `typing` well;
  avoid `Any` except at I/O / third-party boundaries.
- **Env-driven settings** centralized in `app/config/settings.py`
  (`Settings.from_env()`) — no scattered `os.getenv` or magic values.
- **Tests fast + isolated**: pytest, no network in unit tests, `tmp_path`
  fixtures, no reliance on machine state.
- **`MagicMock(spec=RealClass)`** when mocking, so interface mismatches raise.
- **Required bats present**: `start.bat`, `install.bat`, `update.bat`,
  `tools\run_tests.bat`.
- **Structured logging** via the `logging` module, centralized in
  `logging_setup.py`.

## External rules referenced

- `D:\GIT\BenjaminKobjolke\claude-code\coding-rules\COMMON_RULES.md`
- `D:\GIT\BenjaminKobjolke\claude-code\coding-rules\PYTHON_RULES.md`

Rules deliberately skipped because they don't apply: Jinja2 / Jinja2 integration
(no HTML), python-localization + translation-key conventions (English-only CLI;
tiny string surface), SQLAlchemy (no DB), Pydantic validation (file format is
trivial; custom parser is clearer), asyncio (no I/O concurrency).
