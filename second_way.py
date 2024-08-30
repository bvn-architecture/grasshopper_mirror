import Grasshopper as gh
import Grasshopper.Kernel as ghk


def get_colour(i):
    colours = [
        "blueviolet",
        "brown",
        "burlywood",
        "cadetblue",
        "chartreuse",
        "chocolate",
        "coral",
        "cornflowerblue",
        "cornsilk",
        "crimson",
        "cyan",
        "orangered",
        "orchid",
    ]
    return colours[i % len(colours)]


def make_fully_qualified_name(obj):
    node_id = obj.InstanceGuid.ToString()
    fq_name = "{0}_{1}".format(obj.NickName, node_id)
    return fq_name


def make_nick_name(obj):
    nick_name = obj.NickName
    if nick_name != obj.Name:
        nick_name = "{}\\n({})".format(nick_name, obj.Name)
    return nick_name


def make_centre_node(index, nick_name, fq_name, fontsize=20):
    return '"{}" [label="{}", fillcolor="{}", fontsize={}];\n    '.format(
        fq_name, nick_name, get_colour(index), fontsize
    )


def make_node_subgraph(index, node_id, nick_name, internal_connections_dot, params_dot):
    g = """
#{4}
subgraph "cluster_subgraph_{0}" {{
    node [style=filled];
    nodesep="0.05";
    style="rounded";
    label = "{1}";
    # Nodes
    {2}
    # Edges
    {3}
}}
""".format(
        node_id, nick_name, params_dot, internal_connections_dot, index
    )
    return g


def simple_edge(from_node="in", to_node="out", num_spaces=4, edge_label=""):
    if edge_label:
        edge_label = ' [label="{}"]'.format(edge_label)
    edge = '"{f}" -> "{t}" {el};\n{num_spaces}'.format(
        f=from_node, t=to_node, num_spaces=" " * num_spaces, el=edge_label
    )
    return edge.replace('""', '"')


def generate_internal_connections(index, obj):
    node_id = obj.InstanceGuid.ToString()
    fq_name = make_fully_qualified_name(obj)
    centre_label = make_centre_node(index, make_nick_name(obj), fq_name)
    params_dot = "" + centre_label
    internal_connections_dot = ""

    # Enumerate inputs
    for input_param in obj.Params.Input:
        node_name = '"{nick}_in_{id}"'.format(nick=input_param.NickName, id=node_id)
        params_dot += make_node_def(input_param, node_name)
        internal_connections_dot += simple_edge(
            from_node=node_name, to_node=fq_name, edge_label="r i in"
        )

    # Enumerate outputs
    for output_param in obj.Params.Output:
        node_name = '"{nick}_out_{id}"'.format(nick=output_param.NickName, id=node_id)
        params_dot += make_node_def(output_param, node_name)
        internal_connections_dot += simple_edge(
            from_node=fq_name, to_node=node_name, edge_label="r i out"
        )

    return internal_connections_dot, params_dot


def generate_internal_connections_sources(index, obj, value):
    node_id = obj.InstanceGuid.ToString()
    nick_name = make_nick_name(obj)
    fq_name = make_fully_qualified_name(obj)
    internal_connections_dot = ""
    params_dot = (
        '"{}" [label="{}\\nValue: {}", fillcolor="{}", fontsize=20];\n    '.format(
            fq_name, nick_name, value, get_colour(index)
        )
    )
    if obj.Sources:
        node_name = '"{nick}_in_{id}"'.format(nick=obj.NickName, id=node_id)
        params_dot += '{} [label="in →•"];\n    '.format(node_name)
        internal_connections_dot += simple_edge(
            from_node=node_name, to_node=fq_name, edge_label="leaf i in"
        )
    if obj.Recipients:
        node_name = '"{nick}_out_{id}"'.format(nick=obj.NickName, id=node_id)
        params_dot += '{} [label="•→ out"];\n    '.format(node_name)
        internal_connections_dot += simple_edge(
            from_node=fq_name, to_node=node_name, edge_label="leaf i out"
        )

    return internal_connections_dot, params_dot


