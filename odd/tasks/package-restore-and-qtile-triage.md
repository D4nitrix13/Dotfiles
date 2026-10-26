# Task: Package Restoration and Qtile Log Triage

## Objective

Restore every package listed under `packages/` onto the current CachyOS installation through a single idempotent script, reorganize the package manifests by category for each package manager, and triage the Qtile log so the reported errors are separated into ones the restoration fixes and ones that need a separate fix.

## Problem

The manifests under `packages/` were captured from the previous CachyOS installation. After the reinstall, 268 of the 466 pacman packages are missing, so the recorded environment cannot be reproduced by hand. The Qtile log at `~/.local/share/qtile/qtile.log` also carries a mix of live warnings and stale tracebacks from before the 2026-10-25 restore, which makes it impossible to tell which failures are still real.

## Why

The user needs the machine to match its own recorded manifests, and needs to know which Qtile errors are actually still firing instead of guessing from a log that mixes three months of history.

## Scope

### In scope

- `Scripts/installPackages.sh`: idempotent installer covering pacman, AUR, npm, cargo, pipx and flatpak, documented in Spanish.
- `packages/` reorganized by category: one file per category and package manager, each with its own explanatory header.
- `Scripts/classifyPackages.py`: the tool that produced the split and that regenerates the aggregate manifests, so the reorganization is reproducible instead of a one-off edit.
- Idempotence: packages already present are detected and skipped, so the script can be re-run safely.
- Explicit handling of packages that were renamed upstream and of packages deleted from every repository.
- Qtile log triage across `qtile.log` and `qtile.log.1`.

### Out of scope

- Re-adding the Omarchy package repository. `omarchy-*` packages are unavailable on this machine and the audit deliberately removed that coupling.
- Rewriting the Qtile configuration.
- Committing, pushing or opening a pull request.

## Constraints

- `sudo` requires a password and is unavailable to the orchestrator. The script is executed by the owner; the orchestrator only validates it.
- `omarchy-keyring`, `omarchy-nvim` and `omarchy-walker` are absent from every configured repository. The owner confirmed on 2026-10-26 that they are not needed, so they were removed from the manifests entirely instead of being parked in an exclusion list.
- `asdcontrol` and `tobi-try` were deleted upstream from both the official repositories and the AUR.
- `pipx` 1.18.4 crashes with `ModuleNotFoundError: No module named 'filelock'`, so `python-filelock` must be installed before any pipx operation.
- `node` is not on `PATH` in a non-login shell; it is provided by mise. The script must locate it explicitly.
- Qtile runs under X11 (`/usr/sbin/qtile`, started from `/etc/ly/setup.sh`), not Wayland, even though the manifest also lists Hyprland and Wayland tooling.

## Route per task

| Task | Route | Trigger evidence |
|------|-------|------------------|
| T1 Qtile log triage | direct inline | read-only, 2 log files, findings are the deliverable |
| T2 Write `install-packages.sh` | direct inline | 1 new file, no research dependency beyond the already-completed package survey |
| T3 Validate the script | delegated direct (fresh worker) | independent check of the written artifact |

TDD mode: not applicable. The deliverable is a shell script and a report, not application source. Checks are structural (`bash -n`, `shellcheck`) plus a dry run against live package state.

## Checklist

- [x] T1 — Triage `qtile.log` and `qtile.log.1`: classify every error as live, stale or fixed
- [x] T2 — Write the installer covering all six managers
- [x] T3 — Validate with `bash -n`, `shellcheck` and a `--dry-run` against live state
- [x] T4 — Reorganize `packages/` by category for each manager, with headers and an exclusion convention
- [x] T5 — Move the installer to `Scripts/` and rewrite it in Spanish
- [x] T6 — Close the gap that left the `yay/` manifest out of the install plan
- [x] T7 — Ship the classification tool so the reorganization is reproducible
- [x] T8 — Fix the CachyOS mirror failure that made every download return 404
- [x] T9 — Resolve the rustup/rust conflict instead of aborting the transaction
- [x] T10 — Remove conflicting packages together with their dependents
- [x] T11 — Build AUR packages with the system toolchain, not Homebrew's
- [x] T12 — Move Homebrew to the end of the PATH in the session scripts
- [x] T13 — Drop the duplicated and unbuildable AUR packages

## Acceptance criteria

