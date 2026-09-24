"""OCP CAD Viewer entry point for the top panel (print one)."""

from ocp_vscode import show

from enclosure_frame import make_top_panel


top_panel = make_top_panel()
show(top_panel, names=["top_panel"], colors=["black"])
