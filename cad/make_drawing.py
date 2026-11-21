"""Generate SVG drawing views (true scale, mm units) from the CAD geometry."""
import base64, io, json, math, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, trimesh
from tc2030_holder import BOTTOM, TOP, POGO, GUIDES, POGO_HOLE, GUIDE_HOLE, FRONT_T, FLANGE_T, FLANGE_Z0, SPINE_X, CASE_Z_OFFSET

def f(v): return f"{v:.3f}".rstrip("0").rstrip(".")
def poly(pts, cls, flip=True):
    return f'<polygon class="{cls}" points="' + " ".join(f"{f(x)},{f(-y if flip else y)}" for x, y in pts) + '"/>'
def circ(x, y, r, cls): return f'<circle class="{cls}" cx="{f(x)}" cy="{f(y)}" r="{f(r)}"/>'
def line(x1, y1, x2, y2, cls): return f'<line class="{cls}" x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}"/>'
def text(x, y, s, cls="dt", anchor="middle", rot=None):
    t = f' transform="rotate({rot} {f(x)} {f(y)})"' if rot else ""
    return f'<text class="{cls}" x="{f(x)}" y="{f(y)}" text-anchor="{anchor}"{t}>{s}</text>'
def hdim(x1, x2, y, ext_from, label, above=True):
    o = [line(x1, ext_from, x1, y + (-0.3 if above else 0.3), "ext"), line(x2, ext_from, x2, y + (-0.3 if above else 0.3), "ext"),
         f'<line class="dim" x1="{f(x1)}" y1="{f(y)}" x2="{f(x2)}" y2="{f(y)}" marker-start="url(#a)" marker-end="url(#a)"/>',
         text((x1 + x2) / 2, y - 0.25 if above else y + 0.75, label)]
    return "".join(o)
def vdim(y1, y2, x, ext_from, label, left=True):
    o = [line(ext_from, y1, x + (-0.3 if left else 0.3), y1, "ext"), line(ext_from, y2, x + (-0.3 if left else 0.3), y2, "ext"),
         f'<line class="dim" x1="{f(x)}" y1="{f(y1)}" x2="{f(x)}" y2="{f(y2)}" marker-start="url(#a)" marker-end="url(#a)"/>',
         text(x - 0.3 if left else x + 0.75, (y1 + y2) / 2, label, rot=-90)]
    return "".join(o)
def cl(x1, y1, x2, y2): return line(x1, y1, x2, y2, "cl")

def svg(vb, body, title):
    return f'<svg viewBox="{vb}" role="img" aria-label="{title}" xmlns="http://www.w3.org/2000/svg">{body}</svg>'

views = {}

# ---------- View A: tip face (front plate) ----------
b = []
b.append(poly(BOTTOM, "part"))
for x, y in POGO: b.append(circ(x, -y, POGO_HOLE / 2, "hole"))
for x, y in GUIDES: b.append(circ(x, -y, GUIDE_HOLE / 2, "hole g"))
b.append(cl(-4.4, 0, 4.6, 0)); 
for x in (-1.27, 0, 1.27): b.append(cl(x, -2.4, x, 2.4))
b.append(cl(-2.54, -1.0, -2.54, 1.0)); b.append(cl(2.54, -2.0, 2.54, 2.0))
xs = [p[0] for p in BOTTOM]; ys = [p[1] for p in BOTTOM]
b.append(hdim(min(xs), max(xs), 3.4, 0, f"{max(xs)-min(xs):.2f}"))
b.append(hdim(-1.27, 0, -2.6 + 0, -0.6, "1.27", above=True).replace('y1="-2.6"', 'y1="-2.6"'))
b.append(hdim(-2.54, 2.54, 2.55, 0.4, "5.08"))
b.append(vdim(-max(ys), max(ys), min(xs) - 0.9, min(xs) + 0.6, f"{2*max(ys):.2f}"))
b.append(vdim(-1.016, 1.016, 4.45, 2.94, "2.032", left=False))
b.append(vdim(-0.635, 0.635, -0.45, -1.0, "1.27", left=True).replace('x1="-0.45"', 'x1="-0.45"'))
views["tip"] = svg("-5.6 -3.9 11.4 8.0", "".join(b), "Tip face view")

