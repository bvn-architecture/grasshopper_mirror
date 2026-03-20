"""Grasshopper Mirror — Scaffold wrapper.

Paste this into a GhPython node and run it ONCE.
It will create all the Mirror capture nodes on the canvas.

Re-running is safe — it updates existing nodes by NickName match.

Input:  trigger   Output:  out

Adjust LIB_PATH if your lib/ folder is not at ../lib relative to this .gh file.
"""
import sys, os
import importlib
import Grasshopper as gh

LIB_PATH = os.path.join(os.pardir, "lib")

_here = os.path.dirname(ghenv.Component.OnPingDocument().FilePath)
sys.path.insert(0, os.path.join(_here, LIB_PATH))

import mirror_scaffold
importlib.reload(mirror_scaffold)
from mirror_scaffold import scaffold

a = scaffold(ghenv.Component.OnPingDocument(),
               gh.Instances.ActiveCanvas,
               lib_path=LIB_PATH,
               caller=ghenv.Component)
