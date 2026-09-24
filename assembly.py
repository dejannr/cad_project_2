"""OCP CAD Viewer entry point for the fully assembled enclosure frame."""

from ocp_vscode import show

from enclosure_frame import make_assembly


assembly = make_assembly()
show(assembly)
