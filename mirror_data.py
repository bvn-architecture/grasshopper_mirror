"""Grasshopper Mirror — Data JSON Generator

Paste this into a GhPython Script node on the Grasshopper canvas.

    Node setup
    ----------
    Input:  trigger  — connect a button or any wire to trigger generation
    Output: out      — status message / JSON string

Target: Rhino 8+ / CPython 3.9

Captures leaf-node values, component state, and script source code.
Output is deterministically sorted by GUID so the file is byte-identical
when nothing changes.

Kept separate from _topology.dot so value/state changes don't pollute
structural diffs.
"""

import json
import os
import Grasshopper as gh


MAX_REPR_LEN = 100


def _truncated_repr(val):
    """Return repr(val) truncated to MAX_REPR_LEN characters."""
    try:
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
                values.append(_truncated_repr(item))
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


def _get_component_state(obj):
    """Capture component state flags."""
    state = {}

    # Locked = disabled (greyed out on canvas)
    if hasattr(obj, "Locked"):
        try:
            state["locked"] = bool(obj.Locked)
        except Exception:
            pass

    # Hidden = preview off
    if hasattr(obj, "Hidden"):
        try:
            state["hidden"] = bool(obj.Hidden)
        except Exception:
            pass

    return state


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

        # Component state
        state = _get_component_state(obj)
        if state:
            entry["state"] = state

        # Script source code
        source = _get_script_source(obj)
        if source is not None:
            entry["script_source"] = source

        # Component with Params — capture input param values
        if hasattr(obj, "Params"):
            input_values = {}
            for p in obj.Params.Input:
                vals = _get_volatile_values(p)
                if vals:
                    input_values[p.NickName] = vals
            if input_values:
                entry["input_values"] = input_values

            output_values = {}
            for p in obj.Params.Output:
                vals = _get_volatile_values(p)
                if vals:
                    output_values[p.NickName] = vals
            if output_values:
                entry["output_values"] = output_values

        # Leaf / standalone parameter — capture its own value
        elif hasattr(obj, "Sources"):
            vals = _get_volatile_values(obj)
            if vals:
                entry["values"] = vals

        # Only include entries that have something beyond name/type
        has_content = any(
            k in entry
            for k in ("state", "script_source", "input_values",
                       "output_values", "values")
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
out = _write_data(gh_doc)
