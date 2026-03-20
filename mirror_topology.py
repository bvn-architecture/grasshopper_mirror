"""Grasshopper Mirror — Topology DOT Generator (Iteration 1)

Paste this into a GhPython Script node on the Grasshopper canvas.

    Node setup
    ----------
    Input:  trigger  — connect a button or any wire to trigger generation
    Output: graph    — the topology DOT string

Target: Rhino 8+ / CPython 3.9

Output format
-------------
DOT digraph with HTML-table record nodes:
  - Input ports on the left, component name in the centre, output ports
    on the right — mirroring the visual layout of a Grasshopper node.
  - Nodes and edges are sorted by GUID so the output is byte-identical
    when nothing on the canvas has changed.
  - GUIDs serve as DOT node identifiers (invisible in rendered graphs)
    and appear in comment lines for easy grepping in text diffs.
  - No values, no positions — topology only (per the Mirror spec).
"""

import Grasshopper as gh


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitize(name):
    """Alphanumeric + underscore only — safe for DOT port identifiers."""
    return "".join(c if c.isalnum() or c == "_" else "_" for c in name)


def _unique_port(base, seen):
    """Return *base* if unused in *seen*, otherwise append a numeric suffix."""
    candidate = base
    i = 2
    while candidate in seen:
        candidate = f"{base}{i}"
        i += 1
    seen.add(candidate)
    return candidate


