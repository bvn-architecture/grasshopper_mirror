"""Grasshopper Mirror — Canvas Scaffold

Paste this into a single GhPython Script node and run it once.
It will create (or update) all the Mirror capture nodes on the canvas:

    Data Dam → Data → ┬─ Topology Capture (Py3 + Panel)
                       ├─ Layout Capture   (Py3 + Panel)
                       ├─ Data Capture     (Py3 + Panel)
                       └─ Canvas Capture   (Py3 + Toggle + Panel)

Plus a README Generation subgroup with input panels.

Idempotent: re-running updates existing nodes by NickName match.

Public API
----------
    scaffold(gh_doc, canvas, lib_path="../lib") → str
"""

import os
import System.Drawing as sd
import Grasshopper as gh
import Grasshopper.Kernel as ghk
from Grasshopper.Kernel.Special import (
    GH_Panel,
    GH_BooleanToggle,
    GH_Group,
)

# Python 3 Script nodes are created via ComponentServer by name.
# No special imports needed — _create_by_name("Python 3 Script") handles it.


# ---------------------------------------------------------------------------
# Wrapper code templates
# ---------------------------------------------------------------------------

def _wrapper_code(module_name, func_name, output_var, lib_path,
                  extra_imports="", extra_args="", guard=False):
    """Generate the wrapper code for a Py3 Script node."""
    lines = [
        "import sys, os, importlib",
    ]
    if extra_imports:
        lines.append(extra_imports)
    lines.append("")
    lines.append(f'LIB_PATH = os.path.join({_path_expr(lib_path)})')
    lines.append("")
    lines.append("_here = os.path.dirname(ghenv.Component.OnPingDocument().FilePath)")
    lines.append("sys.path.insert(0, os.path.join(_here, LIB_PATH))")
    lines.append("")
    lines.append(f"import {module_name}")
    lines.append(f"importlib.reload({module_name})")
    lines.append(f"from {module_name} import {func_name}")
    lines.append("")

    doc_expr = "ghenv.Component.OnPingDocument()"

    if guard:
        lines.append("if not guard:")
        lines.append(f"    {output_var} = {func_name}({doc_expr}{extra_args})")
        lines.append('else:')
        lines.append(f'    {output_var} = "Guarded — toggle to run"')
    else:
        lines.append(f"{output_var} = {func_name}({doc_expr}{extra_args})")

    return "\n".join(lines)


def _path_expr(lib_path):
    """Convert a relative path like '../lib' into os.path.join args."""
    parts = lib_path.replace("\\", "/").split("/")
    args = []
    for p in parts:
        if p == "..":
            args.append("os.pardir")
        else:
            args.append(f'"{p}"')
    return ", ".join(args)


# ---------------------------------------------------------------------------
# ComponentServer helper — create arbitrary components by display name
# ---------------------------------------------------------------------------

def _create_by_name(name):
    """Create a component instance by its display name via the ComponentServer.

    Works for any registered component (Data Dam, Relay, etc.) without
    needing to know the exact .NET class or namespace.
    """
    server = gh.Instances.ComponentServer
    for proxy in server.ObjectProxies:
        if proxy.Desc.Name == name:
            obj = proxy.CreateInstance()
            return obj
    return None


# ---------------------------------------------------------------------------
# Node finding / creation helpers
# ---------------------------------------------------------------------------

def _find_by_nickname(gh_doc, nickname, type_filter=None):
    """Find an existing object by NickName.  Returns None if not found."""
    for obj in gh_doc.Objects:
        if obj.NickName == nickname:
            if type_filter is None or isinstance(obj, type_filter):
                return obj
    return obj if obj.NickName == nickname else None


def _find_by_nickname_exact(gh_doc, nickname):
    """Find an existing object by NickName.  Returns None if not found."""
    for obj in gh_doc.Objects:
        if obj.NickName == nickname:
            return obj
    return None


def _place(obj, x, y):
    """Set the pivot position of an object."""
    if obj.Attributes is None:
        print("Creating attributes for object", obj.NickName)
        obj.CreateAttributes()
    obj.Attributes.Pivot = sd.PointF(float(x), float(y))


