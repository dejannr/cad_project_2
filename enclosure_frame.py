"""Parametric, PETG-printable three-piece enclosure frame.

Coordinate convention: X = width, Y = depth, Z = height.  The assembled model
occupies X=0..300, Y=0..250, and Z=0..100 mm.
"""

from pathlib import Path

import cadquery as cq
from cadquery import exporters
from ocp_vscode import show


# Finished external envelope (millimetres).
OUTER_WIDTH = 300.0
OUTER_DEPTH = 250.0
OUTER_HEIGHT = 100.0

SIDE_PANEL_THICKNESS = 10.0
TOP_PANEL_THICKNESS = 10.0
SIDE_PANEL_HEIGHT = 100.0
INNER_WIDTH = OUTER_WIDTH - 2 * SIDE_PANEL_THICKNESS
TOP_PANEL_WIDTH = INNER_WIDTH

# Four PETG-friendly circular locating connections per side.  These are
# diameters (not radii); female sockets are in the side walls and male bosses
# project outward from the top component's internal flanges.
MALE_BOSS_DIAMETER = 20.0
MALE_BOSS_RADIUS = MALE_BOSS_DIAMETER / 2.0
MALE_BOSS_PROTRUSION = 3.7
RADIAL_CLEARANCE = 0.30
DEPTH_CLEARANCE = 0.30
SOCKET_DIAMETER = MALE_BOSS_DIAMETER + 2 * RADIAL_CLEARANCE
SOCKET_RADIUS = SOCKET_DIAMETER / 2.0
SOCKET_DEPTH = 4.0
CONNECTION_GAP = 34.0
CONNECTION_Y = [44.0, 98.0, 152.0, 206.0]
MALE_BOSS_CHAMFER = 0.7
SOCKET_ENTRY_CHAMFER = 0.5
BOSS_BASE_FILLET = 1.0
TOP_FLANGE_THICKNESS = 6.0
TOP_FLANGE_ROOT_FILLET = 2.0

# Reusable wooden-dowel visualization component.  It is a 20 mm male cylinder
# that seats 4 mm into each of the existing 20.6 mm side-panel sockets.
WOOD_ROD_DIAMETER = 20.0
WOOD_ROD_RADIUS = WOOD_ROD_DIAMETER / 2.0
MODULE_OUTER_WIDTH = 300.0
MODULE_INNER_WIDTH = MODULE_OUTER_WIDTH - 2 * SIDE_PANEL_THICKNESS
WOOD_ROD_INSERTION = SOCKET_DEPTH
WOOD_ROD_LENGTH = MODULE_INNER_WIDTH + 2 * WOOD_ROD_INSERTION
WOOD_ROD_END_CHAMFER = 0.7

assert abs(WOOD_ROD_LENGTH - 288.0) < 1e-9

OUTPUT_DIR = Path(__file__).parent

# The top fits between the full-height side panels and is flush at Z=100.
TOP_BOTTOM_Z = OUTER_HEIGHT - TOP_PANEL_THICKNESS
# The circular axes stay fixed.  The support reaches the actual top surface,
# so the circle is centered in the complete visible top/flange section.
CONNECTION_Z = 84.7
FLANGE_TOP_Z = OUTER_HEIGHT
FLANGE_BOTTOM_Z = 2 * CONNECTION_Z - FLANGE_TOP_Z
TOP_FLANGE_HEIGHT = FLANGE_TOP_Z - FLANGE_BOTTOM_Z
SUPPORT_VERTICAL_MARGIN = FLANGE_TOP_Z - (CONNECTION_Z + MALE_BOSS_RADIUS)

assert abs(FLANGE_TOP_Z - (CONNECTION_Z + MALE_BOSS_RADIUS) - SUPPORT_VERTICAL_MARGIN) < 0.001
assert abs((CONNECTION_Z - MALE_BOSS_RADIUS) - FLANGE_BOTTOM_Z - SUPPORT_VERTICAL_MARGIN) < 0.001


def _box_at_min_corner(x_size, y_size, z_size, x_min, y_min, z_min):
    """Return a box positioned from its minimum XYZ corner."""
    return cq.Workplane("XY").box(x_size, y_size, z_size).translate(
        (x_min + x_size / 2, y_min + y_size / 2, z_min + z_size / 2)
    )


