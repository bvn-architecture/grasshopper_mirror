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
subgraph "cluster_subgraph_{0}" {{
    node [style=filled];
    nodesep="0.05";
    style="rounded";
    label = "{1}";
    # Nodes
    {2}
    # Edges
    {3}
    #{4}
  }}
""".format(
        node_id, nick_name, params_dot, internal_connections_dot, index
    )
    return g


def generate_internal_connections(index, obj, node_id, fq_name):
    internal_connections_dot = ""
    nick_name = make_nick_name(obj)
    centre_label = make_centre_node(index, nick_name, fq_name)
    params_dot = "" + centre_label

    # Enumerate inputs
    for input_param in obj.Params.Input:
        node_name = '"{nick}_in_{id}"'.format(nick=input_param.NickName, id=node_id)
        params_dot += '{node_name} [label="{nick} \\n{type_name}"];\n    '.format(
            node_name=node_name,
            nick=input_param.NickName,
            type_name=type(input_param).__name__,
        )
        internal_connections_dot += '{node_name} -> "{fq_name}";\n    '.format(
            node_name=node_name, fq_name=fq_name
        )

    # Enumerate outputs
    for output_param in obj.Params.Output:
        node_name = '"{}_out_{}"'.format(output_param.NickName, node_id)
        params_dot += '{} [label="{} \\n{}"];\n    '.format(
            node_name, output_param.NickName, type(output_param).__name__
        )
        internal_connections_dot += '"{}" -> {};\n    '.format(fq_name, node_name)

    return internal_connections_dot, params_dot


def generate_internal_connections_sources(index, obj, value):
    nick_name = make_nick_name(obj)
    fq_name = make_fully_qualified_name(obj)
    internal_connections_dot = ""
    params_dot = (
        '"{}" [label="{}\\nValue: {}", fillcolor="{}", fontsize=20];\n    '.format(
            fq_name, nick_name, value, get_colour(index)
        )
    )
    if obj.Sources:
        params_dot += '"{0}_in" [label="in →•"];'.format(fq_name)
        internal_connections_dot += '"{0}_in" -> "{0}";\n    '.format(fq_name)
    if obj.Recipients:
        params_dot += '"{0}_out" [label="•→ out"];'.format(fq_name)
        internal_connections_dot += '"{0}" -> "{0}_out";\n    '.format(fq_name)

    return internal_connections_dot, params_dot


def generate_connections_dot(connections_dot, obj, node_id):
    # Enumerate inputs
    for input_param in obj.Params.Input:
        node_name = '"{nick}_in_{id}"'.format(nick=input_param.NickName, id=node_id)
        for source in input_param.Sources:
            source_node_name = '"{nick}_out_{id}"'.format(
                nick=source.NickName, id=source.InstanceGuid.ToString()
            )
            connections_dot += "{} -> {};\n    ".format(source_node_name, node_name)

    # Enumerate outputs
    for output_param in obj.Params.Output:
        node_name = '"{}_out_{}"'.format(output_param.NickName, node_id)
        for recipient in output_param.Recipients:
            recipient_node_name = '"{}_in_{}"'.format(
                recipient.NickName, recipient.InstanceGuid.ToString()
            )
            connections_dot += "{} -> {};\n    ".format(node_name, recipient_node_name)

    return connections_dot


def generate_connections_dot_sources(connections_dot, obj):
    fq_name = make_fully_qualified_name(obj)
    for source in obj.Sources:
        source_node_name = '"{}_out_{}"'.format(
            source.NickName, source.InstanceGuid.ToString()
        )
        connections_dot += '{} -> "{}_in";\n    '.format(source_node_name, fq_name)

    for recipient in obj.Recipients:
        recipient_node_name = '"{}_in_{}"'.format(
            recipient.NickName, recipient.InstanceGuid.ToString()
        )
        connections_dot += '"{}_out" -> {};\n    '.format(fq_name, recipient_node_name)

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
                index, obj, node_id, fq_name
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
    # These are the connections that I've manually created that actually connect teh graph the way it ought to be connected.
    # These should be automatically generated, but I can't work out why they're not yet.
    "V_out_296e8b38-2af3-4633-aa6e-20cd8f0bcac8" -> "T_in_d8a179fc-7fab-4814-b4b9-20be26bfe82c";
    "G_out_d8a179fc-7fab-4814-b4b9-20be26bfe82c" -> "O_in_cdffa07a-a8b6-4077-978a-eda881b24570";
    "P_out_cdffa07a-a8b6-4077-978a-eda881b24570" -> "P_in_5ad19c48-1e9f-4067-8bc7-fa66cd4a694e";
    "base_out_a6456689-42ae-4206-a7a4-5324d1a4934a" -> "R1_in_5ad19c48-1e9f-4067-8bc7-fa66cd4a694e";
    "base_out_10f0c688-9b64-4a5b-97aa-419aa174c25c" -> "R2_in_5ad19c48-1e9f-4067-8bc7-fa66cd4a694e";
    "height_87d28aaa-18a9-41a5-86b7-4c1685edb815_out" -> "height_in_a6456689-42ae-4206-a7a4-5324d1a4934a";
    "height_87d28aaa-18a9-41a5-86b7-4c1685edb815_out" -> "height_in_10f0c688-9b64-4a5b-97aa-419aa174c25c";
    "height_87d28aaa-18a9-41a5-86b7-4c1685edb815_out" -> "A_in_296e8b38-2af3-4633-aa6e-20cd8f0bcac8";
    "small_angle_d9728bb0-9967-449f-b352-182acd5a7aef_out" -> "D_in_59cb3897-f400-43f3-9461-0701f2ceb61b";
    "big_angle_14465b62-ae35-49a8-bba2-e50b935551b5_out" -> "D_in_2a326121-470f-4022-9477-ef4b47e3853d";
    "R_out_59cb3897-f400-43f3-9461-0701f2ceb61b" -> "angle_in_10f0c688-9b64-4a5b-97aa-419aa174c25c";
    "R_out_2a326121-470f-4022-9477-ef4b47e3853d" -> "angle_in_a6456689-42ae-4206-a7a4-5324d1a4934a";
    "S_out_71ee981e-b545-4cb0-907c-8955b015922f" -> "G_in_d8a179fc-7fab-4814-b4b9-20be26bfe82c";
    "Line_6c767123-f309-40da-af83-09b32ece5832_out"->"C_in_71ee981e-b545-4cb0-907c-8955b015922f";
    "Line_6c767123-f309-40da-af83-09b32ece5832_out"->"Vec_be341bd1-f76a-45e9-a82c-b36bca905729_in";
    "Crv_a4599816-cbc1-40cb-af2f-95c15603b142_out"->"C_in_41047c00-e8c0-42f0-99aa-d3177a8bd895";
    "C_out_41047c00-e8c0-42f0-99aa-d3177a8bd895"->"Line_6c767123-f309-40da-af83-09b32ece5832_in";
    "big_angle_14465b62-ae35-49a8-bba2-e50b935551b5_out"->"_2f48438c-75c3-443c-a1c8-95eccd8670fc_in"
    "small_angle_d9728bb0-9967-449f-b352-182acd5a7aef_out" -> "_db3162a4-9892-487b-b2fa-a2d005e3726b_in"
    "E_out_5ad19c48-1e9f-4067-8bc7-fa66cd4a694e" -> "trigger_in_6ff0ff7e-a539-4919-acff-d2ed22901e68";
    "graph_out_6ff0ff7e-a539-4919-acff-d2ed22901e68" -> "dot panel_51209a31-00e0-4b05-b172-4c0230265a66_in";

}}""".format(
        subgraphs, connections_dot
    )

    return graph


graph = main()
