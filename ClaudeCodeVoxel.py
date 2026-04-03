#!/usr/bin/env python3
"""
Claude Code Voxel Mascot - 3D Printable Model Generator
========================================================

This script builds a voxel-style mascot and exports printable meshes in STL and
3MF formats. It is intended for makers who want an easy-to-edit, code-first
pipeline for custom figurines.

What it generates:
    - claude_base.stl / .3mf : Body + legs
    - claude_hat.stl / .3mf  : Wizard hat
    - claude_full.stl / .3mf : Fully assembled model

Default target size (approx.):
    - Width: 95 mm
    - Depth: 60 mm

Usage:
    python ClaudeCodeVoxel.py

Customization guide:
    - SCALE controls global model size in mm per voxel.
    - BX0/BX1, BY0/BY1, BZ0/BZ1 define body dimensions.
    - LEG_HEIGHT controls the leg height.
    - Hat shape is defined tier-by-tier in build_hat().
"""
import struct
import zipfile
import os
import sys
# ============================================================
# CONFIG - Adjust these to tune the model
# ============================================================
SCALE = 4.0  # mm per voxel unit
# Body bounding box (in voxel units)
# Width (X): BX1-BX0 units. 14 units * 5mm = 70mm body width
# Depth (Y): BY1-BY0 units. 11 units * 5mm = 55mm body depth
# Height(Z): BZ1-BZ0 units.  7 units * 5mm = 35mm body height (shorter = cuter)
BX0, BX1 = 3, 18    # body X: [3,16] = 14 units wide
BY0, BY1 = 2, 12    # body Y: [2,12] = 11 units deep
BZ0 = 4             # body bottom Z (leg top)
BZ1 = 11            # body top Z → 7 units tall (reduced from 10 for cuter look)
LEG_HEIGHT = BZ0     # legs go from z=0 to z=BZ0
# Eye position (relative to body)
EYE_Z = [8, 9]       # which Z rows the eyes occupy (2 tall)
EYE_LEFT_X = [6, 7]       
EYE_RIGHT_X = [13, 14]    
# ============================================================
# CORE FUNCTIONS
# ============================================================
def cube_triangles(x, y, z, neighbors):
    """Generate triangles for exposed faces of a unit cube at (x,y,z).
    Only creates faces where no neighbor cube exists (watertight mesh).
    """
    tris = []
    if (x, y, z+1) not in neighbors:  # top
        tris.append(([0,0,1], [x,y,z+1], [x+1,y,z+1], [x+1,y+1,z+1]))
        tris.append(([0,0,1], [x,y,z+1], [x+1,y+1,z+1], [x,y+1,z+1]))
    if (x, y, z-1) not in neighbors:  # bottom
        tris.append(([0,0,-1], [x,y,z], [x,y+1,z], [x+1,y+1,z]))
        tris.append(([0,0,-1], [x,y,z], [x+1,y+1,z], [x+1,y,z]))
    if (x+1, y, z) not in neighbors:  # right
        tris.append(([1,0,0], [x+1,y,z], [x+1,y+1,z], [x+1,y+1,z+1]))
        tris.append(([1,0,0], [x+1,y,z], [x+1,y+1,z+1], [x+1,y,z+1]))
    if (x-1, y, z) not in neighbors:  # left
        tris.append(([-1,0,0], [x,y,z], [x,y,z+1], [x,y+1,z+1]))
        tris.append(([-1,0,0], [x,y,z], [x,y+1,z+1], [x,y+1,z]))
    if (x, y+1, z) not in neighbors:  # back
        tris.append(([0,1,0], [x,y+1,z], [x,y+1,z+1], [x+1,y+1,z+1]))
        tris.append(([0,1,0], [x,y+1,z], [x+1,y+1,z+1], [x+1,y+1,z]))
    if (x, y-1, z) not in neighbors:  # front
        tris.append(([0,-1,0], [x,y,z], [x+1,y,z], [x+1,y,z+1]))
        tris.append(([0,-1,0], [x,y,z], [x+1,y,z+1], [x,y,z+1]))
    return tris
