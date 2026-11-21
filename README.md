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

## Ready-to-print G-code: Elegoo Neptune 3 Pro (Klipper, 0.4 mm nozzle, PETG)

| File | Contents | Time / filament |
|---|---|---|
| `print/TC2030_holders_test_PETG_N3Pro_klipper.gcode` | 6 holders + depth jig (test print first) | ~51 min / 0.50 m |
| `print/TC2030_full_set_PETG_N3Pro_klipper.gcode` | 4 holders, jig, case half A v2, case half B v2, cover | ~1 h 32 min / 1.18 m |

These files were sliced with PrusaSlicer 2.7.2 using `print/neptune3pro_klipper_petg_0.12.ini`: 0.12 mm layers, 100 % infill, Arachne walls, 3 mm brim, PETG at 240/80 °C.
Each part is labelled for Klipper `EXCLUDE_OBJECT`, so you can cancel one failed part from Mainsail/Fluidd.
The start G-code uses only standard commands plus `BED_MESH_CALIBRATE`. If your printer.cfg has a `PRINT_START` macro, swap that block for the macro.
The `.3mf` plates in `print/` open in PrusaSlicer or OrcaSlicer for re-slicing.

FDM note: on a 0.4 mm nozzle the pogo holes print at about Ø0.5 mm. Drill them to Ø0.70 (pogo) and Ø0.80 (guides) with carbide PCB drills. Drill the jig's blind holes to Ø1.0 and Ø1.2.