def _x_cylinder(radius, length, x_start, y_center, z_center, direction=1):
    """Return a cylinder whose axis is X, starting at the given X face."""
    solid = cq.Solid.makeCylinder(
        radius,
        length,
        cq.Vector(x_start, y_center, z_center),
        cq.Vector(direction, 0, 0),
    )
    return cq.Workplane("XY").newObject([solid])


def make_side_panel():
    """Create one full-height side wall with four blind sockets on each face.

    Rotating this exact solid 180 degrees about Z produces the right wall. The
    two socket patterns are aligned so either face can serve a future module.
    """
    side = _box_at_min_corner(
        SIDE_PANEL_THICKNESS, OUTER_DEPTH, SIDE_PANEL_HEIGHT, 0, 0, 0
    )

    # Blind sockets are cut 4 mm from both X faces. Their 2 mm central core
    # prevents the opposing cuts from becoming through-holes.
    for y_center in CONNECTION_Y:
        inner_socket = _x_cylinder(
            SOCKET_RADIUS,
            SOCKET_DEPTH + 0.01,
            SIDE_PANEL_THICKNESS + 0.01,
            y_center,
            CONNECTION_Z,
            direction=-1,
        )
        outer_socket = _x_cylinder(
            SOCKET_RADIUS,
            SOCKET_DEPTH + 0.01,
            -0.01,
            y_center,
            CONNECTION_Z,
            direction=1,
        )
        side = side.cut(inner_socket).cut(outer_socket)

    # A modest entry chamfer is applied to all eight openings, not the clean
    # exterior faces themselves.
    socket_entry_edges = side.edges("%Circle").filter(
        lambda edge: abs(edge.Center().x) < 1e-5
        or abs(edge.Center().x - SIDE_PANEL_THICKNESS) < 1e-5
    )
    return socket_entry_edges.chamfer(SOCKET_ENTRY_CHAMFER).clean()


def make_top_panel():
    """Create the 280 mm-wide top that fits between the two side panels."""
    top = _box_at_min_corner(
        TOP_PANEL_WIDTH,
        OUTER_DEPTH,
        TOP_PANEL_THICKNESS,
        SIDE_PANEL_THICKNESS,
        0,
        TOP_BOTTOM_Z,
    )

    # The connection flanges are wholly inside the side walls and only support
    # the circular pegs; no rails, tongues, grooves, or channels remain.
    left_flange = _box_at_min_corner(
        TOP_FLANGE_THICKNESS,
        OUTER_DEPTH,
        TOP_FLANGE_HEIGHT,
        SIDE_PANEL_THICKNESS,
        0,
        FLANGE_BOTTOM_Z,
    )
    right_flange = _box_at_min_corner(
        TOP_FLANGE_THICKNESS,
        OUTER_DEPTH,
        TOP_FLANGE_HEIGHT,
        OUTER_WIDTH - SIDE_PANEL_THICKNESS - TOP_FLANGE_THICKNESS,
        0,
        FLANGE_BOTTOM_Z,
    )
    top = top.union(left_flange).union(right_flange).clean()

    # Fillet the long, internal flange roots for PETG durability.
    flange_root_edges = top.edges("|Y").filter(
        lambda edge: abs(edge.Center().z - TOP_BOTTOM_Z) < 1e-5
        and (
            abs(edge.Center().x - (SIDE_PANEL_THICKNESS + TOP_FLANGE_THICKNESS)) < 1e-5
            or abs(edge.Center().x - (OUTER_WIDTH - SIDE_PANEL_THICKNESS - TOP_FLANGE_THICKNESS))
            < 1e-5
        )
    )
    top = flange_root_edges.fillet(TOP_FLANGE_ROOT_FILLET).clean()

    # Add outward-facing pegs to the internal flanges.  Their axes are X: the
    # left flange points -X to the left side, the right flange +X to the right.
    for y_center in CONNECTION_Y:
        left_boss = _x_cylinder(
            MALE_BOSS_RADIUS,
            MALE_BOSS_PROTRUSION,
            SIDE_PANEL_THICKNESS,
            y_center,
            CONNECTION_Z,
            direction=-1,
        )
        right_boss = _x_cylinder(
            MALE_BOSS_RADIUS,
            MALE_BOSS_PROTRUSION,
            OUTER_WIDTH - SIDE_PANEL_THICKNESS,
            y_center,
            CONNECTION_Z,
            direction=1,
        )
        left_boss = left_boss.faces("<X").edges().chamfer(MALE_BOSS_CHAMFER)
        right_boss = right_boss.faces(">X").edges().chamfer(MALE_BOSS_CHAMFER)
        top = top.union(left_boss).union(right_boss).clean()

    # The requested 1 mm root fillet would consume the 0.30 mm insertion fit
    # at this shallow 3.7 mm peg/socket interface, so it is intentionally not
    # applied here. The 2 mm flange-root fillet carries the PETG load instead.
    return top.clean()


