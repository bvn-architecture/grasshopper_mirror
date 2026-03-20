"""Grasshopper Mirror — Topology wrapper.

Paste into a GhPython node.  Logic lives in lib/mirror_topology.py.
Input:  trigger   Output:  graph
"""
import sys, os

# Relative path from this .gh file's folder to the lib/ directory.
# Override if your repo layout differs (e.g. "../../lib").
LIB_PATH = os.path.join(os.pardir, "lib")

_here = os.path.dirname(ghenv.Component.OnPingDocument().FilePath)
sys.path.insert(0, os.path.join(_here, LIB_PATH))

from mirror_topology import generate_topology

graph = generate_topology(ghenv.Component.OnPingDocument())
