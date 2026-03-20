"""Grasshopper Mirror — Layout JSON Generator

Paste this into a GhPython Script node on the Grasshopper canvas.

    Node setup
    ----------
    Input:  trigger  — connect a button or any wire to trigger generation
    Output: out      — status message / JSON string

Target: Rhino 8+ / CPython 3.9

Captures the x/y position (Pivot) and bounding box of every component,
leaf parameter, and group on the canvas.  Output is deterministically
sorted by GUID so the file is byte-identical when nothing moves.

Kept separate from _topology.dot so canvas tidying doesn't pollute
topology or data diffs.
"""

import json
import os
import Grasshopper as gh


def _collect_layout(gh_doc):
    """Return a dict of layout data keyed by GUID string."""
    layout = {}

    for obj in gh_doc.Objects:
        guid = str(obj.InstanceGuid)
        attrs = obj.Attributes
        if attrs is None:
            continue

        pivot = attrs.Pivot
        bounds = attrs.Bounds

        entry = {
            "name": obj.NickName or obj.Name or "",
            "pivot": {"x": round(float(pivot.X), 2),
                      "y": round(float(pivot.Y), 2)},
            "bounds": {"x": round(float(bounds.X), 2),
                       "y": round(float(bounds.Y), 2),
                       "w": round(float(bounds.Width), 2),
                       "h": round(float(bounds.Height), 2)},
        }

        # Include the concrete type for context
        if hasattr(obj, "GetType"):
            entry["type"] = obj.GetType().Name

        layout[guid] = entry

    # Sort by GUID for deterministic output
    return dict(sorted(layout.items()))


def _write_layout(gh_doc):
    """Generate layout JSON and write to disk."""
    file_path = gh_doc.FilePath
    if not file_path:
        return "Cannot save: document has no file path (save the .gh first)"

    layout = _collect_layout(gh_doc)
    json_str = json.dumps(layout, indent=2, ensure_ascii=False)

    base = os.path.splitext(os.path.basename(file_path))[0]
    out_path = os.path.join(os.path.dirname(file_path), f"{base}_layout.json")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json_str)
        f.write("\n")

    return f"Saved {len(layout)} entries to {out_path}"


gh_doc = gh.Instances.ActiveCanvas.Document
out = _write_layout(gh_doc)
