# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

DeCode IDE — an early-stage, modal (Vim-like) desktop code editor built with PyQt6. The long-term direction (per `embedded/`) is an IDE aimed at embedded/PlatformIO development; the running side of that (`:pio build|upload|monitor|clean|env|init`) landed in Sprint 10 (`init` in Sprint 11), while the serial monitor is still a stub. Comments, docstrings, commit messages and the `docs/` package in this repo are written in Turkish; match that convention when editing existing files.

Planning lives in `docs/`: [`docs/Roadmap.md`](docs/Roadmap.md) holds the phase plan and the technical-debt table, `docs/sprint/` the per-sprint log (`README.md` lists them and says which sprint is active).

## Running

```bash
python3 main.py
```

Runtime dependencies are in `requirements.txt` (`PyQt6`, `pyte` — the terminal panel's screen buffer). `main.py` forces `QT_QPA_PLATFORM=wayland;xcb` before creating the `QApplication`, so it works on both Wayland and X11.

## Testing

```bash
.venv/bin/python -m pytest -q          # tüm testler
.venv/bin/python -m pytest tests/test_fuzzy.py -q
```

`tests/conftest.py` sets `QT_QPA_PLATFORM=offscreen` before Qt is imported and exposes two fixtures: a session-scoped `qapp`, and a function-scoped `pencere` — an `IDEWindow(settings=config.default_settings())` that shuts down its terminal PTY and deletes itself on teardown. This is why tests run headless (SSH, CI) *and* never depend on whatever happens to be in the developer's real `~/.config/decode/config.toml` (see "Settings" below). Dev dependencies: `requirements-dev.txt`. Config: `pytest.ini` (`pythonpath = .`, `testpaths = tests`).

Note: this repo's `.venv` was created at an older path, so the `pip`/`pytest` *console scripts* have a stale shebang — call them as `.venv/bin/python -m pip` / `-m pytest`. There is no linter or build step configured.

## Architecture

The app follows a simple, signal-driven layering:

- **`main.py`** — entry point; creates `QApplication` and the top-level `IDEWindow`.
- **`ui/main_window.py` (`IDEWindow`)** — the composition root. Its `modal_host` property is "whoever currently hosts the command line" — the active editor, or the welcome page when there are no tabs; mode and suggestion checks go through it, `self.editor` stays for genuinely editor-only work (save, symbols, cursor position) and can be `None`. Builds a `QSplitter` with `Sidebar` on the left and, on the right, a vertical stack of `EditorTabs` above `TerminalPanel`. Wires up all cross-component signals, owns file open/save via `core/file_manager.py`, positions the floating command line / suggestions / palette, and applies the Tokyo Night–inspired stylesheet. `apply_settings()` distributes `self.settings` everywhere (palette, QSS, editors, terminal) and is what both startup and `:reload` call — see "Settings" below for the `settings=` contract.
- **`ui/theme.py`** — the single source of color: a module-level `DEFAULT_PALETTE` (17 named Tokyo Night tokens) and `_current`, the live palette every component reads at paint time via `theme.color(token)` — so a palette swap reaches everything that repaints without threading it through five constructors. `set_palette`/`build_palette` are the only way to change it; it's genuinely global (no per-window theme). `stylesheet()` builds the app's QSS from it. `tests/test_no_hardcoded_colors.py` recursively greps `ui/`/`core/` for stray `#rrggbb` literals outside this file *and* `core/config.py` (its commented template naturally contains hex too — that's the full exempt set, not just this file), so new color code has nowhere else to hide one.
- **`ui/components/editor_tabs.py` (`EditorTabs`)** — a `QTabWidget` where each tab owns its own `ModalEditor` (its own mode, cursor and state machine). Re-opening an already-open file switches to that tab; an empty untitled tab is reused. Unsaved changes show as `●` in the tab title. Signals from the *active* tab are relayed outward via `_relay`, so `IDEWindow` can talk to "one editor". `tab_count_changed` tells `IDEWindow` to swap between the tab stack and the welcome page.
- **`ui/components/welcome_page.py` (`WelcomePage`)** — what replaces the editor when the last tab is closed; the app deliberately does **not** quit there (`:q` on the last tab lands here, `:qa` still exits). It owns its own `StateMachine`, so the `:` command line keeps working for the commands that need no text buffer — its `available_commands` tuple narrows the suggestion list, and the editor operations `StateMachine` calls (`copy`, `delete_current_line`, `search`, …) are silent stubs. It emits the same signal names as `ModalEditor`, which is what lets `IDEWindow._connect_modal_host` wire both from one table.
- **`ui/components/code_editor.py` (`ModalEditor`)** — a `QPlainTextEdit` subclass that is the heart of the modal input model (see below). Owns a `StateMachine`, a syntax highlighter swapped via `set_highlighter_for_file()`, the line-number gutter, and the in-file search state (`search`, `search_next`, `clear_search`, `goto_line`).
- **`ui/components/sidebar.py` (`Sidebar`)** — a `QTreeView` over `QFileSystemModel`, rooted at the process's CWD (`:cd` re-roots it). Emits `return_focus_requested` on Escape.
- **`ui/components/bottom_panel.py`** — `StatusLine` (always-visible mode/file/position bar), `CommandLine` (the centered `:`-input box, COMMAND mode only), and `CommandSuggestions` (a thin `FloatingList` adapter that formats `(command, description)` pairs).
- **`ui/components/floating_list.py` (`FloatingList`)** — the shared floating box: scrollable, at most `MAX_VISIBLE_ROWS` (8) rows, drop shadow, Tokyo Night scrollbar. Used by both `CommandSuggestions` and `CommandPalette`. Two traps documented in the code: the `QScrollArea` viewport's transparency must be set on the viewport's own stylesheet, and `set_rows` must `invalidate()`/`updateGeometry()` or Qt caches the old size.
- **`ui/components/command_palette.py` (`CommandPalette`)** — the telescope-style picker: a query line plus a `FloatingList` of fuzzy matches. Unlike the command line it **takes focus itself** (the `TerminalView` pattern), so keys land on it, and Escape returns focus to the editor. One widget, three `mode`s: `"file"` (`:ts`), `"symbol"` (`:sym`) and `"env"` (`:pio env`); `IDEWindow._on_palette_accepted` interprets the payload accordingly.
- **`ui/components/terminal_panel.py` / `core/terminal_process.py`** — a real shell over a platform transport, drawn with `pyte`; tabbed, sits *in the layout* below the editor (so the editor really shrinks), ANSI colors mapped to Tokyo Night. Managed with the Alt+Shift shortcut family. `TerminalProcess` also runs a given `argv` (with an optional `cwd`) instead of the login shell and reports the child's exit status on a *separate* `exited(int)` signal — deliberately separate, because `finished` is wired straight to `QWidget.update` and adding an argument would silently break that connection. It clears `_pid` once the child is reaped, so `is_running()` stays honest. `TerminalPanel.run_command(argv, title, cwd)` opens (or reuses) a **command tab**: the tab is labelled `pio build`, then `pio build ✓` / `pio build ✗ (1)` when the process exits; matching for reuse looks at the *undecorated* `command_title`, and a finished tab must not restart itself when the panel is re-shown (`_finished` guard) — for `pio upload` that would write to the board again. The PTY size is fixed at `start()`, which is why `resize()` stores rows/cols even while stopped and `start_now()` measures before starting.
  `TerminalProcess` itself is platform-agnostic: the spawn, the read loop, the
  window size and the kill sequence live behind a *transport* it owns, picked
  at import time (`core/pty_posix.py` on POSIX, `core/pty_windows.py` on
  Windows). Everything shared — the `pyte` screen, the exit-code semantics,
  `child_environment`, `resize` storing the size while stopped — stays in
  `terminal_process.py`, deliberately: splitting it in two is how the two
  platforms drift apart.
- **`ui/components/syntax_highlighter.py` (`CppHighlighter`, `PythonHighlighter`)** — `QSyntaxHighlighter` subclasses with hardcoded regex rules. `CppHighlighter` is the default for anything that isn't a `.py` file. `PythonHighlighter` tracks per-block state for triple-quoted strings.
- **`core/state_machine.py` (`StateMachine`)** — interprets NORMAL-mode bare keys and owns the real `:` command line (see below). Not a generic state machine; it's specific to `ModalEditor`.
- **`core/pty_posix.py` / `core/pty_windows.py`** — the two terminal
  transports, behind one contract (`spawn`, `write`, `set_size`, `is_alive`,
  `exit_code`, `close`, `default_shell_argv`). Two guarantees are part of that
  contract and break *silently* when violated: `on_data`/`on_eof` are **always
  invoked on the main thread** (free on POSIX, where `QSocketNotifier` already
  lives there; on Windows the reader thread's signal is delivered by a queued
  connection) — this is what lets `pyte` and `TerminalPanel` stay
  single-threaded; and `close()` **never blocks the main thread indefinitely**
  on either platform, which is the generalized form of the macOS shutdown
  deadlock (`a039d53`). Windows needs a reader `QThread` at all because
  `QSocketNotifier` there only accepts *socket* descriptors, and ConPTY hands
  you a pipe. Neither module is imported on the other's platform, so
  `pywinpty` never becomes a Linux/macOS dependency. If `pywinpty` is missing,
  `_UnavailableTransport` in `terminal_process.py` keeps the editor running
  and reports 127 — crashing at import is the bug the port exists to fix.
- **`core/keymap.py`** — the single source for key bindings: the ordered `ACTIONS`
  table (name, group, default, description), `parse`/`build`/`defaults`, the
  `Keymap` object (`binding_of`, `action_for`, `label`) and conflict resolution.
  Pure Python, no Qt import. Two groups with deliberately different vocabularies:
  `panel` bindings must carry `ctrl`/`alt`/`meta` (otherwise that letter would
  become untypeable in INSERT mode) and are case-insensitive; `normal` bindings
  are a single character or `escape`, take no modifier prefix, and are
  case-sensitive (`n` ≠ `N`).
- **`ui/keys.py`** — the thin Qt shell that turns a `QKeyEvent` into the binding
  shape `core/keymap.py` produces. Which key *names* are valid is `keymap`'s
  knowledge; only their `Qt.Key` values live here, and
  `tests/test_shortcut_config.py` guards the two tables against drift.
- **`core/config.py`** — reads and validates `~/.config/decode/config.toml` (`load`, `parse`, `default_settings`, `ensure_exists`, `config_path`). Pure Python, no Qt import; doesn't know color *token names*, only that `colors.*` values look like `#rrggbb` (token validity is `ui/theme.build_palette`'s job). Every bad/unknown key becomes a printed warning and that one setting falls back to its default — a malformed file never crashes the app. `bool` is a subclass of `int` in Python, so `font_size = true` would pass a plain `isinstance(value, int)` check; `_validated` checks `bool` first, separately. Only `main.py` calls `ensure_exists` (writes the commented template on first run) — it's the sole home-directory writer in the app.
  The config path is platform-aware: `%APPDATA%\decode\config.toml` on
  Windows, `~/.config/decode/config.toml` elsewhere, with `XDG_CONFIG_HOME`
  winning everywhere. `config_path(platform_name=None, environ=None)` takes
  both as parameters so the Windows branch is testable *on Linux* — the same
  pattern as `main._qt_platform_hint`.
- **`core/fuzzy.py`** — subsequence scoring for the palette (`score`, `rank`). No external dependency; consecutive letters and segment starts (`/`, `_`, `.`) get bonuses. Greedy left-to-right, not optimal alignment.
- **`core/file_index.py`** — `scan_files()` (pure; skips `.git`, `.venv`, `__pycache__`, `node_modules`, hidden entries; caps at 20 000 files) plus `FileIndexWorker(QThread)` so `:ts` never blocks the UI.
- **`core/search.py`** — pure in-file search/replace: `find_next` (wraps around, forward and backward), `find_all` (for highlighting), `replace_all`, `parse_replace_args` (`shlex`, so quoted arguments work).
- **`core/symbols.py`** — `extract_symbols(text, file_path)` → `(kind, name, 1-based line)`. Line-based regex heuristic, not a parser: Python `def`/`class`; C/C++ functions plus `class/struct/enum/namespace`, with control keywords (`if`, `for`, …) filtered out.
- **`core/file_manager.py` (`FileManager`)** — static read/write helpers. `read_file` raises `ValueError` (not `FileNotFoundError`) when the path is missing or is a directory.
- **`embedded/pio_cli.py`** — pure PlatformIO CLI helpers: `find_executable()` (PATH, then `~/.platformio/penv/bin/pio`), the `SUBCOMMANDS` table that is the single source for `:pio ` completion, and `build_argv()`. It builds argv only — starting the process is `IDEWindow`'s job. No `-e` flag is added when no environment is selected, so `platformio.ini`'s `default_envs` keeps the decision.
  `find_executable(platform_name=None)` falls back to
  `~\.platformio\penv\Scripts\pio.exe` on Windows and gates it with
  `os.path.isfile`, not `os.access(X_OK)` — the latter returns True for
  practically every existing file on Windows and would filter nothing.
- **`embedded/pio_project.py`** — pure `platformio.ini` reader: `find_project_root()` walks up for the file, `parse_environments()` returns `{"environments": [...], "default_envs": [...]}`. Uses `ConfigParser(interpolation=None, strict=False)` — interpolation runs at `get()` time, so a `%` in `default_envs` would otherwise raise, and real-world ini files repeat keys. Same contract as `core/config.py`: returns `(data, warnings)`, never prints, never raises.
- **`embedded/serial_reader.py`** — still an empty placeholder (Sprint 12); `:pio monitor` currently runs PlatformIO's own monitor in a command tab.

### Modal editing model

`ModalEditor` has three modes (`self.current_mode`, visualized via cursor width — thick in NORMAL, thin in INSERT):

- In **INSERT**, keystrokes pass straight through to `QPlainTextEdit` except Escape, which returns to NORMAL.
- In **NORMAL**, keystrokes do *not* insert text. Navigation keys and Ctrl-modified keys still pass through to the base widget. The bare keys are `i` (INSERT), `:` (COMMAND), `n` / `N` (next / previous match of the last `:find`) and Escape (clears the search highlight, `:nohlsearch`) — all five are now **configurable** through the `[shortcuts]` section (see "Settings"): `handle_normal_mode` resolves the event to an *action* name via `ui.keys.match(event, self._keymap, "normal")` and calls `StateMachine.handle_normal_action(action)` rather than switching on the raw key. Escape is still resolved by key name, not `event.text()` (which for Escape is **not** empty, `\x1b`), so it never falls through to the printable-key branch. Case is preserved (`event.text()`, not `.lower()`) because `n` and `N` are different commands; a side effect is that Shift+i does not enter INSERT.
- In **COMMAND** (`:`), every key goes to `StateMachine.handle_command_key`. Text accumulates in `self.command_text` and only runs on Enter, like real Vim. Tab/Shift+Tab cycle the suggestion list; Backspace on an empty line exits; Escape cancels.
- `_matches_for(prefix)` builds the suggestion list: a filename/directory completion for `:cd ` (dirs only) and `:openfile ` (dirs + files) via `_path_matches_for(command, path_part, include_files)`, otherwise the known commands whose name starts with the prefix.
- Commands act either directly on the editor (`:d`, `:find`, `:replace`, `:42`) or by emitting a Qt signal that `EditorTabs` relays and `IDEWindow` handles (`:w` → save, `:b` → sidebar focus, `:ts` → telescope, `:openfile` → open path, `:sym` → symbol palette, `:cd`, `:q`/`:wq`/`:qa`/`:wqa`, `:term`/`:termnew`, `:reload` → re-read and re-apply the config file, see "Settings" below, `:pio <subcommand>` → PlatformIO, see below).

Panel shortcuts (every mode, default `Alt+Shift`): `T` moves focus editor ↔
terminal, `N` new tab, `W` close tab, `←`/`→` switch tabs. `ModalEditor`,
`TerminalView` and `WelcomePage` all ask the same question — `ui.keys.match(event,
self._keymap, "panel")` — and map the resulting *action* to their own signal
names, so the command applies to whatever currently has focus. `Alt+Shift+T`
from the editor only does something when the terminal panel is already open
(`TerminalPanel.focus_terminal`), by design. **No Ctrl shortcuts are used by
default** — that is a deliberate project decision, as is entering search via
`:find` rather than a bare `/`; but every binding is user-configurable through
the `[shortcuts]` section (see "Settings").

### Adding a new modal command

Update three places in `core/state_machine.py` together: `KNOWN_COMMANDS`, `COMMAND_DESCRIPTIONS` (this is what the suggestion list shows), and the `match` / `elif` chain in `_execute_command_line`. Then either implement the action as a private `_method` on `StateMachine` (or a public method on `ModalEditor`, for anything touching editor state), or add a new `pyqtSignal` on `ModalEditor`, relay it in `EditorTabs._wire`, and connect it in `IDEWindow._setup_ui`.

Prefer putting real logic in a pure `core/` module (`fuzzy`, `search`, `symbols`, `file_index` are the examples) with unit tests, and keep the Qt layer a thin shell over it.

### PlatformIO

`:pio build|upload|monitor|clean|env|init` (`core/state_machine.py` validates the
subcommand against `pio_cli.SUBCOMMANDS`, then emits `pio_requested(str)`;
`IDEWindow._on_pio_requested` does the work). The flow is: find the project root
by walking up for `platformio.ini` → for `env`, open the telescope palette in
`mode="env"` → otherwise find the `pio` executable → build argv → run it in a
command tab of the terminal panel, with `cwd` set to the project root. Every
failure (no project, no `pio`, unknown subcommand) prints one Turkish line and
opens no tab.

`init` is the odd one out, in three ways. It is the only subcommand that takes
an argument (the board, optional). Its precondition is *inverted* — it must NOT
require an existing `platformio.ini`, since it is the command that creates one,
so `_on_pio_requested` runs it in `os.getcwd()` rather than looking for a
project root; putting the root lookup before it would make the command
unreachable. And `-e` is never appended to it (`pio_cli._ENV_SUBCOMMANDS`),
because `pio project init -e <env>` is meaningless. Firing it also resets
`IDEWindow.pio_env`, since the environment list in the ini is about to change.
The signal stays `pyqtSignal(str)` and carries the whole string
(`"init esp32dev"`) so `EditorTabs._relay` needs no change; validation looks at
the first token only.

The selected environment lives in `IDEWindow.pio_env` and shows in the status
line: bare (`esp32dev`) when the user picked it, in parentheses (`(esp32dev)`)
when it is just `platformio.ini`'s default — in that case argv carries no `-e`
at all. `:cd` resets the selection, since it may be a different project. The
badge is plain text on purpose: anything that copies a color into a stylesheet
has to be re-applied by hand in `apply_settings()` (see `StatusLine.set_mode`).

Jumping from a build error to the code is *not* implemented (Sprint 11). It
cannot scrape the terminal screen: the panel is 9 rows and `pyte.Screen` keeps
no scrollback, so the parser will have to tap the raw bytes at the single
`feed()` point in `TerminalProcess._drain_master`.

### Settings

`~/.config/decode/config.toml` (`core/config.py`) drives `[editor]` (`font_family`, `font_size`, `tab_width`, `expand_tabs`, `line_numbers`), `[terminal]` (`rows`), `[shortcuts]` (any of the 10 action names in `core/keymap.ACTIONS`, each a binding string), and `[colors]` (any of the 17 tokens in `ui/theme.DEFAULT_PALETTE`, each a `#rrggbb` string). When the file is missing, the defaults reproduce today's hardcoded look exactly — the one deliberate exception is tab width, which used to fall back to Qt's 80px default and is now 4 characters. A malformed file never crashes the app: `core/config.parse` turns each bad/unknown key or section into a printed warning and falls back to that one setting's default. `core/config.py` validates only that a `[shortcuts]` value is a non-empty string; which action names and bindings are actually valid is `core/keymap.build`'s job — the same split `[colors]` already has with `ui/theme.build_palette`.

`IDEWindow(settings=None)` would call `config.load()` itself if `settings` were left `None`, but nothing in this codebase actually relies on that fallback: `main.py` resolves settings itself (`config.ensure_exists(path)`, then `config.load(path)`) and always passes the result explicitly, and every test does the same with `config.default_settings()` (the `pencere` fixture in `tests/conftest.py`). That's what keeps *constructing* an `IDEWindow` from touching the developer's real config file during tests. Home-directory writes happen only in `main.py` (`ensure_exists`, on first run); tests instead keep `reload_settings()` off the real file the same way — by monkeypatching `core.config.config_path`, since `:reload` legitimately re-reads the real file on every invocation in the actual running app (that's the point of the command).

`:reload` re-reads the file and calls `IDEWindow.apply_settings()` again (palette, QSS, per-editor settings, terminal rows, keymap) without touching open tabs, cursors, or terminal sessions. One trap: syntax-highlighter and search-highlight colors live in `QTextCharFormat` objects, which copy the color in and do **not** follow a palette swap on their own, so `apply_settings` must explicitly rebuild them afterwards — `editor.refresh_theme()` per open editor (there is no `force=` parameter on `set_highlighter_for_file` any more; that method only ever switches highlighter *class* on file-extension change, `refresh_theme()` is the one mechanism for re-coloring in place, via `highlighter.rebuild()` and `_highlight_matches()`). Dropping the call regresses silently: every other test still passes, code just stops re-coloring on `:reload` (`tests/test_settings_reload.py` guards this specifically). The key map rebuilds the same way: `apply_settings` calls `keymap.build(self.settings["shortcuts"])` and hands the result to `EditorTabs`, `TerminalPanel` and `WelcomePage` via `apply_keymap()`, so `:reload` re-binds shortcuts live too.

**Navigation stays on the arrow keys, deliberately diverging from Vim.** `ModalEditor.handle_normal_mode`'s `nav_keys` check runs before and independent of modifiers, so Arrow/Home/End/PageUp/PageDown navigate, Shift+Arrow selects, and Ctrl+Arrow jumps by word — this is the permanent design, not a placeholder. Letter-based motions (`h/j/k/l`, `w/b`, `gg`/`G`) are a deliberate non-goal and will not be implemented; editing commands (`dd`, `yy`, `x`, `o`/`O`) remain open work, tracked separately in `docs/Roadmap.md`.
