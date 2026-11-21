# TC2030 one-piece 3D-printed pin holder (draft)

A redesign of [afedorov3/Tag-Connect-DIY](https://github.com/afedorov3/Tag-Connect-DIY) (CC0).
The top and bottom PCBs are merged into **one 3D-printed holder**:

- front plate: the original bottom-PCB outline, 1.6 mm thick
- rear flange: the original top-PCB outline, 1.2 mm thick, so it fits the case slot
- two side spines around the guide pins; the long sides stay open so wires can be soldered to the pogo barrels

| File | Purpose |
|---|---|
| `output/TC2030_pin_holder.stl` / `.step` | Holder (print tip face down, resin recommended) |
| `output/TC2030_depth_jig.stl` | Sets pogo tails and guide ends 1.5 mm behind the flange |
| `output/case_half_A_v2.stl`, `case_half_B_v2.stl` | Original case halves with the entry pocket widened for the spines |
| `output/case_cover.stl` | Original cover, unchanged |
| `output/TC2030_pin_holder_drawing.html` | Draft drawing |
| `cad/tc2030_holder.py` | Parametric CadQuery source (`pip install cadquery trimesh manifold3d`) |

Pogo holes are Ø0.70 and guide holes Ø0.80. Ream them after printing.
