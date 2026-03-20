"""Grasshopper Mirror — Canvas capture wrapper.

Paste into a GhPython node.  Logic lives in lib/mirror_canvas.py.
Input:  guard (Boolean Toggle), trigger   Output:  a
"""
import sys, os
import Grasshopper as gh

LIB_PATH = os.path.join(os.pardir, "lib")

_here = os.path.dirname(ghenv.Component.OnPingDocument().FilePath)
sys.path.insert(0, os.path.join(_here, LIB_PATH))

from mirror_canvas import save_canvas_image

if not guard:
    a = save_canvas_image(ghenv.Component.OnPingDocument(),
                          gh.Instances.ActiveCanvas)
else:
    a = "Guarded — toggle to run"