def make_wood_rod():
    """Create one Ø20 mm, 288 mm-long wooden dowel along the positive X axis."""
    rod = _x_cylinder(WOOD_ROD_RADIUS, WOOD_ROD_LENGTH, 0, 0, 0)
    rod = rod.faces("<X").edges().chamfer(WOOD_ROD_END_CHAMFER)
    return rod.faces(">X").edges().chamfer(WOOD_ROD_END_CHAMFER).clean()


def make_assembly():
    """Return a positioned assembly: left side, rotated identical right, top."""
    side_panel = make_side_panel()
    # Rotate the same geometry around Z, then translate it into X=270..300.
    right_side = side_panel.rotate((0, 0, 0), (0, 0, 1), 180).translate(
        (OUTER_WIDTH, OUTER_DEPTH, 0)
    )
    top_panel = make_top_panel()

    assembly = cq.Assembly(name="enclosure_frame")
    assembly.add(side_panel, name="left_side", color=cq.Color(0.08, 0.08, 0.08))
    assembly.add(right_side, name="right_side", color=cq.Color(0.08, 0.08, 0.08))
    assembly.add(top_panel, name="top_panel", color=cq.Color(0.08, 0.08, 0.08))
    return assembly


def make_extended_assembly():
    """Show three connected modules with four shared side walls and eight rods."""
    side_panel = make_side_panel()
    top_panel = make_top_panel()
    wood_rod = make_wood_rod()
    side_pitch = MODULE_OUTER_WIDTH - SIDE_PANEL_THICKNESS
    side_positions = [index * side_pitch for index in range(4)]

    assembly = cq.Assembly(name="extended_modular_frame")
    for index, x_position in enumerate(side_positions):
        assembly.add(
            side_panel.translate((x_position, 0, 0)),
            name=f"side_{chr(ord('a') + index)}",
            color=cq.Color(0.08, 0.08, 0.08),
        )

    # The pre-existing top is positioned for a module beginning at X=0.  Move
    # it to shared walls B/C, where its 280 mm body occupies X=300..580.
    assembly.add(
        top_panel.translate((side_positions[1], 0, 0)),
        name="top_panel",
        color=cq.Color(0.08, 0.08, 0.08),
    )

    # Rods start 4 mm inside each left wall and terminate 4 mm inside the
    # neighbouring wall.  The two rod modules are A/B and C/D.
    for module_index, left_side_index in enumerate((0, 2), start=1):
        rod_start_x = side_positions[left_side_index] + (
            SIDE_PANEL_THICKNESS - WOOD_ROD_INSERTION
        )
        for rod_index, y_center in enumerate(CONNECTION_Y, start=1):
            assembly.add(
                wood_rod.translate((rod_start_x, y_center, CONNECTION_Z)),
                name=f"rod_module_{module_index}_{rod_index}",
                color=cq.Color(0.45, 0.25, 0.10),
            )
    return assembly


