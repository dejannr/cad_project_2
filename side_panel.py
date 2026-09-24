"""OCP CAD Viewer entry point for the reusable side panel (print two)."""

from ocp_vscode import show

from enclosure_frame import make_side_panel


side_panel = make_side_panel()
show(side_panel, names=["side_panel"], colors=["black"])