def _esc(text):
    """Escape characters that are special inside HTML/DOT labels."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ---------------------------------------------------------------------------
# HTML-table label builder
# ---------------------------------------------------------------------------

def _html_label(nick, name, inputs, outputs, indent=8):
    """Build an HTML <table> label for one DOT node.

    Layout:  inputs (left) | component name (centre) | outputs (right)
    Returns a string like ``< ... >`` ready for a DOT ``label=`` attribute.
    """
    pad = " " * indent
    n_rows = max(len(inputs), len(outputs), 1)

    # Centre cell content — NickName, with (Name) on a smaller second line
    # if they differ.
    if nick and nick != name:
        centre = (
            f'{_esc(nick)}<br/>'
            f'<font point-size="10">({_esc(name)})</font>'
        )
    elif nick:
        centre = _esc(nick)
    else:
        centre = f'<font point-size="10">({_esc(name)})</font>'

    rows = []
    for i in range(n_rows):
        cells = []

        # Left column — input port
        if i < len(inputs):
            p = inputs[i]
            cells.append(f'<td port="{p["port"]}">{_esc(p["nick"])}</td>')
        else:
            cells.append("<td></td>")

        # Centre column (first row only, spanning all rows)
        if i == 0:
            cells.append(f'<td rowspan="{n_rows}">{centre}</td>')

        # Right column — output port
        if i < len(outputs):
            p = outputs[i]
            cells.append(f'<td port="{p["port"]}">{_esc(p["nick"])}</td>')
        else:
            cells.append("<td></td>")

        rows.append(f'{pad}    <tr>{"".join(cells)}</tr>')

    return (
        "<\n"
        f'{pad}<table border="0" cellborder="1" cellspacing="0" cellpadding="4">\n'
        + "\n".join(rows) + "\n"
        + f"{pad}</table>>"
    )


# ---------------------------------------------------------------------------
# Collection pass — nodes & parameter map
# ---------------------------------------------------------------------------

def _collect(gh_doc):
    """Walk the GH document and return ``(nodes, param_map, groups)``.

    * ``nodes`` — list of node dicts, sorted by GUID.
    * ``param_map`` — ``{param_guid_str: (parent_node_guid_str, port_id)}``
      Used to resolve the source end of every connection.
    * ``groups`` — list of group dicts, sorted by GUID.  Each has
      ``guid``, ``nick``, ``member_guids`` (set of str).
    """
    objects = sorted(gh_doc.Objects, key=lambda o: str(o.InstanceGuid))

    nodes = []
    param_map = {}
    groups = []

    for obj in objects:
        guid = str(obj.InstanceGuid)
        nick = obj.NickName or ""
        name = obj.Name or ""

        # -- Component (incl. Clusters, Script nodes) ----------------------
        if hasattr(obj, "Params"):
            seen_ports = set()

            inputs = []
            for p in obj.Params.Input:
                pg = str(p.InstanceGuid)
                port = _unique_port(_sanitize(p.NickName) + "_in", seen_ports)
                inputs.append({"nick": p.NickName, "port": port, "guid": pg})
                param_map[pg] = (guid, port)

            outputs = []
            for p in obj.Params.Output:
                pg = str(p.InstanceGuid)
                port = _unique_port(_sanitize(p.NickName) + "_out", seen_ports)
                outputs.append({"nick": p.NickName, "port": port, "guid": pg})
                param_map[pg] = (guid, port)

            nodes.append({
                "guid": guid, "nick": nick, "name": name,
                "kind": "component",
                "inputs": inputs, "outputs": outputs, "obj": obj,
            })

        # -- Leaf / standalone parameter (slider, panel, value, …) ---------
        elif hasattr(obj, "Sources"):
            has_src = obj.Sources is not None and len(obj.Sources) > 0
            has_rec = obj.Recipients is not None and len(obj.Recipients) > 0

            inputs = []
            outputs = []
            if has_src:
                inputs.append({"nick": "in", "port": "in", "guid": guid})
            if has_rec:
                outputs.append({"nick": "out", "port": "out", "guid": guid})

            # When this leaf appears as a *source* for another node's input,
            # the SDK reports this leaf's own GUID.  Map it to the "out" port.
            if has_rec:
                param_map[guid] = (guid, "out")

            nodes.append({
                "guid": guid, "nick": nick, "name": name,
                "kind": "leaf",
                "inputs": inputs, "outputs": outputs, "obj": obj,
            })

        # -- Group ---------------------------------------------------------
        elif hasattr(obj, "Objects") and callable(obj.Objects):
            member_guids = set()
            try:
                for member in obj.Objects():
                    member_guids.add(str(member.InstanceGuid))
            except Exception:
                pass
            groups.append({
                "guid": guid,
                "nick": nick or name or "unnamed_group",
                "member_guids": member_guids,
            })

        # -- Scribble / annotation / other ---------------------------------
        else:
            clr_type = obj.GetType().Name if hasattr(obj, "GetType") else "unknown"
            # Capture scribble text if available
            scribble_text = ""
            if hasattr(obj, "Text"):
                try:
                    scribble_text = str(obj.Text)
                except Exception:
                    pass
            nodes.append({
                "guid": guid, "nick": nick, "name": name,
                "kind": "other", "clr_type": clr_type,
                "scribble_text": scribble_text, "obj": obj,
            })

    return nodes, param_map, groups


# ---------------------------------------------------------------------------
# Edge collection
# ---------------------------------------------------------------------------

def _edges(nodes, param_map):
    """Return a deterministically sorted list of edges.

    Each edge is ``(src_node_guid, src_port, tgt_node_guid, tgt_port)``.
    """
    edges = []

    for node in nodes:
        guid = node["guid"]

        if node["kind"] == "component":
            # Build a quick lookup from param GUID → port id
            port_of = {inp["guid"]: inp["port"] for inp in node["inputs"]}

            for p in node["obj"].Params.Input:
                pg = str(p.InstanceGuid)
                tgt_port = port_of.get(pg)
                if tgt_port is None:
                    continue
                for src in p.Sources:
                    sg = str(src.InstanceGuid)
                    if sg in param_map:
                        sn, sp = param_map[sg]
                        edges.append((sn, sp, guid, tgt_port))

        elif node["kind"] == "leaf":
            obj = node["obj"]
            if obj.Sources:
                for src in obj.Sources:
                    sg = str(src.InstanceGuid)
                    if sg in param_map:
                        sn, sp = param_map[sg]
                        edges.append((sn, sp, guid, "in"))

    edges.sort()
    return edges


# ---------------------------------------------------------------------------
# DOT generation
# ---------------------------------------------------------------------------

def _dot(nodes, edges, groups):
    """Assemble the final DOT string from collected nodes and edges.

    Groups are emitted as nested ``subgraph cluster_<guid>`` blocks.
    A group that is a member of another group becomes a child subgraph.
    Nodes are placed in the deepest (innermost) group that claims them.
    Ungrouped nodes are emitted at the top level.
    """
    node_by_guid = {n["guid"]: n for n in nodes}
    group_by_guid = {g["guid"]: g for g in groups}
    group_guids = set(group_by_guid)

    # --- Build group hierarchy ---
    # A group is a child of another group if its GUID appears in the
    # parent's member_guids.
    group_parent = {}     # child_group_guid → parent_group_guid
    group_children = {}   # group_guid → [child_group_guids]
    for grp in groups:
        children = []
        for mg in grp["member_guids"]:
            if mg in group_guids:
                group_parent[mg] = grp["guid"]
                children.append(mg)
        children.sort()
        group_children[grp["guid"]] = children

    top_level_groups = sorted(
        [g for g in groups if g["guid"] not in group_parent],
        key=lambda g: g["guid"],
    )

    # --- Assign each node to its deepest (innermost) group ---
    # Walk groups smallest-first so the innermost group wins.
    node_to_group = {}  # node_guid → group_guid
    for grp in sorted(groups, key=lambda g: len(g["member_guids"])):
        for mg in grp["member_guids"]:
            if mg in node_by_guid:
                node_to_group[mg] = grp["guid"]

    # Collect direct child nodes per group (only nodes whose innermost
    # group is this one — not nodes that belong to a deeper child group).
    direct_nodes = {}  # group_guid → [node_guid, ...]
    for ng, gg in node_to_group.items():
        direct_nodes.setdefault(gg, []).append(ng)
    for k in direct_nodes:
        direct_nodes[k].sort()

    ungrouped = [n for n in nodes if n["guid"] not in node_to_group]

    # --- Helpers ---
    def _emit_node(n, indent=4):
        """Return DOT lines for a single node."""
        pad = " " * indent
        out = []
        if n["kind"] in ("component", "leaf"):
            label = _html_label(
                n["nick"], n["name"],
                n.get("inputs", []), n.get("outputs", []),
                indent=indent + 4,
            )
            comment_name = n["nick"] or n["name"]
            out.append(f'{pad}// {comment_name} (guid: {n["guid"]})')
            out.append(f'{pad}"{n["guid"]}" [margin=0, label={label}];')
            out.append("")
        elif n["kind"] == "other":
            obj_type = n.get("clr_type", "unknown")
            comment_name = n["nick"] or n["name"]
            scribble_text = n.get("scribble_text", "")
            out.append(
                f'{pad}// [skipped] {comment_name}'
                f' (type: {obj_type}, guid: {n["guid"]})'
            )
            if scribble_text:
                for line in scribble_text.splitlines():
                    out.append(f'{pad}//   {line}')
        return out

    def _emit_group(grp, indent=4):
        """Recursively emit a group as a subgraph cluster."""
        pad = " " * indent
        out = []
        out.append(f'{pad}// group: {grp["nick"]} (guid: {grp["guid"]})')
        out.append(f'{pad}subgraph "cluster_{grp["guid"]}" {{')
        out.append(f'{pad}    label="{_esc(grp["nick"])}";')

        # Emit child groups (nested subgraphs)
        for cg in group_children.get(grp["guid"], []):
            out.extend(_emit_group(group_by_guid[cg], indent=indent + 4))

        # Emit direct child nodes
        for ng in direct_nodes.get(grp["guid"], []):
            out.extend(_emit_node(node_by_guid[ng], indent=indent + 4))

        out.append(f'{pad}}}')
        out.append("")
        return out

    # --- Build output ---
    lines = [
        "digraph G {",
        "    rankdir=LR;",
        "    node [shape=plaintext];",
        "",
    ]

    # Emit group hierarchy (starting from top-level groups)
    if top_level_groups:
        lines.append("    // --- Groups ---")
        for grp in top_level_groups:
            lines.extend(_emit_group(grp))

    # Emit ungrouped nodes
    if ungrouped:
        lines.append("    // --- Nodes (ungrouped) ---")
        for n in ungrouped:
            lines.extend(_emit_node(n))

    lines.append("")
    lines.append("    // --- Edges ---")
    for sn, sp, tn, tp in edges:
        lines.append(f'    "{sn}":{sp} -> "{tn}":{tp};')

    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    gh_doc = gh.Instances.ActiveCanvas.Document
    nodes, param_map, groups = _collect(gh_doc)
    edges = _edges(nodes, param_map)
    return _dot(nodes, edges, groups)


graph = main()