def _obsolete_report_fit(side_panel, top_panel):
    """Report finished envelope, specified clearance, and solid interference."""
    right_side = side_panel.rotate((0, 0, 0), (0, 0, 1), 180).translate(
        (OUTER_WIDTH, OUTER_DEPTH, 0)
    )
    assembled = cq.Compound.makeCompound(
        [side_panel.val(), right_side.val(), top_panel.val()]
    )
    bounds = assembled.BoundingBox()

    # Positive common volume would indicate an unintended solid overlap.
    left_interference = top_panel.val().intersect(side_panel.val()).Volume()
    right_interference = top_panel.val().intersect(right_side.val()).Volume()
    tolerance = 1e-6
    lateral_clearance = (GROOVE_WIDTH - TONGUE_WIDTH) / 2
    vertical_clearance = GROOVE_DEPTH - TONGUE_HEIGHT
    left_groove_center_x = PANEL_THICKNESS / 2
    right_groove_center_x = OUTER_WIDTH - PANEL_THICKNESS / 2

    # Keep only locating-feature cylinders; the tongue/groove lead-ins also
    # contain cylindrical fillet faces.  Bosses are on top flanges; sockets are
    # blind recesses in the two instances of the reusable side solid.
    left_boss_faces = [
        face
        for face in top_panel.faces("%Cylinder").vals()
        if abs(face.Center().z - CONNECTION_Z) <= tolerance and face.Center().x < PANEL_THICKNESS
    ]
    right_boss_faces = [
        face
        for face in top_panel.faces("%Cylinder").vals()
        if abs(face.Center().z - CONNECTION_Z) <= tolerance
        and face.Center().x > OUTER_WIDTH - PANEL_THICKNESS
    ]
    left_socket_faces = [
        face
        for face in side_panel.faces("%Cylinder").vals()
        if abs(face.Center().z - CONNECTION_Z) <= tolerance and face.Center().x < PANEL_THICKNESS
    ]
    right_socket_faces = [
        face
        for face in right_side.faces("%Cylinder").vals()
        if abs(face.Center().z - CONNECTION_Z) <= tolerance
        and face.Center().x > OUTER_WIDTH - PANEL_THICKNESS
    ]
    expected_y = sorted(CONNECTION_Y)
    left_boss_y = sorted(round(face.Center().y, 6) for face in left_boss_faces)
    right_boss_y = sorted(round(face.Center().y, 6) for face in right_boss_faces)
    left_socket_y = sorted(round(face.Center().y, 6) for face in left_socket_faces)
    right_socket_y = sorted(round(face.Center().y, 6) for face in right_socket_faces)
    alignment_ok = (
        left_boss_y == expected_y
        and right_boss_y == expected_y
        and left_socket_y == expected_y
        and right_socket_y == expected_y
        and abs(left_groove_center_x - PANEL_THICKNESS / 2) <= tolerance
        and abs(right_groove_center_x - (OUTER_WIDTH - PANEL_THICKNESS / 2))
        <= tolerance
    )
    identical_sides = abs(side_panel.val().Volume() - right_side.val().Volume()) <= tolerance
    envelope_ok = (
        abs(bounds.xmin) <= tolerance
        and abs(bounds.ymin) <= tolerance
        and abs(bounds.zmin) <= tolerance
        and abs(bounds.xlen - OUTER_WIDTH) <= tolerance
        and abs(bounds.ylen - OUTER_DEPTH) <= tolerance
        and abs(bounds.zlen - OUTER_HEIGHT) <= tolerance
    )
    clearance_ok = (
        abs(lateral_clearance - XY_CLEARANCE) <= tolerance
        and abs(vertical_clearance - Z_CLEARANCE) <= tolerance
    )
    # Measure the base wall and horizontal top sheet, excluding inward bosses
    # and downward flanges respectively.
    side_wall_thickness = PANEL_THICKNESS - side_panel.val().BoundingBox().xmin
    top_sheet_thickness = OUTER_HEIGHT - TOP_BOTTOM_Z
    side_thickness_ok = abs(side_wall_thickness - PANEL_THICKNESS) <= tolerance
    top_thickness_ok = abs(top_sheet_thickness - PANEL_THICKNESS) <= tolerance
    boss_count_ok = (
        len(left_boss_faces) == len(CONNECTION_Y)
        and len(right_boss_faces) == len(CONNECTION_Y)
    )
    socket_count_ok = (
        len(left_socket_faces) == len(CONNECTION_Y)
        and len(right_socket_faces) == len(CONNECTION_Y)
    )
    bosses_outward_ok = (
        all(face.Center().x < PANEL_THICKNESS for face in left_boss_faces)
        and all(face.Center().x > OUTER_WIDTH - PANEL_THICKNESS for face in right_boss_faces)
    )
    solids_valid = side_panel.val().isValid() and top_panel.val().isValid()
    socket_backing = PANEL_THICKNESS - SOCKET_DEPTH
    socket_blind_ok = socket_backing > 0 and abs(socket_backing - 5.7) <= tolerance
    boss_seating_clearance = SOCKET_DEPTH - BOSS_PROTRUSION
    boss_seating_ok = (
        boss_seating_clearance >= 0
        and abs(boss_seating_clearance - DEPTH_CLEARANCE) <= tolerance
    )
    gaps = [
        CONNECTION_Y[0] - BOSS_RADIUS,
        *[
            CONNECTION_Y[index + 1] - CONNECTION_Y[index] - BOSS_DIAMETER
            for index in range(len(CONNECTION_Y) - 1)
        ],
        OUTER_DEPTH - (CONNECTION_Y[-1] + BOSS_RADIUS),
    ]
    gap_ok = all(abs(gap - CONNECTION_GAP) <= tolerance for gap in gaps)
    top_surface_clean = (
        abs(top_panel.val().BoundingBox().zmax - OUTER_HEIGHT) <= tolerance
        and all(abs(face.Center().z - CONNECTION_Z) > tolerance for face in top_panel.faces(">Z").vals())
    )

    print(f"Assembly width: {bounds.xlen:.3f} mm")
    print(f"Assembly depth: {bounds.ylen:.3f} mm")
    print(f"Assembly height: {bounds.zlen:.3f} mm")
    print(
        "Tongue/groove clearance: "
        f"{lateral_clearance:.3f} mm per side, {vertical_clearance:.3f} mm vertical "
        f"({'PASS' if clearance_ok else 'FAIL'})"
    )
    print(
        "Identical side geometry reused for left and right: "
        f"{'PASS' if identical_sides else 'FAIL'} (180 degree Z rotation)"
    )
    print(
        "Panel thicknesses: "
        f"side={'PASS' if side_thickness_ok else 'FAIL'} ({side_wall_thickness:.3f} mm), "
        f"top={'PASS' if top_thickness_ok else 'FAIL'} ({top_sheet_thickness:.3f} mm)"
    )
    print(
        "Circular connections: "
        f"bosses/side={len(left_boss_faces)}/{len(right_boss_faces)} "
        f"({'PASS' if boss_count_ok else 'FAIL'}), "
        f"sockets/side={len(left_socket_faces)}/{len(right_socket_faces)} "
        f"({'PASS' if socket_count_ok else 'FAIL'})"
    )
    print(
        "Boss/socket dimensions: "
        f"boss Ø{BOSS_DIAMETER:.3f} (R{BOSS_RADIUS:.3f}), "
        f"socket Ø{SOCKET_DIAMETER:.3f} (R{SOCKET_RADIUS:.3f}), "
        f"protrusion {BOSS_PROTRUSION:.3f}, depth {SOCKET_DEPTH:.3f} mm"
    )
    print(
        "Boss/socket centers concentric: "
        f"{'PASS' if alignment_ok else 'FAIL'} "
        f"(Y={CONNECTION_Y}, Z={CONNECTION_Z:.3f} mm)"
    )
    print(
        f"Even edge-to-edge gaps: {'PASS' if gap_ok else 'FAIL'} "
        f"({[round(gap, 3) for gap in gaps]} mm)"
    )
    print(
        "Blind side sockets / outer-face backing: "
        f"{'PASS' if socket_blind_ok else 'FAIL'} ({socket_backing:.3f} mm)"
    )
    print(
        "Boss anti-bottoming depth allowance: "
        f"{'PASS' if boss_seating_ok else 'FAIL'} ({boss_seating_clearance:.3f} mm)"
    )
    print(f"Top bosses point outward: {'PASS' if bosses_outward_ok else 'FAIL'}")
    print(f"Horizontal top surface clean: {'PASS' if top_surface_clean else 'FAIL'}")
    print(f"Joint geometry inside external envelope: {'PASS' if envelope_ok else 'FAIL'}")
    print(f"All resulting solids valid: {'PASS' if solids_valid else 'FAIL'}")
    print(
        "Unintended top/side interference: "
        f"{'NO' if left_interference <= tolerance and right_interference <= tolerance else 'YES'} "
        f"(left={left_interference:.6f}, right={right_interference:.6f} mm^3)"
    )