def voxels_to_mesh(voxels, scale=1.0, center_xy=True):
    """Convert a set of voxel positions to centered triangle list."""
    all_tris = []
    for pos in voxels:
        all_tris.extend(cube_triangles(pos[0], pos[1], pos[2], voxels))
    if not all_tris:
        return []
    if center_xy:
        coords = list(voxels)
        min_x = min(c[0] for c in coords)
        max_x = max(c[0] for c in coords) + 1
        min_y = min(c[1] for c in coords)
        max_y = max(c[1] for c in coords) + 1
        cx = (min_x + max_x) / 2.0
        cy = (min_y + max_y) / 2.0
    else:
        cx, cy = 0, 0
    centered = []
    for normal, v1, v2, v3 in all_tris:
        centered.append((
            normal,
            [(v1[0]-cx)*scale, (v1[1]-cy)*scale, v1[2]*scale],
            [(v2[0]-cx)*scale, (v2[1]-cy)*scale, v2[2]*scale],
            [(v3[0]-cx)*scale, (v3[1]-cy)*scale, v3[2]*scale]
        ))
    return centered
def write_binary_stl(filename, triangles):
    """Write binary STL file."""
    with open(filename, 'wb') as f:
        header = b'Claude Code Mascot' + b'\0' * 62
        f.write(header[:80])
        f.write(struct.pack('<I', len(triangles)))
        for normal, v1, v2, v3 in triangles:
            f.write(struct.pack('<3f', *normal))
            for v in [v1, v2, v3]:
                f.write(struct.pack('<3f', *v))
            f.write(struct.pack('<H', 0))
def create_3mf(stl_path, output_path):
    """Create 3MF from binary STL."""
    vertices, triangles = [], []
    vertex_map = {}
    with open(stl_path, 'rb') as f:
        f.read(80)
        num = struct.unpack('<I', f.read(4))[0]
        for _ in range(num):
            struct.unpack('<3f', f.read(12))
            tri = []
            for _ in range(3):
                v = struct.unpack('<3f', f.read(12))
                key = (round(v[0],4), round(v[1],4), round(v[2],4))
                if key not in vertex_map:
                    vertex_map[key] = len(vertices)
                    vertices.append(key)
                tri.append(vertex_map[key])
            triangles.append(tri)
            struct.unpack('<H', f.read(2))
    vxml = '\n'.join(f'      <vertex x="{v[0]:.4f}" y="{v[1]:.4f}" z="{v[2]:.4f}" />' for v in vertices)
    txml = '\n'.join(f'      <triangle v1="{t[0]}" v2="{t[1]}" v3="{t[2]}" />' for t in triangles)
    model = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US"
       xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <resources>
    <object id="1" type="model">
      <mesh>
        <vertices>
{vxml}
{txml}
        </vertices>
        <triangles>
        </triangles>
      </mesh>
    </object>
  </resources>
  <build><item objectid="1" /></build>
