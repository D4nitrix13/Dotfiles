# Task: System Audit and CachyOS Reinstall Preparation

## Objective

Prepare a fresh CachyOS installation with a corrected partition layout (larger `/`, smaller `/home`, 8 GB swap), remove the Omarchy dependency from the dotfiles repository, update every package manager, and produce a persisted audit that classifies every installed package and every repository section as keep / remove / optional.

## Problem

The machine has a 59 GB root partition at 97% capacity (2.1 GB free) while `/home` (129 GB) sits at 57% with 54 GB free. The root partition cannot absorb further package growth and the layout is inverted relative to actual usage. A reinstall is planned.

Separately, the thermal mitigation applied on 2026-10-20 (`cpufreq-stabilize.service`, `powersave` governor, 3.0 GHz cap, `balance_power` EPP) has been lost: the service and its script no longer exist, the governor is back to `performance` on all 16 CPUs, EPP is `performance`, the cap is back to 4.55 GHz, and `thermal_zone0` reads 81 °C at idle. That mitigation was never versioned in this repository, so it cannot be restored from git. The `amdgpu.runpm=0` parameter applied on 2026-10-24 keeps the GPU permanently powered and will increase the thermal load further.

## Why

The user is reinstalling CachyOS, needs the disk layout corrected first, wants Omarchy removed from the dotfiles, wants all package managers updated before the reinstall so the package manifests are accurate, and wants an audit that tells them which packages and configuration sections still earn their place.

## Scope

### In scope

- Repository audit, section by section, across all 608 tracked files.
- Redundancy detection, including the `docs/` (lowercase, untracked) vs `Docs/` (uppercase, tracked) case collision on a case-sensitive filesystem.
- Identification of Omarchy-coupled configuration and the portable equivalent for each.
- Package inventory across pacman, yay, brew, pipx, cargo, npm, go, uv and flatpak, classified keep / remove / optional with justification.
- Package manager update commands.
- Thermal mitigation restored and made persistent in this repository.
- Partition and swap sizing plan for the reinstall.

### Out of scope

- Performing the reinstall itself.
- Physical maintenance (thermal paste, fan cleaning, battery replacement) — recommended, not executable.
- Modifying the partitions of the running system.

## Constraints

- `sudo` requires a password and is not available to the orchestrator. Every privileged command is handed to the user as a copy-pasteable block.
- Root filesystem has 2.1 GB free; a kernel upgrade needs the pacman cache cleared first or the transaction can fail mid-flight and leave the system unbootable.
- `pacman -Scc` was run on 2026-10-21 and erased the package cache, so no in-place downgrade path exists for kernel 7.2.8 or mesa 26.2.3.
- CachyOS mirrors `mirror.krfoss.org` and `mirror5.krfoss.org` return HTTP 418; `cdn.cachyos.org` works.
- The Dell BIOS (113-BARCELO-004, 2022-02-23) is already the latest published by fwupd for this Inspiron 15 3535.
- `amdgpu.runpm=0` trades battery life and thermals for display stability; it is the first parameter to reconsider if thermal throttling appears.

## Route per task

| Task | Route | Trigger evidence |
|------|-------|------------------|
| T1 Free root space | delegated direct (user-executed commands) | privileged operation, no in-agent route |
| T2 Update package managers | delegated direct (user-executed commands) | privileged, long-running, multi-manager |
| T3 Repository section map | delegated direct | 4+ files, 608 tracked files across 8 sections |
| T4 Redundancy and Omarchy coupling | delegated direct | depends on T3 output, multi-file analysis |
| T5 Package inventory classification | delegated direct | cross-manager, needs the manifests plus live state |
| T6 Persist audit and recommendations | delegated direct | 2+ non-trivial files (audit in `docs/`, remediation files in repo) |
| T7 Partition and swap plan | direct inline | single document, no research dependency |

TDD mode: not applicable. No source code changes — configuration, manifests and documentation only. Checks are structural (valid config syntax, regenerated bootloader config, service state) plus functional (idle soak test).

## Checklist

