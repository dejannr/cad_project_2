"""OCP CAD Viewer entry point for the reusable wooden dowel."""

from ocp_vscode import show

from enclosure_frame import make_wood_rod


wood_rod = make_wood_rod()
show(wood_rod, names=["wood_rod"], colors=["saddlebrown"])
