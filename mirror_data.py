"""Grasshopper Mirror — Data wrapper.

Paste into a GhPython node.  Logic lives in lib/mirror_data.py.
Input:  trigger   Output:  out
"""
import sys, os

LIB_PATH = os.path.join(os.pardir, "lib")

_here = os.path.dirname(ghenv.Component.OnPingDocument().FilePath)
sys.path.insert(0, os.path.join(_here, LIB_PATH))

from mirror_data import write_data

out = write_data(ghenv.Component.OnPingDocument())
