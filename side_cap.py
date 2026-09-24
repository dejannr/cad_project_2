"""OCP CAD Viewer entry point for a flush exterior side-panel socket cap."""

from ocp_vscode import show

from enclosure_frame import make_side_cap


side_cap = make_side_cap()
show(side_cap, names=["side_cap"], colors=["black"])