def _add_or_update_panel(gh_doc, nickname, x, y, content=""):
    """Find or create a Panel, position it, return it."""
    existing = _find_by_nickname_exact(gh_doc, nickname)
    if existing and isinstance(existing, GH_Panel):
        _place(existing, x, y)
        return existing

    panel = GH_Panel()
    panel.NickName = nickname
    if content:
        panel.SetUserText(content)
    _place(panel, x, y)
    gh_doc.AddObject(panel, False)
    return panel


def _add_or_update_toggle(gh_doc, nickname, x, y, default_value=True):
    """Find or create a Boolean Toggle."""
    existing = _find_by_nickname_exact(gh_doc, nickname)
    if existing and isinstance(existing, GH_BooleanToggle):
        _place(existing, x, y)
        return existing

    toggle = GH_BooleanToggle()
    toggle.NickName = nickname
    toggle.Value = default_value
    _place(toggle, x, y)
    gh_doc.AddObject(toggle, False)
    return toggle


def _add_or_update_dam(gh_doc, nickname, x, y):
    """Find or create a Data Dam."""
    existing = _find_by_nickname_exact(gh_doc, nickname)
    if existing is not None:
        _place(existing, x, y)
        return existing

    dam = _create_by_name("Data Dam")
    if dam is None:
        return None
    dam.NickName = nickname
    _place(dam, x, y)
    gh_doc.AddObject(dam, False)
    return dam


def _add_or_update_relay(gh_doc, nickname, x, y):
    """Find or create a Relay (pass-through Data node)."""
    existing = _find_by_nickname_exact(gh_doc, nickname)
    if existing is not None:
        _place(existing, x, y)
        return existing

    relay = _create_by_name("Relay")
    if relay is None:
        return None
    relay.NickName = nickname
    _place(relay, x, y)
    gh_doc.AddObject(relay, False)
    return relay


def _set_code(script, code):
    """Set the source code on a script component, trying known attributes."""
    if hasattr(script, "Code"):
        script.Code = code
    elif hasattr(script, "ScriptSource"):
        script.ScriptSource = code


def _configure_script_params(script, input_names, output_names,
                             input_access=None):
    """Add / rename input and output parameters on a script component.

    Works with the Rhino 8 Python 3 Script node created via the
    ComponentServer.  After creation, the node typically starts with
    one default input (``x``) and one default output (``a``).  We
    reconcile to the desired names by renaming existing params and
    registering extras as needed.

    Parameters
    ----------
    input_access : dict or None
        Mapping of input name → GH_ParamAccess int (0=item, 1=list, 2=tree).
        Defaults to item (0) for all inputs.
    """
    from Grasshopper.Kernel.Parameters import Param_ScriptVariable
    from Grasshopper.Kernel import GH_ParamAccess

    input_access = input_access or {}

    # --- Inputs ---
    existing_in = list(script.Params.Input)
    for i, name in enumerate(input_names):
        access_val = input_access.get(name, 0)
        access_enum = (GH_ParamAccess.list if access_val == 1
                       else GH_ParamAccess.tree if access_val == 2
                       else GH_ParamAccess.item)
        if i < len(existing_in):
            # Rename existing
            existing_in[i].Name = name
            existing_in[i].NickName = name
            existing_in[i].Optional = True
            existing_in[i].Access = access_enum
        else:
            # Add new
            p = Param_ScriptVariable()
            p.Name = name
            p.NickName = name
            p.Optional = True
            p.Access = access_enum
            script.Params.RegisterInputParam(p)

    # --- Outputs ---
    existing_out = list(script.Params.Output)
    for i, name in enumerate(output_names):
        if i < len(existing_out):
            existing_out[i].Name = name
            existing_out[i].NickName = name
        else:
            p = Param_ScriptVariable()
            p.Name = name
            p.NickName = name
            script.Params.RegisterOutputParam(p)