- The script runs twice in a row with the second run reporting zero actions, proving idempotence.
- `shellcheck Scripts/installPackages.sh` reports no findings.
- Every package in every manifest is either installed, reported as already present, or reported as unavailable with a reason.
- The dry run names the exact package count per manager and never mutates the system.
- The union of the category files of every manager is identical to the original flat manifests.
- The Qtile report separates the live warnings from the stale tracebacks and names the fix for each live one.

## Checks

- `bash -n Scripts/installPackages.sh`
- `shellcheck Scripts/installPackages.sh`
- `Scripts/installPackages.sh --dry-run`
- `Scripts/installPackages.sh --dry-run --only pacman` names the repository packages that are missing
- `Scripts/installPackages.sh --list` lists the excluded and the renamed packages
- `Scripts/classifyPackages.py --verify` reports OK for the six managers
- `Scripts/classifyPackages.py --split <manifiestos planos>` reproduces the same categorization

## Progress

### Completed

- Live-state survey: 1109 pacman packages present, 268 missing, 253 of those in official repositories and 15 not.
- The 15 packages outside the official repositories match `~/.local/share/backups/package-restore/not-in-repos.txt` exactly: 12 AUR-only, 2 deleted upstream, 1 renamed.
- npm: all 12 target packages already present in `~/.local/lib/node_modules`; npm only fails because `node` is absent from `PATH`.
- cargo: `tokei`, `vtracer` and `zellij` already installed.
- pipx: all 5 target applications already present in `~/.local/share/pipx/venvs`; `pipx list` crashes on the missing `filelock` module.
- flatpak: `es.danirod.Cartero` already installed.
- Qtile triage completed; findings are in the final report.

### Mirror and conflict findings

The install run failed on every CachyOS package with a 404 followed by a PGP
signature error. Root cause, verified rather than guessed:

- `cdn.cachyos.org` is not present in ANY of the three mirrorlists
  (`cachyos-v3-mirrorlist`, `cachyos-mirrorlist`, `mirrorlist`). The
  reflector-generated lists start with third-party mirrors that lag behind the
  repository.
- Every failing package returns HTTP 200 on `cdn.cachyos.org`, including
  `ty-0.0.91-1.1`, `gcc-fortran-16.2.1+r23+gd564253eb6c8-1`,
  `go-2:1.27.1-2` and `rustup-1.29.2-1`.
- The sync database stores the servers it was fetched from. A stale database
  keeps pointing at the dead mirrors even after the mirrorlist is corrected,
  so the database has to be refreshed too.
- The AUR build failures for `k6`, `mdbtools` and `cliamp` had the same cause:
  their repository dependency `go` could not be downloaded.
- `rustup` conflicts with `rust`, and the `rust` package also provides `cargo`
  and `rustfmt`, so installing `rustup` means removing `rust` outright.

The script now prepends the CDN to both CachyOS mirrorlists, refreshes the
sync database before the transaction, and removes the conflicting package when
the manifest declares the incompatible one.

### Second round of failures

After the mirror fix, two independent problems remained:

- `pacman -R rust` was refused: `quitando rust se rompe la dependencia con
  «rust», necesaria para el paquete rust-src`. The `rust` package also
  provides `cargo` and `rustfmt`, and `rust-src` depends on `rust`, so the
  dependent has to go first. The script now walks the dependent chain and
  removes it before the package it blocks.
- `mdbtools` failed to build with
  `../../libtool: eval: line 1912: syntax error near unexpected token '|'`.
  The cause is not the package: Homebrew puts its own `nm`, `ld`, `ar`,
  `ranlib`, `strip` and `libtool` in `/home/linuxbrew/.linuxbrew/bin`, which
  sits second in the PATH. Autotools picked up Homebrew's `nm`, its `-B`
  option check failed, and libtool emitted a command with an empty pipe
  stage. AUR builds now run with `/usr/bin:/bin` prepended to the PATH.
  Verified by rebuilding mdbtools with the clean PATH: `Compilación terminada:
  mdbtools 1.0.1-2`.
- `pacman -Qi` prints its field names in the system language, so the
  "Required By" lookup returned nothing under `es_MX`. The dependency query
  now forces `LC_ALL=C`. This one would have silently reintroduced the
  rustup failure.

### Homebrew in the session PATH

