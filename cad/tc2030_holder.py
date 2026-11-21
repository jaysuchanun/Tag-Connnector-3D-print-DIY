"""
One-piece 3D-printed pin holder for the DIY TC2030 probe.

Replaces BOTH PCBs of afedorov3/Tag-Connect-DIY (CC0) with a single printed part:
  * front plate  = old "bottom PCB" outline (thickened 1.2 -> 1.6 mm)
  * rear flange  = old "top PCB" outline, still 1.2 mm so it drops into the
                   original case slot
  * two side spines join the plates around the guide pins, leaving the long
    sides open so wires can be soldered to the pogo barrels.

Also generates:
  * a pin-depth jig (sets pogo tails + guide ends 1.5 mm behind the flange)
  * case halves with the 3 mm entry pocket widened for the spines

Coordinates (mm): X = long axis (same as the original Gerber), Y = across,
Z = pin axis, Z=0 at the probe-tip face of the front plate, +Z toward the case.

Run:  python3 cad/tc2030_holder.py   (needs cadquery, trimesh, manifold3d)
"""
import math
import os
import re

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "output")

# ---------------------------------------------------------------- parameters
POGO_PITCH = 1.27          # TC2030 grid
POGO_HOLE = 0.70           # P50 barrel is 0.68 mm; print/drill to 0.70
GUIDE_HOLE = 0.80          # 0.8 mm steel wire (paper clip)
FRONT_T = 1.60             # front plate thickness (PCB was 1.2)
FLANGE_T = 1.20            # MUST stay 1.2 to fit the case slot
FLANGE_Z0 = 9.00           # flange front face (same as original top PCB)
SPINE_X = 1.90             # spines occupy |x| >= SPINE_X
JIG_DEPTH = 1.50           # pogo tail / guide end protrusion behind flange
CASE_CLEAR = 0.15          # clearance of spine pocket cut into the case
CASE_Z_OFFSET = 4.65       # holder Z -> original case STL Z
CASE_FRONT_Z = 10.60       # case front face (case STL coords)
CASE_SLOT_Z0 = 13.65       # case slot front face (case STL coords)

POGO = [(x * POGO_PITCH, y * POGO_PITCH / 2) for y in (-1, 1) for x in (-1, 0, 1)]
GUIDES = [(-2.54, 0.0), (2.54, -1.016), (2.54, 1.016)]


# ------------------------------------------------------ Gerber outline parser
def gerber_outline(path, arc_step_deg=6):
    """Read a mechanical-layer Gerber (lines + G03 arcs) -> closed point list."""
    txt = open(path).read()
    scale = 1e-3  # FSLAX43, mm
    x = y = 0.0
    mode = "G01"
    segs = []
    for blk in txt.replace("\n", "").split("*"):
        if blk.startswith(("G01", "G02", "G03")) and len(blk) == 3:
            mode = blk
            continue
        m = re.match(r"(?:X(-?\d+))?(?:Y(-?\d+))?(?:I(-?\d+))?(?:J(-?\d+))?D0([12])$", blk)
        if not m:
            continue
        nx = int(m[1]) * scale if m[1] else x
        ny = int(m[2]) * scale if m[2] else y
        if m[5] == "1":
            if mode == "G01":
                segs.append([(x, y), (nx, ny)])
            else:
                cx, cy = x + int(m[3] or 0) * scale, y + int(m[4] or 0) * scale
                r = math.hypot(x - cx, y - cy)
                a0 = math.atan2(y - cy, x - cx)
                a1 = math.atan2(ny - cy, nx - cx)
                if mode == "G03":
                    while a1 <= a0:
                        a1 += 2 * math.pi
                else:
                    while a1 >= a0:
                        a1 -= 2 * math.pi
                n = max(2, int(abs(a1 - a0) / math.radians(arc_step_deg)))
                segs.append([(cx + r * math.cos(a0 + (a1 - a0) * i / n),
                              cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)])
        x, y = nx, ny
    # chain segments end-to-end
    pts = list(segs.pop(0))
    close = lambda a, b: math.hypot(a[0] - b[0], a[1] - b[1]) < 0.02
    while segs:
        for i, s in enumerate(segs):
            if close(s[0], pts[-1]):
                pts += s[1:]
                break
            if close(s[-1], pts[-1]):
                pts += s[::-1][1:]
                break
        else:
            raise ValueError("open outline in " + path)
        segs.pop(i)
    if close(pts[0], pts[-1]):
        pts.pop()
    return pts


BOTTOM = gerber_outline(os.path.join(HERE, "ref_bottom_outline.GML"))
TOP = gerber_outline(os.path.join(HERE, "ref_top_outline.GML"))


def prism(pts, z0, h):
    return cq.Workplane("XY").workplane(offset=z0).polyline(pts).close().extrude(h)


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def holes(body, z0, z1):
    for (hx, hy) in POGO:
        body = body.cut(cq.Workplane("XY").workplane(offset=z0).center(hx, hy).circle(POGO_HOLE / 2).extrude(z1 - z0))
    for (hx, hy) in GUIDES:
        body = body.cut(cq.Workplane("XY").workplane(offset=z0).center(hx, hy).circle(GUIDE_HOLE / 2).extrude(z1 - z0))
    return body