- [x] T0 — Establish baseline: disk layout, package manager inventory, repository section count, thermal state
- [ ] T1 — Free root space: clear pacman cache, remove orphaned packages, report reclaimable total *(blocked: needs the owner's sudo)*
- [ ] T2 — Update every package manager; record pre/post versions *(blocked: needs the owner's sudo)*
- [x] T3 — Map every repository section: purpose, contents, dependencies, portability
- [x] T4 — Flag redundancies and Omarchy-coupled config with the portable replacement for each
- [x] T5 — Classify every installed package: keep / remove / optional, with reason
- [x] T6 — Write the audit to `docs/`, restore and version the thermal mitigation, refresh package manifests
- [x] T7 — Document the partition and swap plan for the reinstall

T3 through T7 were completed by a delegated writer that hit the token plan limit while producing the audit document. Its output was reviewed, verified and finished by the orchestrator: the `docs/README.md` index entry was added, both new scripts were made executable, and the missing `.gitignore` entries confirmed. Committed as `dc8c202` on `chore/system-audit-and-reinstall-prep`.


## Acceptance criteria

- Root filesystem has at least 10 GB free after T1.
- All package managers report no pending updates after T2.
- Every repository section appears in the audit with a keep/remove/optional verdict.
- Every package appears in the classification table; no unexplained omissions.
- The thermal mitigation exists as a versioned file in this repository and is active after boot.
- The audit is readable from `docs/` and linked from `docs/README.md`.
- The partition plan states explicit sizes for `/`, `/home` and swap, with the reasoning.

## Checks

- `df -h /` shows the expected free space.
- `pacman -Qkk` and `pacman -Qtdq` report no missing files and no orphans.
- `systemctl is-active cpufreq-stabilize.service` returns `active`; governor reads `powersave`; EPP reads `balance_power`; `thermal_zone0` is below 60 °C at idle.
- `cat /proc/cmdline` contains `amdgpu.runpm=0 amdgpu.aspm=0 amdgpu.gpu_recovery=1`.
- `git status` shows only intended changes; no secrets staged.

## Progress

### Completed

- Baseline captured: root 97% (2.1 GB free), `/home` 57% (54 GB free), 63 GB in `$HOME`.
- GPU freeze diagnosed and patched (DPMS replaced by backlight dim, plus a `post-update.d` hook).
- `kernel.sysrq = 1` applied; `amdgpu.runpm=0 amdgpu.aspm=0 amdgpu.gpu_recovery=1` in GRUB.
- Ollama removed from Vulkan on the shared iGPU; screensaver (120 FPS `tte`) disabled.
- fwupd installed; BIOS confirmed current.
- Thermal regression found: mitigation lost, governor `performance`, 81 °C at idle.
- Full repository audit written to `docs/auditoria-2026-10-24.md` (589 lines, 12 sections).
- Thermal mitigation recovered and versioned under `Utils/systemd/`.
- Portable brightness-dim script versioned under `Utils/scripts/display-brightness`.
- Package manifests regenerated from live state; the three `omarchy-*` packages kept out of the manifests (as of 2026-10-26 they no longer appear in any manifest file; the reason is recorded in `docs/auditoria-2026-10-24.md`).
- `.gitignore` extended with `.config/opencode/service.json` and `.config/chromium-headless/`.

### Verification evidence

- `/proc/sys/kernel/sysrq` = 1
- `GRUB_CMDLINE_LINUX_DEFAULT` contains the three `amdgpu` parameters
- `systemctl show ollama.service -p Environment` includes `OLLAMA_VULKAN=false`
- `fwupdmgr get-updates` reports System Firmware at the latest version
- No manifest under `packages/` contains an `omarchy-` entry
- `packages/npm/installed.txt` contains no Node-bundled package
- `bash -n` passes on `Utils/systemd/cpufreq-stabilize.sh` and `Utils/scripts/display-brightness`
- The plaintext password in `.config/opencode/service.json` was confirmed never to have entered git history
- `git show --stat dc8c202` stages only the intended 14 files

## Next step

The owner runs the privileged commands for T1 and T2, plus the thermal mitigation installation, then the manifests are regenerated one final time against the updated package set. The legacy X11 estate and the remaining Omarchy coupling are not touched until the decisions in section 11 of the audit are answered.


## Forecast

Approximately 500 authored changed lines across the audit document and the remediation files. This is one coherent deliverable, so no split is planned; the advisory per-task budget of roughly 400 lines is exceeded only by the audit narrative itself.

## Delivery strategy

`ask-on-risk` (default). A single audit document plus small remediation files stays well inside one delivery slice.