def _add_or_update_py3(gh_doc, nickname, code, x, y,
                       input_names=None, output_names=None,
                       input_access=None):
    """Find or create a Python 3 Script node and set its code.

    Uses the ComponentServer to create a genuine "Python 3 Script"
    node (CPython 3.x, not IronPython 2.7).
    """
    input_names = input_names or ["trigger"]
    output_names = output_names or ["result"]

    # Try to find existing by nickname
    existing = _find_by_nickname_exact(gh_doc, nickname)
    if existing is not None:
        _set_code(existing, code)
        _place(existing, x, y)
        return existing

    # Create via ComponentServer — this gives us a true Py3 node
    script = _create_by_name("Python 3 Script")
    if script is None:
        print("WARNING: Could not create 'Python 3 Script' component.")
        return None

    script.NickName = nickname
    script.Name = nickname

    _set_code(script, code)
    _configure_script_params(script, input_names, output_names, input_access)
    _place(script, x, y)
    gh_doc.AddObject(script, False)
    return script


def _wire(gh_doc, source_obj, source_port_index,
          target_obj, target_port_index):
    """Wire an output to an input.

    For components with Params, use port indices.
    For special objects (Panel, Toggle, etc.), index 0 is typical.
    """
    try:
        # Get the actual param objects
        if hasattr(source_obj, "Params"):
            src_param = source_obj.Params.Output[source_port_index]
        else:
            # Standalone param (Panel, Toggle, etc.) — it IS the param
            src_param = source_obj

        if hasattr(target_obj, "Params"):
            tgt_param = target_obj.Params.Input[target_port_index]
        else:
            tgt_param = target_obj

        # Check if already connected
        for existing_src in tgt_param.Sources:
            if existing_src.InstanceGuid == src_param.InstanceGuid:
                return  # Already wired

        tgt_param.AddSource(src_param)
    except Exception:
        pass  # Wiring failures are non-fatal


def _group_objects(gh_doc, objects, name, colour=None):
    """Create or update a group containing the given objects.

    Searches for an existing group by name first.
    If no colour is given, a default semi-transparent grey is used
    (GH_Group with no colour set is invisible).
    """
    from Grasshopper.Kernel.Special import GH_Group

    if colour is None:
        colour = sd.Color.FromArgb(80, 160, 160, 160)

    # Find existing group by name
    existing_group = None
    for obj in gh_doc.Objects:
        if isinstance(obj, GH_Group) and obj.NickName == name:
            existing_group = obj
            break

    if existing_group:
        grp = existing_group
    else:
        grp = GH_Group()
        grp.NickName = name
        gh_doc.AddObject(grp, False)

    grp.Colour = colour

    # Set membership
    guids = [obj.InstanceGuid for obj in objects if obj is not None]
    for guid in guids:
        grp.AddObject(guid)

    return grp


# ---------------------------------------------------------------------------
# Main scaffold
# ---------------------------------------------------------------------------

# Layout constants (canvas coordinates)
_COL_DAM    =  0
_COL_DATA   = 180
_COL_SCRIPT = 400
_COL_PANEL  = 700

_ROW_SPACING = 160
_ROW_START   = 0

_README_COL_PANELS = _COL_SCRIPT - 250
_README_COL_SCRIPT = _COL_SCRIPT
_README_COL_OUTPUT = _COL_PANEL


