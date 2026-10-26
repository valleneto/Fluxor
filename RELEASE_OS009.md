# OS009 — Beta release candidate preparation

State: **NOT yet a release candidate**, macOS GUI and distribution tests pending.

## Changes
- Copy loop checks cancellation per 1 MiB block, cleaning up an incomplete destination file.
- Copy refuses changed source size since preview, rejects destination directories redirected through symlinks (best effort, not atomic security).
- Added isolated regression tests in `tests/test_os009.py`.
- Added `scripts/build_macos.sh` as macOS-only build preparation.
- No delete-original functionality; no automatic public distribution.

## Build on trusted local macOS
1. Update development branch only after `git status --short` is clean.
2. Activate the existing virtual environment.
3. Install PyInstaller manually when ready (free dependency): `python3 -m pip install pyinstaller`.
4. Run `zsh scripts/build_macos.sh`.
5. Test `dist/Fluxor Control.app` with a separate, small synthetic folder; verify navigation, index, preview, duplicate scan, cancel, and copy.
6. Measure launch time, RAM and disk footprint in Activity Monitor.
7. Test a clean macOS user environment before wider beta.

No codesign/notarization, app store submission, developer-account purchase or upload is performed by this script.

## Remaining release blockers
- UI testing on real macOS, including Qt thread lifecycle and Quick Look.
- Potential race conditions when destination filesystem changes between validation and open; robust secure dir-descriptor handling remains future work.
- Indexing exceptions may leave an unclosed SQLite connection; cancellation and transaction rollback need further hardening.
- Source contents can change while copying even when size is unchanged. A post-copy hash helps detect mismatches, but concurrent identical changes are not entirely prevented.
- Cloud-only files need safe detection before SHA-256 to avoid unrequested downloads.
- Global sort interaction, accessible UX review, reliable task history/undo, signed/notarized distribution remain outstanding.

## Git workflow
All work lives on `dev/seguranca-mvp`, PR #1 draft. `master` must remain unchanged pending explicit merge authorization.