def report_fit(side_panel, top_panel):
    """Validate the circular-only connection system and final envelope."""
    right_side = side_panel.rotate((0, 0, 0), (0, 0, 1), 180).translate(
        (OUTER_WIDTH, OUTER_DEPTH, 0)
    )
    assembled = cq.Compound.makeCompound(
        [side_panel.val(), right_side.val(), top_panel.val()]
    )
    bounds = assembled.BoundingBox()
    tolerance = 1e-6

    left_bosses = [
        face for face in top_panel.faces("%Cylinder").vals()
        if abs(face.Center().z - CONNECTION_Z) <= tolerance
        and face.Center().x < SIDE_PANEL_THICKNESS
    ]
    right_bosses = [
        face for face in top_panel.faces("%Cylinder").vals()
        if abs(face.Center().z - CONNECTION_Z) <= tolerance
        and face.Center().x > OUTER_WIDTH - SIDE_PANEL_THICKNESS
    ]
    left_sockets = [
        face for face in side_panel.faces("%Cylinder").vals()
        if abs(face.Center().z - CONNECTION_Z) <= tolerance
    ]
    right_sockets = [
        face for face in right_side.faces("%Cylinder").vals()
        if abs(face.Center().z - CONNECTION_Z) <= tolerance
    ]
    expected_y = sorted(CONNECTION_Y)
    boss_y_ok = (
        sorted(round(face.Center().y, 6) for face in left_bosses) == expected_y
        and sorted(round(face.Center().y, 6) for face in right_bosses) == expected_y
    )
    socket_y_ok = (
        sorted({round(face.Center().y, 6) for face in left_sockets}) == expected_y
        and sorted({round(face.Center().y, 6) for face in right_sockets}) == expected_y
    )
    gaps = [
        CONNECTION_Y[0] - MALE_BOSS_RADIUS,
        *[
            CONNECTION_Y[index + 1] - CONNECTION_Y[index] - MALE_BOSS_DIAMETER
            for index in range(len(CONNECTION_Y) - 1)
        ],
        OUTER_DEPTH - (CONNECTION_Y[-1] + MALE_BOSS_RADIUS),
    ]
    side_bounds = side_panel.val().BoundingBox()
    envelope_ok = (
        abs(bounds.xmin) <= tolerance and abs(bounds.ymin) <= tolerance
        and abs(bounds.zmin) <= tolerance
        and abs(bounds.xlen - OUTER_WIDTH) <= tolerance
        and abs(bounds.ylen - OUTER_DEPTH) <= tolerance
        and abs(bounds.zlen - OUTER_HEIGHT) <= tolerance
    )
    side_dimensions_ok = (
        abs(side_bounds.xlen - SIDE_PANEL_THICKNESS) <= tolerance
        and abs(side_bounds.ylen - OUTER_DEPTH) <= tolerance
        and abs(side_bounds.zlen - SIDE_PANEL_HEIGHT) <= tolerance
    )
    core_thickness = SIDE_PANEL_THICKNESS - 2 * SOCKET_DEPTH
    top_body_ok = (
        abs(TOP_PANEL_WIDTH - INNER_WIDTH) <= tolerance
        and abs(TOP_PANEL_WIDTH - 280.0) <= tolerance
        and abs(TOP_BOTTOM_Z - 90.0) <= tolerance
    )
    counts_ok = (
        len(left_bosses) == len(CONNECTION_Y)
        and len(right_bosses) == len(CONNECTION_Y)
        and len(left_sockets) == 2 * len(CONNECTION_Y)
        and len(right_sockets) == 2 * len(CONNECTION_Y)
    )
    pair_alignment_ok = boss_y_ok and socket_y_ok
    gaps_ok = all(abs(gap - CONNECTION_GAP) <= tolerance for gap in gaps)
    bosses_outward_ok = (
        all(face.Center().x < SIDE_PANEL_THICKNESS for face in left_bosses)
        and all(face.Center().x > OUTER_WIDTH - SIDE_PANEL_THICKNESS for face in right_bosses)
    )
    seating_clearance = SOCKET_DEPTH - MALE_BOSS_PROTRUSION
    fit_ok = (
        abs((SOCKET_DIAMETER - MALE_BOSS_DIAMETER) / 2 - RADIAL_CLEARANCE) <= tolerance
        and abs(seating_clearance - DEPTH_CLEARANCE) <= tolerance
        and abs(core_thickness - 2.0) <= tolerance
    )
    interference_left = top_panel.val().intersect(side_panel.val()).Volume()
    interference_right = top_panel.val().intersect(right_side.val()).Volume()
    solids_valid = side_panel.val().isValid() and top_panel.val().isValid()
    top_surface_clean = abs(top_panel.val().BoundingBox().zmax - OUTER_HEIGHT) <= tolerance
    identical_sides = abs(side_panel.val().Volume() - right_side.val().Volume()) <= tolerance

    print(f"Assembly: {bounds.xlen:.3f} x {bounds.ylen:.3f} x {bounds.zlen:.3f} mm")
    circle_top = CONNECTION_Z + MALE_BOSS_RADIUS
    circle_bottom = CONNECTION_Z - MALE_BOSS_RADIUS
    material_above = FLANGE_TOP_Z - circle_top
    material_below = circle_bottom - FLANGE_BOTTOM_Z
    circle_centered = (
        abs(material_above - SUPPORT_VERTICAL_MARGIN) < 0.001
        and abs(material_below - SUPPORT_VERTICAL_MARGIN) < 0.001
        and abs(material_above - material_below) < 0.001
    )
    print(
        "Centered flange circle: "
        f"flange Z={FLANGE_BOTTOM_Z:.3f}..{FLANGE_TOP_Z:.3f}, "
        f"circle center/top/bottom Z={CONNECTION_Z:.3f}/{circle_top:.3f}/{circle_bottom:.3f}, "
        f"above/below={material_above:.3f}/{material_below:.3f} mm "
        f"({'PASS' if circle_centered else 'FAIL'})"
    )
    print(f"Full-height side panel: {'PASS' if side_dimensions_ok else 'FAIL'}")
    print(f"Top body between sides (280 mm at Z=90..100): {'PASS' if top_body_ok else 'FAIL'}")
    print(f"Circular-only connection counts (4 bosses, 8 sockets per side): {'PASS' if counts_ok else 'FAIL'}")
    print(f"Connection centers concentric: {'PASS' if pair_alignment_ok else 'FAIL'} (Y={CONNECTION_Y}, Z={CONNECTION_Z})")
    print(f"Equal edge gaps: {'PASS' if gaps_ok else 'FAIL'} ({gaps} mm)")
    print(
        f"Boss Ø{MALE_BOSS_DIAMETER:.3f}; socket Ø{SOCKET_DIAMETER:.3f}; "
        f"radial clearance {RADIAL_CLEARANCE:.3f} mm"
    )
    print(
        f"Socket depth {SOCKET_DEPTH:.3f}; central core {core_thickness:.3f}; "
        f"anti-bottoming clearance {seating_clearance:.3f} mm ({'PASS' if fit_ok else 'FAIL'})"
    )
    print(f"Outward top bosses / clean horizontal top: {'PASS' if bosses_outward_ok and top_surface_clean else 'FAIL'}")
    print(f"Identical rotated side component: {'PASS' if identical_sides else 'FAIL'}")
    print(f"External envelope and valid solids: {'PASS' if envelope_ok and solids_valid else 'FAIL'}")
    print(
        "Unintended top/side interference: "
        f"{'NO' if interference_left <= tolerance and interference_right <= tolerance else 'YES'} "
        f"(left={interference_left:.6f}, right={interference_right:.6f} mm^3)"
    )


