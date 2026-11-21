"""Shaded renders of the holder / assembly (matplotlib, no GPU needed)."""
import sys, numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def cyl(r, z0, z1, x, y, color):
    m = trimesh.creation.cylinder(radius=r, height=z1-z0, sections=24)
    m.apply_translation([x, y, (z0+z1)/2]); return (m, color)

def draw(items, out, elev, azim, light=(0.4,-0.6,0.7), size=(6,4.5), lim=None):
    fig = plt.figure(figsize=size, dpi=200); ax = fig.add_subplot(111, projection="3d")
    L = np.array(light); L = L/np.linalg.norm(L)
    allv = []
    for m, col in items:
        tri = m.vertices[m.faces]; n = m.face_normals
        s = 0.35 + 0.65*np.clip(n@L, 0, 1)
        c = np.array(matplotlib.colors.to_rgb(col))
        fc = np.clip(c[None,:]*s[:,None], 0, 1)
        pc = Poly3DCollection(tri, facecolors=fc, edgecolors="none", linewidths=0)
        ax.add_collection3d(pc); allv.append(m.vertices)
    V = np.vstack(allv); c = (V.max(0)+V.min(0))/2; r = (V.max(0)-V.min(0)).max()/2*(lim or 0.75)
    ax.set_xlim(c[0]-r,c[0]+r); ax.set_ylim(c[1]-r,c[1]+r); ax.set_zlim(c[2]-r,c[2]+r)
    ax.set_box_aspect((1,1,1)); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()
    fig.patch.set_alpha(0); plt.subplots_adjust(0,0,1,1); fig.savefig(out, transparent=True); plt.close(fig)

H = trimesh.load("output/TC2030_pin_holder.stl")
PINK = "#e7488f"
# holder alone, two views (Z = pin axis drawn vertical: tip face down)
draw([(H, PINK)], "output/render_holder_iso.png", 22, -58)
draw([(H, PINK)], "output/render_holder_back.png", -28, 125)
# assembly: pogo (gold), guides (steel)
pogo = [cyl(0.34, 1.7-0.0, 11.7, x, y, "#d4a72c") for x,y in [(x*1.27, s*0.635) for s in (-1,1) for x in (-1,0,1)]]
plung = [cyl(0.24, -4.85, 1.0, x, y, "#c9c9c9") for x,y in [(x*1.27, s*0.635) for s in (-1,1) for x in (-1,0,1)]]
pogo = [cyl(0.34, -3.0, 11.7, x, y, "#d4a72c") for x,y in [(x*1.27, s*0.635) for s in (-1,1) for x in (-1,0,1)]]
guides = [cyl(0.4, -6.0, 11.7, x, y, "#8c96a3") for x,y in [(-2.54,0),(2.54,-1.016),(2.54,1.016)]]
draw([(H, PINK)]+pogo+plung+guides, "output/render_assembly.png", 20, -60, lim=0.62)
# holder in case half B (y>=0 half) to show fit
C = trimesh.load("output/case_half_A_v2.stl"); C.apply_translation([0,0,-4.65])
draw([(C, "#e8e8e8"), (H, PINK)]+pogo+plung+guides, "output/render_in_case.png", 35, -35, lim=0.62, size=(7,5))
