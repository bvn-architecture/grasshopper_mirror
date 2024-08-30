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
        "orchid"
    ]
    return colours[i % len(colours)]

# Get the active Grasshopper document
gh_doc = gh.Instances.ActiveCanvas.Document

subgraphs = ""
connections_dot = ""

for index, obj in enumerate(gh_doc.Objects):
    node_id = obj.InstanceGuid.ToString()
    nn = obj.NickName
    if nn != obj.Name:
        nn = "{}\\n({})".format(nn, obj.Name)
    fq_name = '{0}_{1}'.format(obj.NickName, node_id)
    print "{} | Object: {}, Type: {} GUID: {}".format(index, nn, type(obj).__name__, node_id)
    
    if hasattr(obj, 'Params'):
        # Enumerate inputs
        internal_connections_dot = ""
        params_dot = '"{}" [label="{}", fillcolor="{}", fontsize=20];\n    '.format(fq_name, nn, get_colour(index))
        for input_param in obj.Params.Input:
            node_name = '"{}_in_{}"'.format(input_param.NickName, node_id)
            params_dot += '{} [label="{} \\n{}"];\n    '.format(node_name, input_param.NickName, type(input_param).__name__)
            internal_connections_dot += '{} -> "{}";\n    '.format(node_name, fq_name)
            
            # Add connections from sources to this input
            for source in input_param.Sources:
                source_node_name = '"{}_out_{}"'.format(source.NickName, source.InstanceGuid.ToString())
                connections_dot += '{} -> {};\n    '.format(source_node_name, node_name)
        
        # Enumerate outputs
        for output_param in obj.Params.Output:
            node_name = '"{}_out_{}"'.format(output_param.NickName, node_id)
            params_dot += '{} [label="{} \\n{}"];\n    '.format(node_name, output_param.NickName, type(output_param).__name__)
            internal_connections_dot += '"{}" -> {};\n    '.format(fq_name, node_name)
            
            # Add connections from this output to recipients
            for recipient in output_param.Recipients:
                recipient_node_name = '"{}_in_{}"'.format(recipient.NickName, recipient.InstanceGuid.ToString())
                connections_dot += '{} -> {};\n    '.format(node_name, recipient_node_name)
        
        subgraphs += """
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
""".format(node_id, nn, params_dot, internal_connections_dot, index)
  
  
    else:
        
        # print("____does not have Params property")
        if hasattr(obj, 'Sources'):
            # Access the value
            try:
                value = obj.VolatileData.get_Branch(0)[0]
            except:
                value = obj.VolatileData
            print("____Value: {}".format(value))
            internal_connections_dot = ""
            params_dot = '"{}" [label="{}\\nValue: {}", fillcolor="{}", fontsize=20];\n    '.format(fq_name, nn, value, get_colour(index))
            if obj.Sources:
                params_dot += '"{0}_in" [label="in →•"];'.format(fq_name)
                internal_connections_dot += '"{0}_in" -> "{0}";\n    '.format(fq_name)
            if obj.Recipients:
                params_dot += '"{0}_out" [label="out •→"];'.format(fq_name)
                internal_connections_dot += '"{0}" -> "{0}_out";\n    '.format(fq_name)

            # Inspect connections
            print "Sources", len(obj.Sources), "Recipients", len(obj.Recipients)
            for source in obj.Sources:
                print("____Connected to: {}, Type: {}".format(source.NickName, type(source).__name__))
                source_node_name = '"{}_out_{}"'.format(source.NickName, source.InstanceGuid.ToString())
                connections_dot += '{} -> "{}_in";\n    '.format(source_node_name, fq_name)

            for recipient in obj.Recipients:
                print("____Recipient: {}, Type: {}".format(recipient.NickName, type(recipient).__name__))
                recipient_node_name = '"{}_in_{}"'.format(recipient.NickName, recipient.InstanceGuid.ToString())
                connections_dot += '"{}_out" -> {};\n    '.format(fq_name, recipient_node_name)
                
            subgraphs += """
subgraph "cluster_subgraph__{0}" {{
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
""".format(node_id, nn, params_dot, internal_connections_dot, index)

graph = """digraph G {{
    rankdir = LR;
    
    {0}
    
    {1}
    
    # Manually connected
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

}}""".format(subgraphs, connections_dot)

print(graph)