# ----------------------------------------------------------------- the holder
def spine_envelope(grow=0.0, z0=FRONT_T, z1=FLANGE_Z0):
    """Bottom-PCB outline restricted to |x| >= SPINE_X (optionally grown)."""
    base = prism(BOTTOM, z0, z1 - z0)
    if grow:
        # cheap offset: union of the prism shifted around a small circle
        sh = [base.translate((grow * math.cos(a), grow * math.sin(a), 0))
              for a in [i * math.pi / 4 for i in range(8)]]
        for s in sh:
            base = base.union(s)
    right = base.intersect(box(SPINE_X - grow, 9, -9, 9, z0, z1))
    left = base.intersect(box(-9, -SPINE_X + grow, -9, 9, z0, z1))
    return right.union(left)


def holder():
    body = prism(BOTTOM, 0, FRONT_T)
    body = body.union(prism(TOP, FLANGE_Z0, FLANGE_T))
    body = body.union(spine_envelope())
    body = holes(body, -1, FLANGE_Z0 + FLANGE_T + 1)
    # small lead-in chamfers on the tip face make pin insertion easier
    return body


# ---------------------------------------------------------------- depth jig
def jig():
    base_t = 2.0
    wall = 1.0
    rim_h = 1.2  # locates the flange outline
    outer = prism(TOP, 0, base_t + JIG_DEPTH + rim_h)
    sh = [outer.translate((wall * math.cos(a), wall * math.sin(a), 0)) for a in [i * math.pi / 6 for i in range(12)]]
    for s in sh:
        outer = outer.union(s)
    # flange seat pocket (top outline + 0.1 clearance), depth = rim_h
    seat = prism(TOP, base_t + JIG_DEPTH, rim_h + 1)
    for s in [seat.translate((0.1 * math.cos(a), 0.1 * math.sin(a), 0)) for a in [i * math.pi / 4 for i in range(8)]]:
        seat = seat.union(s)
    j = outer.cut(seat)
    # blind holes that the pogo tails / guide ends bottom out in
    for (hx, hy) in POGO:
        j = j.cut(cq.Workplane("XY").workplane(offset=base_t).center(hx, hy).circle(0.50).extrude(JIG_DEPTH + 0.01))
    for (hx, hy) in GUIDES:
        j = j.cut(cq.Workplane("XY").workplane(offset=base_t).center(hx, hy).circle(0.60).extrude(JIG_DEPTH + 0.01))
    # through vent in the middle so trapped CA / air can escape
    j = j.cut(cq.Workplane("XY").center(0, 0).rect(1.0, 0.6).extrude(base_t))
    return j


# ------------------------------------------------------------ modified case
def modified_case(case_stl, out_dir):
    import numpy as np
    import trimesh

    pocket = spine_envelope(grow=CASE_CLEAR,
                            z0=CASE_FRONT_Z - CASE_Z_OFFSET - 0.5,
                            z1=CASE_SLOT_Z0 - CASE_Z_OFFSET + 0.05)
    pocket = pocket.translate((0, 0, CASE_Z_OFFSET))
    tmp = os.path.join(out_dir, "_pocket.stl")
    cq.exporters.export(pocket, tmp, tolerance=0.01, angularTolerance=0.1)
    cutter = trimesh.load(tmp)
    os.remove(tmp)
    parts = trimesh.load(case_stl).split(only_watertight=False)
    outs = []
    for p in parts:
        if p.bounds[0][2] > 5:  # the two case halves (cover sleeve untouched)
            p = trimesh.boolean.difference([p, cutter], engine="manifold")
        outs.append(p)
    halves = [p for p in outs if p.bounds[0][2] > 5]
    cover = [p for p in outs if p.bounds[0][2] <= 5]
    for i, h in enumerate(sorted(halves, key=lambda m: m.bounds[0][1])):
        h.export(os.path.join(out_dir, f"case_half_{'A' if i == 0 else 'B'}_v2.stl"))
    for c in cover:
        c.export(os.path.join(out_dir, "case_cover.stl"))
    return halves


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    h = holder()
    cq.exporters.export(h, os.path.join(OUT, "TC2030_pin_holder.step"))
    cq.exporters.export(h, os.path.join(OUT, "TC2030_pin_holder.stl"), tolerance=0.005, angularTolerance=0.05)
    j = jig()
    cq.exporters.export(j, os.path.join(OUT, "TC2030_depth_jig.stl"), tolerance=0.01, angularTolerance=0.1)
    case = os.path.join(HERE, "ref_TC2030-DIY-case.stl")
    if os.path.exists(case):
        modified_case(case, OUT)
    bb = h.val().BoundingBox()
    print("holder bbox: x %.2f..%.2f  y %.2f..%.2f  z %.2f..%.2f" % (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
    print("volume %.1f mm^3" % h.val().Volume())
