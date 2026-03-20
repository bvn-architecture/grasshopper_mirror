"""Grasshopper Mirror — Data JSON Generator

Captures leaf-node values and script source code from a live
Grasshopper document.

Public API
----------
    write_data(gh_doc) → str   (status message)
    collect_data(gh_doc) → dict
"""

from mirror_common import output_path, write_json


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
    """Extract runtime values from a parameter's VolatileData tree."""
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
    for attr_name in ("Code", "ScriptSource"):
        if hasattr(obj, attr_name):
            try:
                src = getattr(obj, attr_name)
                if src and isinstance(src, str) and len(src) > 0:
                    return src
            except Exception:
                pass
    return None


def collect_data(gh_doc):
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

    return dict(sorted(data.items()))


def write_data(gh_doc):
    """Generate data JSON and write to disk."""
    path = output_path(gh_doc, "data.json")
    if path is None:
        return "Cannot save: document has no file path (save the .gh first)"

    data = collect_data(gh_doc)
    write_json(path, data)
    return f"Saved {len(data)} entries to {path}"