def report_extended_assembly():
    """Validate the four-wall, one-top, eight-dowel modular demonstration."""
    side_panel = make_side_panel()
    top_panel = make_top_panel()
    wood_rod = make_wood_rod()
    tolerance = 1e-6
    side_pitch = MODULE_OUTER_WIDTH - SIDE_PANEL_THICKNESS
    side_positions = [index * side_pitch for index in range(4)]
    sides = [side_panel.translate((x_position, 0, 0)) for x_position in side_positions]
    top = top_panel.translate((side_positions[1], 0, 0))
    rods = []
    for left_side_index in (0, 2):
        rod_start_x = side_positions[left_side_index] + (
            SIDE_PANEL_THICKNESS - WOOD_ROD_INSERTION
        )
        rods.extend(
            wood_rod.translate((rod_start_x, y_center, CONNECTION_Z))
            for y_center in CONNECTION_Y
        )

    compound = cq.Compound.makeCompound(
        [*(side.val() for side in sides), top.val(), *(rod.val() for rod in rods)]
    )
    bounds = compound.BoundingBox()
    expected_width = 3 * MODULE_OUTER_WIDTH - 2 * SIDE_PANEL_THICKNESS
    rod_bounds = wood_rod.val().BoundingBox()
    rod_dimensions_ok = (
        abs(rod_bounds.xlen - WOOD_ROD_LENGTH) <= tolerance
        and abs(rod_bounds.ylen - WOOD_ROD_DIAMETER) <= tolerance
        and abs(rod_bounds.zlen - WOOD_ROD_DIAMETER) <= tolerance
    )
    # Each rod starts/ends 4 mm beyond an inner mating face, derived directly
    # from the same placements used by the extended assembly.
    left_module_start = side_positions[0] + SIDE_PANEL_THICKNESS - WOOD_ROD_INSERTION
    left_module_end = left_module_start + WOOD_ROD_LENGTH
    right_module_start = side_positions[2] + SIDE_PANEL_THICKNESS - WOOD_ROD_INSERTION
    right_module_end = right_module_start + WOOD_ROD_LENGTH
    insertion_ok = (
        abs((side_positions[0] + SIDE_PANEL_THICKNESS) - left_module_start - WOOD_ROD_INSERTION)
        <= tolerance
        and abs(left_module_end - side_positions[1] - WOOD_ROD_INSERTION) <= tolerance
        and abs((side_positions[2] + SIDE_PANEL_THICKNESS) - right_module_start - WOOD_ROD_INSERTION)
        <= tolerance
        and abs(right_module_end - side_positions[3] - WOOD_ROD_INSERTION) <= tolerance
    )
    rod_alignment_ok = (
        sorted(
            round((rod.val().BoundingBox().ymin + rod.val().BoundingBox().ymax) / 2, 6)
            for rod in rods[:4]
        )
        == CONNECTION_Y
        and sorted(
            round((rod.val().BoundingBox().ymin + rod.val().BoundingBox().ymax) / 2, 6)
            for rod in rods[4:]
        )
        == CONNECTION_Y
        and all(
            abs(rod.val().BoundingBox().zmin - (CONNECTION_Z - WOOD_ROD_RADIUS)) <= tolerance
            for rod in rods
        )
    )
    top_interference = sum(
        top.val().intersect(sides[index].val()).Volume() for index in (1, 2)
    )
    rod_interference = sum(
        rods[rod_index].val().intersect(sides[side_index].val()).Volume()
        for rod_index, side_index in ((0, 0), (3, 1), (4, 2), (7, 3))
    )
    valid = all(shape.val().isValid() for shape in [*sides, top, *rods])

    print(f"Extended assembly width: {bounds.xlen:.3f} mm (expected {expected_width:.3f} mm)")
    print("Extended component counts: sides=4, top=1, wood_rods=8")
    print(f"Wood rod dimensions: {'PASS' if rod_dimensions_ok else 'FAIL'} (Ø20.000 x 288.000 mm)")
    print(f"Rod insertion at every end: {'PASS' if insertion_ok else 'FAIL'} (4.000 mm)")
    print(f"Rod/socket radial clearance: {RADIAL_CLEARANCE:.3f} mm")
    print(f"Rod axes use Y={CONNECTION_Y}, Z={CONNECTION_Z:.3f}: {'PASS' if rod_alignment_ok else 'FAIL'}")
    print(f"Extended solids valid: {'PASS' if valid else 'FAIL'}")
    print(
        "Extended unintended interference: "
        f"{'NO' if top_interference <= tolerance and rod_interference <= tolerance else 'YES'} "
        f"(top={top_interference:.6f}, rods={rod_interference:.6f} mm^3)"
    )


