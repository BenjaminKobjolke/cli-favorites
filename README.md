# cli-favorites

Tiny Windows CLI to navigate to favorite directories listed in a flat file.

Reads `%USERPROFILE%\.favoritedirs` (one entry per line, format `Name|Path`)
and lets you `pushd` into a chosen entry from any shell.

## Commands

| Command                | What it does                                               |
| ---------------------- | ---------------------------------------------------------- |
| `fav <token>...`       | Filter favorites by all tokens (AND, case-insensitive substring); auto-pick if 1 match, else menu; `pushd` to selection. |
| `fav-add`              | Append the current directory as a new favorite (prompts for name). |
| `fav-del <token>...`   | Filter, pick, delete the chosen entry from the file.       |
| `fav-install-global`   | Copy the three bats above into a directory on your PATH (default `C:\cmdtools`). |

The filter is a case-insensitive substring match against the favorite name **and**
its path. Multiple tokens are AND-ed (`fav erp api` → entries whose name+path
contains both "erp" AND "api"). Pass no tokens to see every entry.

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

- `fav.bat`, `fav-add.bat`, `fav-del.bat` work from cmd.exe.
- Run `fav-install-global.bat` to copy them into a directory on your PATH so
  they work from anywhere. Default target is `C:\cmdtools`.

## Usage examples

```bat
:: From cmd.exe, after fav-install-global to a PATH dir:

fav fman                     :: shows menu of all "fman" matches, picks one, cd's
fav erp api                  :: AND filter — both tokens must match
fav downloads                :: auto-picks single match, cd's to ~/Downloads
fav                          :: lists every favorite

cd D:\some\new\project
fav-add                      :: prompts for a name, appends entry

fav-del fman                 :: filter+pick+remove from the file
```

`fav.bat` uses `cd /d`. The chosen path is handed off via a temp file
(`%TEMP%\fav_target_*.txt`) which the wrapper deletes after reading.

## Configuration

Environment variables:

- `FAV_FILE` — path to favorites file (default `%USERPROFILE%\.favoritedirs`).
- `FAV_LOG_LEVEL` — `DEBUG`, `INFO` (default), `WARNING`, `ERROR`.
- `FAV_TARGET_FILE` — set by `fav.bat` to receive the chosen path. If unset,
  Python prints the path on stdout instead.

## Development

```bat
tools\run_tests.bat                 :: unit tests
tools\run_integration_tests.bat     :: subprocess-driven CLI tests
update.bat                          :: lock + sync + ruff + mypy + tests
```

Project layout follows the rules in
`D:\GIT\BenjaminKobjolke\claude-code\coding-rules\` (`COMMON_RULES.md`, `PYTHON_RULES.md`).