The owner pointed out that the PATH is configured in `~/.xsession`, not in
`~/.zshrc`. Two files put Homebrew first: `~/.xsession` and `~/.profile`.
The session PATH is built by `/etc/ly/setup.sh`, which sources `/etc/profile`
and then `~/.profile` for the fish shell, so both had to be fixed.

After the change, in a simulated fresh session, `/usr/bin` lands at position
34 and Homebrew at 43: `nm`, `ld`, `ar`, `ranlib`, `strip` and `objcopy`
resolve to the system binutils, `brew` stays reachable, and `python3` becomes
the system 3.14, which already carries the same numpy 2.5.4 and the same pip
26.2.2 that Homebrew had. Only `z3` stops being importable, and it is
available through `pip install z3-solver` if it is ever needed.

### Packages dropped from the AUR

| Package | Reason |
|---------|--------|
| `ptpython` | Already in the pipx manifest, and the PyPI wheel needs no compilation. |
| `python-pyodbc` | Replaced by `pyodbc` in pipx, which publishes a manylinux wheel for Python 3.14. |
| `wlroots-asan-git` | A debugging build from git, which by definition cannot be precompiled. |

`pyodbc` was added to the pipx manifest under a new `bases-de-datos`
category. The classification rules were updated to match, and the round trip
was verified: `--split` from the flat manifest reproduces the current
categorization exactly.

`classifyPackages.py --sync` now rewrites the header of every category file
from its own body, so the declared count and the install command cannot
drift from the packages listed.

### Verification evidence

- `pacman -Qq` returns 1109 packages; the diff against `packages/pacman/installed.txt` yields 268 missing.
- `pacman -Si` confirms `python-filelock` is in `extra`, which repairs pipx.
- `pacman -Si` and `yay -Si` both fail for `asdcontrol`, `tobi-try` and the three `omarchy-*` packages.
- The union of the category files of every manager is byte-identical to the original flat manifests, except for `asdcontrol` and `tobi-try`, which moved to `packages/pacman/excluidos/no-disponibles.txt`. Verified for all six managers.
- `Scripts/classifyPackages.py --split` reproduces the exact same categorization from the flat manifests, so the reorganization is deterministic rather than a one-off edit. The round trip was verified after every change to the manifests: the flat list derived from the category files, fed back through `--split`, reproduces the same files.
- `Scripts/classifyPackages.py --verify` reports OK for all six managers.
- The owner ran the installer during the session: 905 pacman packages and 11 of the 13 AUR packages from the pacman manifest were installed.
- `yay -Si hyprland-preview-share-picker-git` succeeds, confirming the rename target.
- `bash -n Scripts/installPackages.sh` passes.
- `shellcheck Scripts/installPackages.sh` reports no findings. It caught one real defect during development of the first version: the array was declared as `OMAARCHY_PACKAGES` but read as `OMARCHY_PACKAGES`.
- A second defect of the same class was NOT caught by shellcheck and had to be found by hand: the result array was written as `RESULTADOS_INSTALLED` in one branch. A one-character difference is below shellcheck's typo threshold.
- The dry run caught a third defect: the manifest glob also matched the aggregate `installed.txt`, so every package was counted twice. The summary reported 960 present instead of 480.
- The dry run completes in 0.79 s. The first version took 3 min 06 s because it asked pacman per package; replacing 268 `pacman -Si` calls with a single `pacman -Slq` lookup set cut it to 0.79 s.
- Package accounting reconciles exactly: 466 manifest entries = 198 present + 253 to install + 2 deleted upstream + 13 AUR. Adding 21 user-level packages already present gives 219 present, 254 to install (253 plus the `python-filelock` repair) and 13 to build.
- Idempotence proven with synthetic manifests holding only installed packages: two consecutive runs both report 47 present, 0 installed, 0 failed and identical output.
- Every `--only` manager reports its own scope: npm 12 present, cargo 3, pipx 5, flatpak 1.
- `--help`, an unknown option, an unknown manager and a missing `PKG_DIR` all fail with a clear message and a non-zero exit.

## Next step

The owner runs `Scripts/installPackages.sh --dry-run` to review the plan, then runs it without `--dry-run` and supplies the `sudo` password. Afterwards, the Qtile session must be restarted to confirm that the `dbus-fast` warning is gone.

## Forecast

Roughly 260 authored lines for the script. One coherent deliverable, comfortably inside a single delivery slice.

## Delivery strategy

`ask-on-risk` (default). The script is a single file well inside one slice.
