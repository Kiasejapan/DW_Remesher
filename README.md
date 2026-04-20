# DW_Remesher

Cylinder remeshing tool for Maya (2018-2025, Python 2 & 3, PySide2 / PySide6).

Two operations on a single tab:

- **Cylinder Cleanup** — detects the cylinder's axis via PCA (or lets you force X/Y/Z), snaps every vertex to a perfectly regular cylinder. **Topology and UVs are preserved** — only vertex positions move.
- **Change Sides (N↔M)** — rebuilds the mesh with a different side count (3–128). Per-ring axis positions and radii are preserved; cylindrical UV projection is applied to the new mesh.

## Install

1. Copy `DW_Remesher.py` into your Maya scripts folder:
   - Windows: `C:\Users\<you>\Documents\maya\scripts\`
   - macOS:   `~/Library/Preferences/Autodesk/maya/scripts/`
   - Linux:   `~/maya/scripts/`

2. In the Maya Script Editor (Python tab):

   ```python
   import DW_Remesher
   DW_Remesher.show()
   ```

3. (Optional) make a shelf button with that snippet.

## Features

- **Auto-update** — the ⬇ button checks the GitHub `main` branch for a newer build and installs it to your Maya scripts folder with one click.
- **Reload** — the ↻ button re-imports the module in place; no need to restart Maya after an update.
- **Bilingual UI** — EN/JP toggle in the top-right.
- **Undo support** — every apply is wrapped in a single undo chunk.

## Build (for contributors)

Source files live in `_build/src/*.txt` and are concatenated by `_build/build.py` into the top-level `DW_Remesher.py`:

```bash
python _build/build.py         # stamps VERSION and rebuilds
python _build/build.py --no-stamp
```

On Windows, `build.bat` wraps build + `git commit` + `git push`.

## License

MIT. See `LICENSE`.
