# Claude Code Voxel Mascot

A code-first 3D printable voxel mascot generator written in Python.

This project generates printable meshes (`.stl` and `.3mf`) for a mascot model composed of a base (body + legs), a wizard hat, and a full assembled version.

## Features

- Voxel-based geometry generation (easy to edit and extend)
- Watertight mesh output from exposed voxel faces
- Exports both STL and 3MF
- Separate parts plus full assembled model
- Simple parameter-driven customization (scale, body bounds, legs, hat tiers)

## Preview Dimensions (Default)

Approximate target size:

- Width: 95 mm
- Depth: 60 mm

Final dimensions depend on `SCALE` and voxel ranges in the script.

## Requirements

- Python 3.8+
- No third-party dependencies (standard library only)

## Quick Start

Run the generator from the project folder:

```bash
python ClaudeCodeVoxel.py
```

Generated files are written to:

```text
home/claude/
```

Expected outputs:

- `claude_base.stl` / `claude_base.3mf`
- `claude_hat.stl` / `claude_hat.3mf`
- `claude_full.stl` / `claude_full.3mf`

## Configuration

Edit constants near the top of the script:

- `SCALE`: millimeters per voxel
- `BX0`, `BX1`, `BY0`, `BY1`, `BZ0`, `BZ1`: body bounds
- `LEG_HEIGHT`: leg height in voxels
- `EYE_Z`, `EYE_LEFT_X`, `EYE_RIGHT_X`: eye indentation positions

Hat shape is defined in `build_hat()` by layered voxel ranges.

## Project Structure

```text
.
├─ ClaudeCodeVoxel.py
├─ README.md
└─ home/
   └─ claude/
      ├─ claude_base.stl
      ├─ claude_base.3mf
      ├─ claude_hat.stl
      ├─ claude_hat.3mf
      ├─ claude_full.stl
      └─ claude_full.3mf
```

## License

No license is included yet.
Add a `LICENSE` file before publishing if you want others to legally use, modify, and redistribute this project.
