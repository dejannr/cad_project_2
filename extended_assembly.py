"""OCP CAD Viewer entry point for the four-wall modular demonstration."""

from ocp_vscode import show

from enclosure_frame import make_extended_assembly


extended_assembly = make_extended_assembly()
show(extended_assembly)
