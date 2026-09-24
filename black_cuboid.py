"""Create a black 30 x 30 x 15 cm cuboid for the OCP CAD Viewer."""

from pathlib import Path

import cadquery as cq
from ocp_vscode import show


# CadQuery uses millimetres: 30 cm x 30 cm footprint and 15 cm height.
WIDTH_MM = 300
DEPTH_MM = 300
HEIGHT_MM = 150
OUTPUT = Path(__file__).with_name("black_cuboid.step")

# Centered at the global origin, with height along Z.
cuboid = cq.Workplane("XY").box(WIDTH_MM, DEPTH_MM, HEIGHT_MM)

# Preserve the black part colour in the exported STEP file.
assembly = cq.Assembly(name="black_cuboid_assembly")
assembly.add(cuboid, name="black_cuboid", color=cq.Color(0, 0, 0))
assembly.save(str(OUTPUT), mode="default")

print(f"Wrote {OUTPUT}")

if __name__ == "__main__":
    show(cuboid, names=["black_cuboid"], colors=["black"])
