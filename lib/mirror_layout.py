"""Grasshopper Mirror — Layout JSON Generator

Captures canvas positions (Pivot, Bounds) for every object in a
Grasshopper document.

Public API
----------
    write_layout(gh_doc) → str   (status message)
    collect_layout(gh_doc) → dict
"""

from mirror_common import output_path, write_json


def collect_layout(gh_doc):
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

    return dict(sorted(layout.items()))


def write_layout(gh_doc):
    """Generate layout JSON and write to disk."""
    path = output_path(gh_doc, "layout.json")
    if path is None:
        return "Cannot save: document has no file path (save the .gh first)"

    layout = collect_layout(gh_doc)
    write_json(path, layout)
    return f"Saved {len(layout)} entries to {path}"