def scaffold(gh_doc, canvas, lib_path=None, caller=None):
    """Create or update all Grasshopper Mirror nodes.

    Parameters
    ----------
    gh_doc : GH_Document
    canvas : GH_Canvas
    lib_path : str or None
        Relative path from the .gh file to the lib/ directory.
        Defaults to "../lib".
    caller : IGH_Component or None
        The component that invoked the scaffold (``ghenv.Component``).
        When provided, all new nodes are placed to the right of and
        below this component so they don't overlap existing work.
    """
    if lib_path is None:
        lib_path = "../lib"

    # Compute origin offset from the calling node's position
    ox, oy = 0, 0
    if caller is not None:
        try:
            pivot = caller.Attributes.Pivot
            ox = int(pivot.X) + 250   # to the right of the caller
            oy = int(pivot.Y) + 100   # below the caller
        except Exception:
            pass  # fall back to absolute layout

    results = []

    # Row positions
    row = _ROW_START

    # --- Data Dam ---
    dam = _add_or_update_dam(gh_doc, "Dam", ox + _COL_DAM, oy + row)
    results.append(f"Dam: {'updated' if dam else 'FAILED'}")

    # --- Data relay (pass-through) ---
    data_relay = _add_or_update_relay(
        gh_doc, "Data", ox + _COL_DATA, oy + row)
    _wire(gh_doc, dam, 0, data_relay, 0)
    results.append(f"Data relay: {'updated' if data_relay else 'FAILED'}")

    # --- Topology Capture ---
    row = _ROW_START
    topo_code = _wrapper_code(
        "mirror_topology", "generate_topology", "graph", lib_path)
    topo_py3 = _add_or_update_py3(
        gh_doc, "Mirror Topology", topo_code, ox + _COL_SCRIPT, oy + row,
        input_names=["trigger"], output_names=["result", "graph"])
    topo_panel = _add_or_update_panel(
        gh_doc, "Dot panel", ox + _COL_PANEL, oy + row)
    if topo_py3 and data_relay:
        _wire(gh_doc, data_relay, 0, topo_py3, 0)      # trigger
    if topo_py3 and topo_panel:
        _wire(gh_doc, topo_py3, 1, topo_panel, 0)       # graph → panel
    results.append(f"Topology: {'updated' if topo_py3 else 'SKIPPED (no Py3 class)'}")

    topo_objects = [o for o in [topo_py3, topo_panel] if o]
    topo_grp = _group_objects(gh_doc, topo_objects, "Topology Capture")

    # --- Layout Capture ---
    row += _ROW_SPACING
    layout_code = _wrapper_code(
        "mirror_layout", "write_layout", "result", lib_path)
    layout_py3 = _add_or_update_py3(
        gh_doc, "Mirror Layout", layout_code, ox + _COL_SCRIPT, oy + row,
        input_names=["trigger"], output_names=["result", "data_json"])
    layout_panel = _add_or_update_panel(
        gh_doc, "Layout output", ox + _COL_PANEL, oy + row)
    if layout_py3 and data_relay:
        _wire(gh_doc, data_relay, 0, layout_py3, 0)
    if layout_py3 and layout_panel:
        _wire(gh_doc, layout_py3, 0, layout_panel, 0)
    results.append(f"Layout: {'updated' if layout_py3 else 'SKIPPED'}")

    layout_objects = [o for o in [layout_py3, layout_panel] if o]
    layout_grp = _group_objects(gh_doc, layout_objects, "Layout Capture")

    # --- Data Capture ---
    row += _ROW_SPACING
    data_code = _wrapper_code(
        "mirror_data", "write_data", "result", lib_path)
    data_py3 = _add_or_update_py3(
        gh_doc, "Mirror Data", data_code, ox + _COL_SCRIPT, oy + row,
        input_names=["trigger"], output_names=["result", "data_json"])
    data_panel = _add_or_update_panel(
        gh_doc, "Data output", ox + _COL_PANEL, oy + row)
    if data_py3 and data_relay:
        _wire(gh_doc, data_relay, 0, data_py3, 0)
    if data_py3 and data_panel:
        _wire(gh_doc, data_py3, 0, data_panel, 0)
    results.append(f"Data: {'updated' if data_py3 else 'SKIPPED'}")

    data_objects = [o for o in [data_py3, data_panel] if o]
    data_grp = _group_objects(gh_doc, data_objects, "Data Capture")

    # --- Canvas Capture ---
    row += _ROW_SPACING
    canvas_code = _wrapper_code(
        "mirror_canvas", "save_canvas_image", "a", lib_path,
        extra_imports="import Grasshopper as gh",
        extra_args=",\n                          gh.Instances.ActiveCanvas",
        guard=True)
    canvas_py3 = _add_or_update_py3(
        gh_doc, "Mirror Canvas", canvas_code, ox + _COL_SCRIPT, oy + row,
        input_names=["guard", "trigger"], output_names=["result", "a"])
    canvas_toggle = _add_or_update_toggle(
        gh_doc, "Toggle", ox + _COL_SCRIPT - 200, oy + row, default_value=True)
    canvas_panel = _add_or_update_panel(
        gh_doc, "Canvas output", ox + _COL_PANEL, oy + row)
    if canvas_py3 and data_relay:
        _wire(gh_doc, data_relay, 0, canvas_py3, 1)     # trigger (port 1)
    if canvas_py3 and canvas_toggle:
        _wire(gh_doc, canvas_toggle, 0, canvas_py3, 0)  # guard (port 0)
    if canvas_py3 and canvas_panel:
        _wire(gh_doc, canvas_py3, 1, canvas_panel, 0)
    results.append(f"Canvas: {'updated' if canvas_py3 else 'SKIPPED'}")

    canvas_objects = [o for o in [canvas_py3, canvas_toggle, canvas_panel] if o]
    canvas_grp = _group_objects(gh_doc, canvas_objects, "Canvas Capture")

    # --- README Generation ---
    row += _ROW_SPACING * 2  # extra space for the input panels

    readme_input_names = [
        "Headline", "Summary", "Tags", "Authors",
        "Headline Image", "Origin Story",
        "Detailed description", "Repo URL",
    ]
    readme_demo_data = {
        "Headline": "My Grasshopper Definition",
        "Summary": "A short description of what this does",
        "Tags": "grasshopper\ncomputational-design",
        "Authors": "Your Name @github-handle",
        "Headline Image": "https://example.com/image.png",
        "Origin Story": "Why this file came into being",
        "Detailed description": "A longer explanation of the definition",
        "Repo URL": "https://github.com/org/repo",
    }
    readme_panels = []
    for i, name in enumerate(readme_input_names):
        panel = _add_or_update_panel(
            gh_doc, name,
            ox + _README_COL_PANELS,
            oy + row + i * 50,
            content=readme_demo_data.get(name, ""))
        readme_panels.append(panel)

    readme_code = _wrapper_code(
        "mirror_readme", "generate_readme", "a", lib_path,
        extra_args=(",\n"
                    "                    headline, tiny_description, "
                    "tags, authors,\n"
                    "                    headline_image_url, summary, "
                    "origin_story,\n"
                    "                    detailed_description, repo_url"))
    readme_py3 = _add_or_update_py3(
        gh_doc, "Mirror README", readme_code,
        ox + _README_COL_SCRIPT, oy + row + len(readme_input_names) * 25,
        input_names=["headline", "tiny_description", "tags", "authors",
                     "headline_image_url", "summary", "origin_story",
                     "detailed_description", "repo_url"],
        output_names=["result", "a"],
        input_access={"tags": 1, "authors": 1})
    readme_output = _add_or_update_panel(
        gh_doc, "README output",
        ox + _README_COL_OUTPUT, oy + row + len(readme_input_names) * 25)

    # Wire input panels to the Py3 node's inputs
    if readme_py3:
        param_map = {
            "Headline": 0,
            "Summary": 1,     # tiny_description
            "Tags": 2,
            "Authors": 3,
            "Headline Image": 4,
            "Origin Story": 5,  # summary param — NOTE: may need reordering
            "Detailed description": 6,
            "Repo URL": 7,
        }
        for panel, name in zip(readme_panels, readme_input_names):
            idx = param_map.get(name)
            if idx is not None and panel:
                _wire(gh_doc, panel, 0, readme_py3, idx)
        _wire(gh_doc, readme_py3, 1, readme_output, 0)
    results.append(f"README: {'updated' if readme_py3 else 'SKIPPED'}")

    readme_objects = [o for o in [readme_py3, readme_output] + readme_panels if o]
    readme_grp = _group_objects(gh_doc, readme_objects, "README Generation")

    # --- Outer group ---
    all_subgroup_objects = (
        topo_objects + layout_objects + data_objects +
        canvas_objects + readme_objects +
        [topo_grp, layout_grp, data_grp, canvas_grp, readme_grp]
    )
    all_subgroup_objects = [o for o in all_subgroup_objects if o]
    _group_objects(gh_doc, all_subgroup_objects, "Grasshopper Mirror")

    # Refresh
    gh_doc.NewSolution(False)
    canvas.Refresh()

    return "Scaffold complete:\n" + "\n".join(results)