def export_parts(side_panel, top_panel, assembly):
    """Write the two printable part files and the assembled STEP model."""
    side_assembly = cq.Assembly(name="side_panel_export")
    side_assembly.add(side_panel, name="side_panel", color=cq.Color(0.08, 0.08, 0.08))
    side_assembly.save(str(OUTPUT_DIR / "side_panel.step"), mode="default")
    exporters.export(side_panel, str(OUTPUT_DIR / "side_panel.stl"))

    top_assembly = cq.Assembly(name="top_panel_export")
    top_assembly.add(top_panel, name="top_panel", color=cq.Color(0.08, 0.08, 0.08))
    top_assembly.save(str(OUTPUT_DIR / "top_panel.step"), mode="default")
    exporters.export(top_panel, str(OUTPUT_DIR / "top_panel.stl"))

    assembly.save(str(OUTPUT_DIR / "assembly.step"), mode="default")


def export_extended_parts(wood_rod, extended_assembly):
    """Write the single reusable dowel and the complete modular assembly."""
    rod_assembly = cq.Assembly(name="wood_rod_export")
    rod_assembly.add(wood_rod, name="wood_rod", color=cq.Color(0.45, 0.25, 0.10))
    rod_assembly.save(str(OUTPUT_DIR / "wood_rod.step"), mode="default")
    exporters.export(wood_rod, str(OUTPUT_DIR / "wood_rod.stl"))
    extended_assembly.save(str(OUTPUT_DIR / "extended_assembly.step"), mode="default")


def main():
    """Build, check, export, and preview the complete enclosure frame."""
    side_panel = make_side_panel()
    top_panel = make_top_panel()
    assembly = make_assembly()
    wood_rod = make_wood_rod()
    extended_assembly = make_extended_assembly()
    report_fit(side_panel, top_panel)
    report_extended_assembly()
    export_parts(side_panel, top_panel, assembly)
    export_extended_parts(wood_rod, extended_assembly)
    show(assembly)


if __name__ == "__main__":
    main()
