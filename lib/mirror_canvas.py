"""Grasshopper Mirror — Canvas Screenshot

Frames the full canvas extent and captures to PNG.

Public API
----------
    save_canvas_image(gh_doc, canvas) → str   (status message)
"""

import os
import System.Drawing as sd
import System.Windows.Forms as swf
import Grasshopper as gh

from mirror_common import doc_dir


PADDING = 60.0
FIT_MARGIN = 0.92


def _compute_objects_bounds(gh_doc):
    """Union of every object's Attributes.Bounds on the canvas."""
    first = True
    for obj in gh_doc.Objects:
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


def save_canvas_image(gh_doc, canvas):
    """Capture full canvas and save to canvas_image.png next to the .gh file."""
    directory = doc_dir(gh_doc)
    if directory is None:
        return "Cannot save: document has no file path (save the .gh first)"

    viewport = canvas.Viewport

    saved_target = sd.Point(viewport.Target.X, viewport.Target.Y)
    saved_zoom = viewport.Zoom

    try:
        bounds = _compute_objects_bounds(gh_doc)
        bounds.Inflate(PADDING, PADDING)

        cx = bounds.X + bounds.Width / 2.0
        cy = bounds.Y + bounds.Height / 2.0

        zoom_x = viewport.Width / bounds.Width
        zoom_y = viewport.Height / bounds.Height
        new_zoom = min(zoom_x, zoom_y) * FIT_MARGIN
        viewport.Zoom = new_zoom

        target_x = int(viewport.Width / 2 - cx * new_zoom)
        target_y = int(viewport.Height / 2 - cy * new_zoom)
        viewport.Target = sd.Point(target_x, target_y)

        viewport.ComputeProjection()
        canvas.Invalidate()
        canvas.Update()
        swf.Application.DoEvents()

        mode = gh.GUI.Canvas.GH_CanvasMode.Export
        bmp = canvas.GetCanvasScreenBuffer(mode)

        path = os.path.join(directory, "canvas_image.png")
        bmp.Save(path)
        bmp.Dispose()

        return f"Saved canvas image to {path}"

    finally:
        viewport.Target = saved_target
        viewport.Zoom = saved_zoom
        canvas.Refresh()
