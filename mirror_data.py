"""Grasshopper Mirror — Data JSON Generator

Paste this into a GhPython Script node on the Grasshopper canvas.

    Node setup
    ----------
    Input:  trigger  — connect a button or any wire to trigger generation
    Output: out      — status message / JSON string

Target: Rhino 8+ / CPython 3.9

Captures leaf-node values and script source code.
Output is deterministically sorted by GUID so the file is byte-identical
when nothing changes.

Kept separate from _topology.dot so value changes don't pollute
structural diffs.  Component state (locked/hidden) lives in the DOT file.
"""

import json
import os
import Grasshopper as gh


MAX_REPR_LEN = 100


def _extract_value(val):
    """Extract a JSON-friendly primitive from a GH data item.

    GH wrapper types (GH_String, GH_Number, GH_Boolean, etc.) expose a
    .Value property that holds the underlying Python primitive.  We pull
    that out so the JSON contains actual strings/numbers/bools instead of
    opaque object reprs.
    """
    try:
        if hasattr(val, "Value"):
            v = val.Value
            if isinstance(v, (str, int, float, bool)):
                return v
        # Fall back to repr for geometry / unknown types
        r = repr(val)
    except Exception:
        r = "<repr failed>"
    if len(r) > MAX_REPR_LEN:
        return r[:MAX_REPR_LEN - 3] + "..."
    return r


def _get_volatile_values(obj):
    """Extract runtime values from a parameter's VolatileData tree.

    Returns a list of string representations, one per item across
    all branches.  Truncated to MAX_REPR_LEN per item.
    """
    values = []
    try:
        vd = obj.VolatileData
        if vd is None or vd.IsEmpty:
            return values
        for branch in vd.Branches:
            for item in branch:
                values.append(_extract_value(item))
    except Exception:
        pass
    return values


def _get_script_source(obj):
    """Try to extract source code from Python 3 / C# script components.

    Returns the source string, or None if not a script component.
    """
    # Python 3 Script (ScriptInstance) — try .Code first, then .ScriptSource
    for attr_name in ("Code", "ScriptSource"):
        if hasattr(obj, attr_name):
            try:
                src = getattr(obj, attr_name)
                if src and isinstance(src, str) and len(src) > 0:
                    return src
            except Exception:
                pass
    return None


def _collect_data(gh_doc):
    """Return a dict of data keyed by GUID string."""
    data = {}

    objects = sorted(gh_doc.Objects, key=lambda o: str(o.InstanceGuid))

    for obj in objects:
        guid = str(obj.InstanceGuid)
        entry = {
            "name": obj.NickName or obj.Name or "",
        }

        # Concrete type
        if hasattr(obj, "GetType"):
            entry["type"] = obj.GetType().Name

        # Script source code
        source = _get_script_source(obj)
        if source is not None:
            entry["script_source"] = source

        # Component with Params — capture only unwired input values
        if hasattr(obj, "Params"):
            input_values = {}
            for p in obj.Params.Input:
                # Skip params that receive values via wire
                if p.Sources and p.Sources.Count > 0:
                    continue
                vals = _get_volatile_values(p)
                if vals:
                    input_values[p.NickName] = vals
            if input_values:
                entry["input_values"] = input_values

        # Leaf / standalone parameter — only if not wired
        elif hasattr(obj, "Sources"):
            if not obj.Sources or obj.Sources.Count == 0:
                vals = _get_volatile_values(obj)
                if vals:
                    entry["values"] = vals

        # Only include entries that have something beyond name/type
        has_content = any(
            k in entry
            for k in ("script_source", "input_values", "values")
        )
        if has_content:
            data[guid] = entry

    # Sort by GUID for deterministic output
    return dict(sorted(data.items()))


def _write_data(gh_doc):
    """Generate data JSON and write to disk."""
    file_path = gh_doc.FilePath
    if not file_path:
        return "Cannot save: document has no file path (save the .gh first)"

    data = _collect_data(gh_doc)
    json_str = json.dumps(data, indent=2, ensure_ascii=False)

    base = os.path.splitext(os.path.basename(file_path))[0]
    out_path = os.path.join(os.path.dirname(file_path), f"{base}_data.json")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json_str)
        f.write("\n")

    return f"Saved {len(data)} entries to {out_path}"


gh_doc = gh.Instances.ActiveCanvas.Document
print(_write_data(gh_doc))