# ---------- View B: rear flange ----------
b = [poly(TOP, "part")]
for x, y in POGO: b.append(circ(x, -y, POGO_HOLE / 2, "hole"))
for x, y in GUIDES: b.append(circ(x, -y, GUIDE_HOLE / 2, "hole g"))
# spine footprints dashed behind
b.append(cl(-5, 0, 5.2, 0))
xs = [p[0] for p in TOP]; ys = [p[1] for p in TOP]
b.append(hdim(min(xs), max(xs), -3.6, -1.7, f"{max(xs)-min(xs):.2f}"))
b.append(vdim(-max(ys), max(ys), min(xs) - 0.7, -0.5, f"{2*max(ys):.2f}"))
b.append(hdim(-1.87, 1.87, 3.55, 2.7, "3.74 notch"))
b.append(vdim(1.56, 2.655, 5.25, 1.6, "1.10", left=False))
b.append(text(0, 0.95 + 1.9, "wire notch", "note"))
b.append(text(0, -2.05, "wire notch", "note"))
views["flange"] = svg("-6.0 -4.6 12.6 9.0", "".join(b), "Rear flange view")

# ---------- View C: side view (looking along Y), X horizontal, Z down the page ----------
# Z axis vertical: tip face at top (z=0) — probe tips point up the page
def zx(z): return z  # svg y = z
b = []
bx = [p[0] for p in BOTTOM]; tx = [p[0] for p in TOP]
# pins (phantom, behind)
for x in (-1.27, 0, 1.27):
    b.append(f'<rect class="pogo" x="{f(x-0.34)}" y="{f(-3.0)}" width="0.68" height="{f(11.7+3.0)}"/>')
    b.append(f'<rect class="plunger" x="{f(x-0.24)}" y="{f(-4.85)}" width="0.48" height="1.85"/>')
for x in (-2.54, 2.54):
    b.append(f'<rect class="guide" x="{f(x-0.4)}" y="{f(-6.0)}" width="0.8" height="{f(17.7)}" rx="0.3"/>')
# part
b.append(f'<rect class="part" x="{f(min(bx))}" y="0" width="{f(max(bx)-min(bx))}" height="{f(FRONT_T)}"/>')
b.append(f'<rect class="part" x="{f(min(tx))}" y="{f(FLANGE_Z0)}" width="{f(max(tx)-min(tx))}" height="{f(FLANGE_T)}"/>')
b.append(f'<rect class="part" x="{f(min(bx))}" y="{f(FRONT_T)}" width="{f(-SPINE_X-min(bx))}" height="{f(FLANGE_Z0-FRONT_T)}"/>')
b.append(f'<rect class="part" x="{f(SPINE_X)}" y="{f(FRONT_T)}" width="{f(max(bx)-SPINE_X)}" height="{f(FLANGE_Z0-FRONT_T)}"/>')
# hidden guide holes in spines
for x in (-2.54, 2.54):
    b.append(line(x - 0.4, 0, x - 0.4, 10.2, "hid")); b.append(line(x + 0.4, 0, x + 0.4, 10.2, "hid"))
# solder zone
b.append(f'<rect class="zone" x="{f(-SPINE_X)}" y="{f(FRONT_T+0.6)}" width="{f(2*SPINE_X)}" height="2.6"/>')
b.append(text(0, FRONT_T + 2.1, "solder", "note")); b.append(text(0, FRONT_T + 2.75, "zone", "note"))
# case front line
cz = 10.6 - CASE_Z_OFFSET
b.append(line(-6.5, cz, 6.5, cz, "case")); b.append(text(6.5, cz - 0.25, "case front", "note", anchor="end"))
# dims (right side)
R = 5.6
b.append(vdim(0, FRONT_T, R, max(bx) + 0.2, "1.6", left=False))
b.append(vdim(FRONT_T, FLANGE_Z0, R, max(bx) + 0.2, "7.4", left=False))
b.append(vdim(FLANGE_Z0, FLANGE_Z0 + FLANGE_T, R, max(tx) + 0.2, "1.2", left=False))
b.append(vdim(0, FLANGE_Z0 + FLANGE_T, R + 1.5, max(tx) + 0.2, "10.2", left=False))
b.append(vdim(FLANGE_Z0 + FLANGE_T, 11.7, R, 3.0, "1.5", left=False))
# dims left side: pin protrusion
L = -5.4
b.append(vdim(-6.0, 0, L, -2.94, "6.0", left=True))
b.append(vdim(-4.85, 0, L + 1.3, -1.6, "4.85", left=True))
b.append(hdim(-SPINE_X, SPINE_X, 12.6, 9.0, "3.80 window", above=False))
views["side"] = svg("-7.4 -7.0 16.4 21.0", "".join(b), "Side view")