def make_node_def(input_param, node_name):
    return '{node_name} [label="{nick}\\n{type_name}"];\n    '.format(
        node_name=node_name,
        nick=input_param.NickName,
        type_name=type(input_param).__name__,
    )


def generate_connections_dot(connections_dot, obj, node_id):
    connections_dot += "# Connections for {}\n".format(obj.NickName)
    # Enumerate inputs
    for input_param in obj.Params.Input:
        node_name = '"{nick}_in_{id}"'.format(nick=input_param.NickName, id=node_id)
        for source in input_param.Sources:
            source_node_name = '"{nick}_out_{id}"'.format(
                nick=source.NickName, id=source.InstanceGuid.ToString()
            )
            connections_dot += simple_edge(source_node_name, node_name)

    # Enumerate outputs
    for output_param in obj.Params.Output:
        node_name = '"{nick}_out_{id}"'.format(nick=input_param.NickName, id=node_id)
        for recipient in output_param.Recipients:
            recipient_node_name = '"{}_in_{}"'.format(
                recipient.NickName, recipient.InstanceGuid.ToString()
            )
            connections_dot += simple_edge(node_name, recipient_node_name)

    return connections_dot


def generate_connections_dot_sources(connections_dot, obj):
    # TODO: I don't think this does anything, remove it
    fq_name = make_fully_qualified_name(obj)
    for source in obj.Sources:
        source_node_name = '"{}_out_{}"'.format(
            source.NickName, source.InstanceGuid.ToString()
        )
        # connections_dot += simple_edge(
        #     source_node_name, fq_name, edge_label="between Source"
        # )

    for recipient in obj.Recipients:
        recipient_node_name = '"{}_in_{}"'.format(
            recipient.NickName, recipient.InstanceGuid.ToString()
        )
        # connections_dot += simple_edge(
        #     fq_name, recipient_node_name, edge_label="between Recipients"
        # )

    return connections_dot


def get_value(obj):
    try:
        # Access the value
        value = obj.VolatileData.get_Branch(0)[0]
    except:
        value = obj.VolatileData
    return value


def main():
    # Get the active Grasshopper document
    gh_doc = gh.Instances.ActiveCanvas.Document

    subgraphs = ""
    connections_dot = ""

    for index, obj in enumerate(gh_doc.Objects):
        node_id = obj.InstanceGuid.ToString()
        nick_name = make_nick_name(obj)
        fq_name = make_fully_qualified_name(obj)
        print(
            "{} | Object: {}, Type: {} GUID: {}".format(
                index, nick_name, type(obj).__name__, node_id
            )
        )

        if hasattr(obj, "Params"):
            internal_connections_dot, params_dot = generate_internal_connections(
                index, obj
            )
            connections_dot = generate_connections_dot(connections_dot, obj, node_id)
            g = make_node_subgraph(
                index, node_id, nick_name, internal_connections_dot, params_dot
            )
            subgraphs += g

        elif hasattr(obj, "Sources"):
            value = get_value(obj)
            internal_connections_dot, params_dot = (
                generate_internal_connections_sources(index, obj, value)
            )
            connections_dot = generate_connections_dot_sources(connections_dot, obj)
            g = make_node_subgraph(
                index, node_id, nick_name, internal_connections_dot, params_dot
            )
            subgraphs += g

        else:
            print("some other kind of object encountered", obj)
            # This is where we'll handle things like groups

    graph = """digraph G {{
    rankdir = LR;
    # Subgraphs
    {0}
    # Generated Connections
    {1}
    # Manually Connected Connections
    # These are the connections that I've manually created that actually connect the graph the way it ought to be connected.
    # These should be automatically generated, but I can't work out why they're not yet.
    #
}}""".format(
        subgraphs, connections_dot
    )

    return graph


graph = main()
