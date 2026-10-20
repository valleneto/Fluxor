# OS 011 — Visual Media beta validation

## Implemented
- The Biblioteca now offers a list/gallery switch (file icons only, no batch thumbnails).
- Selecting an image/video shows an optional Inspector panel. No media is decoded on selection.
- **Mostrar quadro** loads a chosen image, or generates a video poster using macOS `qlmanage -t`. Poster generation uses QProcess with a timeout, temporary directory, and cleanup.
- **Trecho de 4 s (sem som)** lazily initializes QtMultimedia and QVideoWidget. Muted playback stops after 4 seconds and unloads the media source.
- **Parar** interrupts playback. Selecting another file stops the previous preview.
- A simple cloud-path heuristic disables previews for recognized CloudStorage/Mobile Documents paths; **this is not comprehensive cloud-file detection**.
- Unsupported codecs show fallback text. Double-click still opens the user-selected file in the macOS default application.
- No persistent thumbnail cache, no automatic hover playback, no deletion, and no third-party paid service.

## Test coverage limits
- Linux GitHub Actions validates syntax and the pure media policy, **not** Qt GUI playback or codec decoding.
- Video previews may depend on native backend, QtMultimedia and QtMultimediaWidgets plugins, system codecs, and PyInstaller bundling.
- `qlmanage` thumbnail may be an icon or generic frame for some codecs; not guaranteed a frame from the middle.
- The gallery deliberately uses icons; actual thumbnail grid is not implemented to keep memory bounded.
- Proactive cloud-only file detection using filesystem-provider APIs remains a blocker before broadly scanning cloud roots.

## Mac test on synthetic/local videos
1. Close Fluxor; ensure `git status --short` is clean before updating.
2. `git fetch origin && git merge --ff-only origin/dev/seguranca-mvp`
3. Start `python3 fluxor_iniciar.py` from activated existing venv, then rebuild with `zsh scripts/build_macos.sh` only after testing.
4. Index a small truly local folder with an MP4/H.264 video, PNG image, and unsupported sample.
5. Select video, click **Mostrar quadro**; confirm UI is responsive while loading.
6. Click **Trecho de 4 s (sem som)**; verify picture, mute and automatic stop.
7. Switch file during playback, and click **Parar**. Verify playback ends.
8. Switch list/gallery and confirm selection, Inspector data and fallback behavior.
9. Observe Activity Monitor (RAM/CPU), repeat 10 previews and check for leaks/crashes.
10. Avoid cloud-only files for this test.

**Not signed, notarized, or ready for public distribution. master remains untouched.**
