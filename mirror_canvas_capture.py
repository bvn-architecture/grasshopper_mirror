"""Grasshopper Mirror — Canvas Screenshot

Paste this into a GhPython Script node on the Grasshopper canvas.

    Node setup
    ----------
    Input:  guard   — connect a Boolean Toggle (True = don't run)
    Output: out     — status message

Target: Rhino 8+ / CPython 3.9

Frames the full canvas extent and captures to PNG.
Computes bounds from individual object Attributes.Bounds.
Saves and restores the viewport so the view snaps back.
"""

import os
import System.Drawing as sd
import System.Windows.Forms as swf
import Grasshopper as gh


# Padding in canvas units around the computed bounds
PADDING = 60.0

# Slight inward scale so nodes aren't right at the edge
FIT_MARGIN = 0.92


def compute_objects_bounds(ghdoc):
    """Union of every object's Attributes.Bounds on the canvas."""
    first = True
    for obj in ghdoc.Objects:
        if obj.Attributes is None:
            continue
        b = obj.Attributes.Bounds
        if first:
            union = sd.RectangleF(b.X, b.Y, b.Width, b.Height)
            first = False
        else:
            union = sd.RectangleF.Union(union, b)

    if first:
        return sd.RectangleF(0, 0, 100, 100)
    return union


def save_canvas_image():
    ghdoc = ghenv.Component.OnPingDocument()
    canvas = gh.Instances.ActiveCanvas
    viewport = canvas.Viewport

    file_path = ghdoc.FilePath
    if not file_path:
        return "Cannot save: document has no file path (save the .gh first)"

    directory_path = os.path.dirname(file_path)

    # Save current viewport state so we can restore it
    saved_target = sd.Point(viewport.Target.X, viewport.Target.Y)
    saved_zoom = viewport.Zoom

    try:
        bounds = compute_objects_bounds(ghdoc)
        bounds.Inflate(PADDING, PADDING)

        # Centre of the objects region in canvas coords
        cx = bounds.X + bounds.Width / 2.0
        cy = bounds.Y + bounds.Height / 2.0

        # Zoom to fit bounds
        zoom_x = viewport.Width / bounds.Width
        zoom_y = viewport.Height / bounds.Height
        new_zoom = min(zoom_x, zoom_y) * FIT_MARGIN
        viewport.Zoom = new_zoom

        # Target is a screen pixel offset, not a canvas coordinate.
        # Projection: screen = canvas * zoom + target
        # To place canvas point (cx, cy) at screen centre:
        #   target = screen_centre - canvas_centre * zoom
        target_x = int(viewport.Width / 2 - cx * new_zoom)
        target_y = int(viewport.Height / 2 - cy * new_zoom)
        viewport.Target = sd.Point(target_x, target_y)

        viewport.ComputeProjection()
        canvas.Invalidate()
        canvas.Update()
        swf.Application.DoEvents()

        # Capture the screen buffer
        mode = gh.GUI.Canvas.GH_CanvasMode.Export
        bmp = canvas.GetCanvasScreenBuffer(mode)

        path = os.path.join(directory_path, "canvas_image.png")
        bmp.Save(path)
        bmp.Dispose()

        return f"Saved canvas image to {path}"

    finally:
        # Restore viewport immediately
        viewport.Target = saved_target
        viewport.Zoom = saved_zoom
        canvas.Refresh()


if not guard:
    a = save_canvas_image()
else:
    a = "Guarded — toggle to run"
