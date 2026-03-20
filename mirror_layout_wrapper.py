"""Grasshopper Mirror — Layout wrapper.

Paste into a GhPython node.  Logic lives in lib/mirror_layout.py.
Input:  trigger   Output:  out
"""
import sys, os

LIB_PATH = os.path.join(os.pardir, "lib")

_here = os.path.dirname(ghenv.Component.OnPingDocument().FilePath)
sys.path.insert(0, os.path.join(_here, LIB_PATH))

from mirror_layout import write_layout

out = write_layout(ghenv.Component.OnPingDocument())
