# cli-favorites

Tiny Windows CLI to navigate to favorite directories listed in a flat file.

Reads `%USERPROFILE%\.favoritedirs` (one entry per line, format `Name|Path`)
and lets you `pushd` into a chosen entry from any shell.

## Commands

| Command                | What it does                                               |
| ---------------------- | ---------------------------------------------------------- |
| `fav <token>...`       | Filter favorites by all tokens (AND, case-insensitive substring); auto-pick if 1 match, else menu; `pushd` to selection. |
| `fav --scope {name,path,both}` | Restrict the filter to the favorite name, its path, or both (default). |
| `fav --set-limit N`    | Persist the max number of results shown in menus and the FCC palette (default 10). |
| `fav-name <token>...`  | Same as `fav`, but filters the name only (shortcut for `fav --scope name`). |
| `fav-dir <token>...`   | Same as `fav`, but filters the path only (shortcut for `fav --scope path`). |
| `fav-add`              | Append the current directory as a new favorite (prompts for name). |
| `fav-del [token]...`   | Filter, pick, delete the chosen entry (asks `[y/N]` first). No tokens: offers to delete the current directory if it's a favorite, else lists all. `-y/--yes` skips confirmation. `--scope` works the same as on `fav`. |
| `fav-install-global`   | Copy the bat wrappers above (plus the `.ps1` wrappers for PowerShell) into a directory on your PATH (default `C:\cmdtools`). |

The filter is a case-insensitive substring match against the favorite name **and**
its path. Multiple tokens are AND-ed (`fav erp api` → entries whose name+path
contains both "erp" AND "api"). Pass no tokens to see every entry. Add
`--scope name` or `--scope path` (or use `fav-name` / `fav-dir`) to search only
one field.

Menus and palette suggestions show at most **10** results (frecency-sorted, so
the best matches survive the cut). Change the cap persistently with
`fav --set-limit N`; narrow with more filter tokens to reach hidden entries.

## Favorites file format

`%USERPROFILE%\.favoritedirs`, plain UTF-8 text:

```
fman Data|~/AppData/Roaming/fman
FMAN User Home|~/.fman
Downloads|~/Downloads
Project|D:\GIT\some\project
UNC Share|\\server\share
```

- `~` expands to your home directory. No other placeholders.
- The first `|` on a line is the separator; subsequent `|` characters belong to the path.
- Blank lines and malformed lines are skipped with a warning.

## Installation

Requires [`uv`](https://docs.astral.sh/uv/).

```bat
install.bat
```

Runs `uv sync` and the unit tests. After that:

- `fav.bat`, `fav-add.bat`, `fav-del.bat`, `fav-set-limit.bat`, `fav-name.bat`,
  `fav-dir.bat` work from cmd.exe.
- Run `fav-install-global.bat` to copy them into a directory on your PATH so
  they work from anywhere. Default target is `C:\cmdtools`. It also writes
  `fav.ps1`, `fav-name.ps1` and `fav-dir.ps1` there - see below.

## Usage examples

```bat
:: From cmd.exe, after fav-install-global to a PATH dir:

fav fman                     :: shows menu of all "fman" matches, picks one, cd's
fav erp api                  :: AND filter — both tokens must match
fav downloads                :: auto-picks single match, cd's to ~/Downloads
fav                          :: lists every favorite
fav --scope name erp         :: name-only filter (same as: fav-name erp)
fav-name erp                 :: shortcut for fav --scope name
fav-dir api                  :: shortcut for fav --scope path

cd D:\some\new\project
fav-add                      :: prompts for a name, appends entry

fav-del fman                 :: filter+pick+confirm+remove from the file
fav-del                      :: cwd is a favorite? offers to delete it, else lists all
fav-del fman --yes           :: skip the [y/N] confirmation

fav --set-limit 20           :: show up to 20 results from now on (default 10)
```

In the selection menu (shown for `fav` / `fav-del` when more than one entry
matches), navigate with **Up/Down** arrows and confirm with **Enter** — Enter on
the highlighted top (most-frecent) result picks it. You can also type a number,
and **Esc** or **q** cancels. When input is piped (not an interactive console)
the menu falls back to a plain numbered prompt.

`fav.bat` uses `cd /d`. The chosen path is handed off via a temp file
(`%TEMP%\fav_target_*.txt`) which the wrapper deletes after reading.

## PowerShell

A `.bat` can only change the directory of the process that interprets it. cmd.exe
runs the bat in-process, so `cd /d` sticks; PowerShell spawns a child `cmd.exe`,
so the `cd` dies with that child and the prompt never moves.

`fav-install-global` therefore also installs `fav.ps1`, `fav-name.ps1` and
`fav-dir.ps1` - the three commands that change directory. They use the same
`FAV_TARGET_FILE` handoff (nothing is redirected, so the arrow-key menu keeps its
console) and end in `Set-Location`, which handles UNC paths that `cd /d` cannot.

PowerShell prefers `.ps1` over `.bat` when both sit in the same PATH directory,
so `fav` resolves per shell with no profile changes. Check with `Get-Command fav`.

`fav-add`, `fav-del` and `fav-set-limit` never change directory, so they stay
bat-only and work from either shell.

## Configuration

Environment variables:

- `FAV_FILE` — path to favorites file (default `%USERPROFILE%\.favoritedirs`).
- `FAV_LOG_LEVEL` — `DEBUG`, `INFO` (default), `WARNING`, `ERROR`.
- `FAV_TARGET_FILE` — set by `fav.bat` to receive the chosen path. If unset,
  Python prints the path on stdout instead.

Persistent preferences live in a JSON sidecar `<favorites>.config` (e.g.
`%USERPROFILE%\.favoritedirs.config`), currently just `max_results` — set it
via `fav --set-limit N`. A missing or corrupt file falls back to the default
of 10.

## FastCommandCenter integration

The repo doubles as an FCC external tool (`fasttool.json`): a "Favorite
Folders" text provider — type in the palette to filter favorites, pick one
and FCC copies the resolved path to the clipboard and pastes it into the
previously focused window.

Setup:

1. Build the palette host exe: `tools\build.bat` → `dist\FavPalette.exe`.
2. In FCC's palette: `Tools: manage folders` → add this repo's folder, then
   reopen the palette — "Favorite Folders" appears. Optionally bind a global
   hotkey to it via `Configure keyboard shortcuts`.

FCC launches `FavPalette.exe --palette` on demand (`app/palette_host.py`,
using the `fasttool_palette` shim from `FastCommandCenter-tool-bridge`). The
favorites file is reloaded on every query, so `fav-add`/`fav-del` edits show
immediately. FCC echoes each pick back to the tool (the v3 `selected`
message), so selections made through FCC bump the same frecency counts as
normal CLI use.

## Development

```bat
tools\run_tests.bat                 :: unit tests
tools\run_integration_tests.bat     :: subprocess-driven CLI tests
update.bat                          :: lock + sync + ruff + mypy + tests
```

Project layout follows the rules in
`D:\GIT\BenjaminKobjolke\claude-code\coding-rules\` (`COMMON_RULES.md`, `PYTHON_RULES.md`).
