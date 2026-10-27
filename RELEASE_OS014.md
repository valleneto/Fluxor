# OS 014 — Fluxor Release Readiness

**Result:** development hardening delivered; NOT commercially ready.
Pre-OS014 baseline: `5743129211e4ae8fb2bcd0f2fec1a01feb2475ee`.
Branch: `dev/seguranca-mvp`. PR #1 remains a draft. Main branch is not part of this work.

## What changed
- Catalog and review SQLite connections close reliably; index updates roll back on error or cancellation.
- Index emits actual item counts; both indexing and copy preview support cooperative cancellation.
- Copy previews record modification timestamps; stale inputs are rejected and copied source identity is checked.
- Duplicate scan skips known cloud locations, verifies metadata freshness, and requests user confirmation before reading file content.
- Zen Core now distinguishes completed, failed, partial, and cancelled tasks instead of showing false success.
- Inspector displays catalog metadata, constrains image decoding, and allows stopping video startup.
- Search is debounced, filters by project/size, sorts globally, paginates correctly, and formats sizes.
- Local macOS build includes explicit lazy Qt Multimedia imports and the Fluxor logo. It remains unsigned and unnotarized.

## Evidence and limitations
- GitHub Actions includes core, rollback, cancellation, duplicate, stale-plan, and Qt offscreen GUI smoke checks.
- Qt GUI smoke uses a synthetic PNG and temporary HOME; it is NOT a macOS hardware test.
- One synthetic 50,000-record benchmark on Ubuntu yielded P95 search 23.3 ms; results may differ on real files and the Mac.
- Abrupt interruption of a copy can leave a partial destination file; journaled/atomic copy and recovery must precede commercial release.
- Offline-only cloud detection is not exhaustive. Duplicate scans may read remotely hosted files from unrecognized providers.
- Real gallery thumbnails, large-catalog background insights, true undo, full Project View and full accessibility testing remain incomplete.
- Intel/Apple Silicon install testing, audio/video codec matrix, bundle icon conversion, signing, notarization, versioning and updater remain pending.
- No personal files were accessed, and no paid service, public release, merge or deployment was requested or executed.

## Target-Mac acceptance test
1. Inspect local changes before updating. Close the Fluxor app.
2. Fetch and fast-forward the development branch only if local changes permit.
3. Run `python3 fluxor_iniciar.py` in the existing virtual environment.
4. Check Zen Core, reduced movement, sidebar, library search/project/size filters, pagination, and header sorting.
5. Select a synthetic local image: Inspector should display it. Verify Space still opens the native Quick Look popup.
6. Cancel indexing a synthetic folder and verify that the prior catalog remains intact.
7. Check duplicate consent prompt and review-only controls on synthetic duplicates.
8. Confirm copy-plan invalidation after synthetic file modifications. Inspect CPU/RAM and repeat media previews.
9. Back up the previous app bundle before building a new local bundle via `zsh scripts/build_macos.sh`.

## Non-destructive rollback
Prior tested development snapshot: `5743129211e4ae8fb2bcd0f2fec1a01feb2475ee`.
With a clean local working tree, create an independent verification branch from that commit rather than rewriting branch history:
`git fetch origin && git switch -c validation/os013-baseline 5743129211e4ae8fb2bcd0f2fec1a01feb2475ee`.
Preserve the existing bundled app before rebuilding. For permanent rollback, prepare reviewed revert commits in a separate development PR.