# ---------- View D: section through x=0 (looking along X) — Y horizontal ----------
b = []
by = max(p[1] for p in BOTTOM)
# at x=0 the flange is notched to |y|<=1.56
b.append(f'<rect class="cut" x="{f(-by)}" y="0" width="{f(2*by)}" height="{f(FRONT_T)}"/>')
b.append(f'<rect class="cut" x="-1.56" y="{f(FLANGE_Z0)}" width="3.12" height="{f(FLANGE_T)}"/>')
# spine beyond (seen in background)
b.append(f'<rect class="beyond" x="{f(-by)}" y="{f(FRONT_T)}" width="{f(2*by)}" height="{f(FLANGE_Z0-FRONT_T)}"/>')
for y in (-0.635, 0.635):
    b.append(f'<rect class="pogo" x="{f(y-0.34)}" y="-3.0" width="0.68" height="14.7"/>')
    b.append(f'<rect class="plunger" x="{f(y-0.24)}" y="-4.85" width="0.48" height="1.85"/>')
# wires to the two rows
for s in (-1, 1):
    y = s * 0.635
    path = f'M{f(y+s*0.34)},{f(3.4)} C{f(s*1.6)},{f(3.6)} {f(s*2.1)},{f(5.5)} {f(s*2.1)},{f(8.5)} L{f(s*2.1)},{f(14.0)}'
    b.append(f'<path class="wire" d="{path}"/>')
b.append(text(2.9, 13.4, "wire", "note", anchor="start"))
b.append(hdim(-by, by, -0.9, 0, f"{2*by:.2f}", above=True).replace('y1="-0.9"', 'y1="-0.9"') if False else "")
b.append(vdim(0, FRONT_T, -3.1, -by, "1.6"))
b.append(vdim(FLANGE_Z0, FLANGE_Z0 + FLANGE_T, -3.1, -1.56, "1.2"))
b.append(text(0, 7.6, "open both sides", "note"))
views["section"] = svg("-4.6 -6.0 9.6 20.6", "".join(b), "Section A-A")

# ---------- View E: fit in case (side view, case section at y=0.3) ----------
b = []
case = [m for m in trimesh.load(os.path.join(os.path.dirname(__file__), "..", "output", "case_half_B_v2.stl")).split(only_watertight=False)]
orig = [m for m in trimesh.load(os.path.join(os.path.dirname(__file__), "ref_TC2030-DIY-case.stl")).split(only_watertight=False) if m.bounds[0][2] > 5 and m.bounds[1][1] > 3]
def section_paths(mesh, cls, yplane=0.3):
    s = mesh.section(plane_origin=[0, yplane, 0], plane_normal=[0, 1, 0])
    out = []
    for e in s.discrete:
        pts = " ".join(f"{f(p[0])},{f(p[2]-CASE_Z_OFFSET)}" for p in e)
        out.append(f'<polyline class="{cls}" clip-path="url(#fitclip)" points="{pts}"/>')
    return out
b += section_paths(orig[0], "orig")
b += section_paths(case[0], "casecut")
# holder side silhouette
b.append(f'<rect class="part" x="{f(min(bx))}" y="0" width="{f(max(bx)-min(bx))}" height="{f(FRONT_T)}"/>')
b.append(f'<rect class="part" x="{f(min(tx))}" y="{f(FLANGE_Z0)}" width="{f(max(tx)-min(tx))}" height="{f(FLANGE_T)}"/>')
b.append(f'<rect class="part" x="{f(min(bx))}" y="{f(FRONT_T)}" width="{f(-SPINE_X-min(bx))}" height="{f(FLANGE_Z0-FRONT_T)}"/>')
b.append(f'<rect class="part" x="{f(SPINE_X)}" y="{f(FRONT_T)}" width="{f(max(bx)-SPINE_X)}" height="{f(FLANGE_Z0-FRONT_T)}"/>')
for x in (-2.54, 2.54):
    b.append(f'<rect class="guide" x="{f(x-0.4)}" y="-6" width="0.8" height="17.7" rx="0.3"/>')
b.append(text(-6.2, 12.4, "flange in original slot", "note", anchor="start"))
b.append(text(-6.2, 7.4, "pocket widened", "note", anchor="start"))
b.append(text(-6.2, 8.1, "(z 10.6–13.65)", "note", anchor="start"))
views["fit"] = svg("-6.6 -7.0 13.2 22.5", "".join(b), "Fit in case")

# renders
def b64(p):
    return "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode()
imgs = {k: b64(f"output/render_{k}.png") for k in ("holder_iso", "holder_back", "assembly")}
json.dump({"views": views, "imgs": imgs}, open("output/_drawing_parts.json", "w"))
print({k: len(v) for k, v in views.items()}, {k: len(v) // 1024 for k, v in imgs.items()})
