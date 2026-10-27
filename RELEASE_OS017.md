# FLUXOR — OS017 | Street-art visual rebuild

Status: **candidate for manual visual homologation**. No merge, deploy, automatic installation or modifications to user media.

## Why this OS was needed

The OS016 interface looked generic/corporate. The approved creative brief is **street graffiti / trap / authentic movement**, not a mere "graphite gray" palette. The product remains named **FLUXOR** pending separate naming approval.

## Implementation

### Visual identity
- `fluxor_mural.py`: original SVG-free/asset-free vector mural in Qt with graff-inspired slanted wordmark FLUXOR, multi-layer ink shadows, paint dashes, moving bezier ribbons, deterministic spray texture, hand-tag underline and muted editorial markers.
- Font glyph vector paths are cached once per instance to reduce CPU. No downloaded fonts, bundled videos, 3D/WebEngine, JavaScript or external visual services.
- `fluxor_iniciar.py`: expressive home, routes 01/02/03, concise operational copy and actual actions.
- `fluxor_design.py`: coherent "asphalt + paint" palette (lemon yellow-green, coral, teal) and legible controls.
- Existing `ZenCore` API preserved for phase state, reducing animation and halting when not visible. Max 20 frames/second.

### Functional regression and fixes
- Same-page navigation no longer leaves the checkable sidebar item unchecked; blocked navigation resynchronizes the active item.
- Library Inspector context from OS015 and safe preview policy unchanged.
- Safe organizer preview/copy/ETA/report from OS016 unchanged.
- Tests use only synthetic temporary fixtures; original Samsung volume is never accessed.

### CI
- `.github/workflows/mvp-checks.yml` runs Python compile checks, existing core OS tests, GUI OS014/OS015/OS016, and GUI OS017.
- `tests/test_os017_gui.py`: verifies the mural actually paints, animation phase advances, reduced motion stops it, selected route remains checked, file content remains intact.
- Initial CI attempts had a Linux Qt/Python interpreter shutdown crash **after the test assertions passed** when repeatedly converting rendered Qt pixmaps to raw byte buffers. The test was adjusted to avoid that problematic native conversion, without suppressing a production exception; current CI succeeds.
- Linux offscreen CI **cannot certify** perceived art direction or smooth performance on a real macOS Catalina 2012 machine.

## Manual user homologation on MacBook Pro

Close the Fluxor application window, then:

```bash
cd ~/Projetos/google-fotos-lab
git status --short
git fetch origin
git switch -c homologacao-grafite-os017 --track origin/dev/visual-graffiti-os017
source .venv/bin/activate
python3 fluxor_iniciar.py
```

Do not use `git reset --hard` or `git clean` if Git encounters local conflicts; stop and preserve the existing working copy.

### What to inspect

1. Home: visible expressive graff lettering FLUXOR, procedural flow ribbons, coherent paint color palette and meaningful actions.
2. Visual motion should be discreet but apparent; verify that **Reduzir animação** pauses it.
3. Sidebar 01/02/03 stays checked on navigation and repeated clicking.
4. Library occupies full width until selection; Inspector appears only when a file is selected.
5. Organizer still has preview-first and visible report. Do not authorize copying from the Samsung.
6. On a laptop, verify no clipping, readability, no stutter and no unusual CPU/fan activity.

## Safety / scope explicitly **not** completed

- **SFTP browser in the Fluxor** and SMB/AFP authorization are a separate OS, not part of the visual release.
- Not a signed/notarized macOS .app installer.
- No guarantee that every audio/video/office format has a native thumbnail; the media policy remains conservative.
- The OS is a **visual candidate** until the real user approves; user feedback may require further authorial iterations.