</model>'''
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml',
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />'
            '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml" />'
            '</Types>')
        zf.writestr('_rels/.rels',
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" />'
            '</Relationships>')
        zf.writestr('3D/3dmodel.model', model)
# ============================================================
# MODEL BUILDING
# ============================================================
def build_legs():
    """8 thicker legs, each 2x2 voxel cross-section, 1 voxel shorter."""
    voxels = set()
    leg_positions = [
        (4, 3), (7, 3), (12, 3), (15, 3),      # front row
        (4, 9), (7, 9), (12, 9), (15, 9),  # back row
    ]

    leg_height = max(1, LEG_HEIGHT)  # Keep at least 1 layer to avoid invalid ranges.

    for lx, ly in leg_positions:
        for dx in (0, 1):
            for dy in (0, 1):
                for z in range(0, leg_height):
                    voxels.add((lx + dx, ly + dy, z))
    return voxels
def build_body():
    """Main body cube with eye indentations and arm stubs. No snout/mouth."""
    voxels = set()
    # Solid body block
    for x in range(BX0, BX1):
        for y in range(BY0, BY1):
            for z in range(BZ0, BZ1):
                voxels.add((x, y, z))
    # Eye indentations (remove voxels from front face)
    for x in EYE_LEFT_X:
        for z in EYE_Z:
            voxels.discard((x, BY0, z))
    for x in EYE_RIGHT_X:
        for z in EYE_Z:
            voxels.discard((x, BY0, z))
    # Left arm stub
    for y in [5, 6]:
        for z in [BZ0+1, BZ0+2]:
            voxels.add((BX0-1, y, z))
    # Right arm stub
    for y in [5, 6]:
        for z in [BZ0+1, BZ0+2]:
            voxels.add((BX1, y, z))
    # Ears (small bumps on top-front corners)
    # voxels.add((BX0, BY0, BZ1))
    # voxels.add((BX0+1, BY0, BZ1))
    # voxels.add((BX0, BY0+1, BZ1))
    # voxels.add((BX0+1, BY0+1, BZ1))
    # voxels.add((BX1-1, BY0, BZ1))
    # voxels.add((BX1-2, BY0, BZ1))
    # voxels.add((BX1-1, BY0+1, BZ1))
    # voxels.add((BX1-2, BY0+1, BZ1))

    return voxels
def build_hat():
    """Purple wizard hat: brim + tiered layers + bent tip + dots."""
    voxels = set()
    hz = BZ1  # hat starts at body top
    # Brim: trimmed by one voxel on the left side (first layer only)
    for x in range(2, 19):   # Previously: range(1, 19)
        for y in range(1, 13):
            voxels.add((x, y, hz))
    # Tier 1
    for x in range(4, 16):
        for y in range(2, 12):
            voxels.add((x, y, hz+1))
    # Tier 2
    for x in range(5, 15):
        for y in range(3, 11):
            voxels.add((x, y, hz+2))
    # Tier 3
    for x in range(6, 14):
        for y in range(4, 10):
            voxels.add((x, y, hz+3))
    # Tier 4
    for x in range(7, 13):
        for y in range(4, 9):
            voxels.add((x, y, hz+4))
    # Tier 5
    for x in range(7, 11):
        for y in range(5, 8):
            voxels.add((x, y, hz+5))
    # Bent tip - curves to left
    for x in range(5, 9):
        for y in range(5, 8):
            voxels.add((x, y, hz+6))
    for x in range(4, 7):
        for y in range(5, 8):
            voxels.add((x, y, hz+7))
    # for x in range(3, 5):
    #     for y in range(6, 8):
    #         voxels.add((x, y, hz+8))
    # voxels.add((2, 6, hz+8))
    # voxels.add((2, 7, hz+8))
    #voxels.add((2, 6, hz+9))
    # Decorative dots (protrusions)
    dots = [
        (6, 1, hz+1), (13, 1, hz+1),
        (8, 2, hz+2), (12, 3, hz+3),
        (9, 3, hz+4),
        (3, 6, hz+1),
        (5, 5, hz+7),
    ]
    # for d in dots:
    #     voxels.add(d)
    return voxels
def print_dimensions(name, voxels):
    coords = list(voxels)
    if not coords:
        print(f"  {name}: empty")
        return
    w = (max(c[0] for c in coords) - min(c[0] for c in coords) + 1) * SCALE
    d = (max(c[1] for c in coords) - min(c[1] for c in coords) + 1) * SCALE
    h = (max(c[2] for c in coords) - min(c[2] for c in coords) + 1) * SCALE
    print(f"  {name}: {w:.0f} x {d:.0f} x {h:.0f} mm (W x D x H)")
def export_part(name, voxels, out_dir):
    """Export a voxel set as STL + 3MF."""
    tris = voxels_to_mesh(voxels, scale=SCALE)
    stl_path = os.path.join(out_dir, f"{name}.stl")
    mf_path = os.path.join(out_dir, f"{name}.3mf")
    write_binary_stl(stl_path, tris)
    create_3mf(stl_path, mf_path)
    return stl_path, mf_path
def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(base_dir, "home", "claude")
    os.makedirs(out_dir, exist_ok=True)

    print("Building Claude Code Mascot (3 parts)...")
    print(f"Scale: {SCALE} mm/voxel\n")

    legs = build_legs()
    body = build_body()
    hat = build_hat()

    base = legs | body
    full = base | hat   # Full assembled model

    print("Dimensions:")
    print_dimensions("Base (body+legs)", base)
    print_dimensions("Hat", hat)
    print_dimensions("Full", full)

    print("\nExporting parts...")
    export_part("claude_base", base, out_dir)
    export_part("claude_hat", hat, out_dir)
    export_part("claude_full", full, out_dir)   # Full model export

    print("\nDone! Files:")
    for part in ["claude_base", "claude_hat", "claude_full"]:  # Include full model
        stl = os.path.join(out_dir, f"{part}.stl")
        mf = os.path.join(out_dir, f"{part}.3mf")
        print(f"  {part}.stl  ({os.path.getsize(stl)/1024:.1f} KB)")
        print(f"  {part}.3mf  ({os.path.getsize(mf)/1024:.1f} KB)")

if __name__ == "__main__":
    main()