"""Provides a scripting component.
    Inputs:
        x: The x script variable
        y: The y script variable
    Output:
        a: The a output variable"""

__author__ = "bdoherty"
__version__ = "2024.08.27"

import rhinoscriptsyntax as rs
import Grasshopper as gh
import Grasshopper.Kernel as ghk
import Grasshopper.Kernel.Data as ghkd
import Grasshopper.Kernel.Types as ghkt

def traverse_grasshopper_graph():
    # Get the active Grasshopper document
    gh_doc = gh.Instances.ActiveCanvas.Document

    # Dictionary to store nodes and edges
    nodes = {}
    edges = []

    # Iterate through all objects in the document
    for obj in gh_doc.Objects:
        if isinstance(obj, (ghk.IGH_Param)):
            # Handle leaf nodes (e.g., numbers, curves)
            node_id = obj.InstanceGuid.ToString()
            node_name = obj.NickName.replace(" ", "_")
            nodes[node_id] = {
                "name": node_name,
                "inputs": [],
                "outputs": [],
                "value": repr(obj.VolatileData.get_Branch(0)[0])[:100] if obj.VolatileData.Count > 0 else None,
            }
        elif isinstance(obj, (ghk.IGH_Component)):
            # Add node
            if obj.VolatileData and obj.VolatileData.PathCount > 0:
                first_branch = obj.VolatileData.get_Branch(0)
                if len(first_branch) > 0:
                    value = repr(first_branch[0])[:100]
                else:
                    value = None
            else:
                value = None

            node_id = obj.InstanceGuid.ToString()
            node_name = obj.Name.replace(" ", "_")
            nodes[node_id] = {
                "name": node_name,
                "inputs": [],
                "outputs": [],
                "value": Value, 
            }

            # Capture leaf node values if easily serializable
            if all(not input_param.Sources for input_param in obj.Params.Input):
                try:
                    nodes[node_id]["value"] = repr(obj.VolatileData.get_Branch(0)[0])[:100]
                except:
                    nodes[node_id]["value"] = None

            # Iterate through input parameters
            for input_param in obj.Params.Input:
                for source in input_param.Sources:
                    if source.Attributes and source.Attributes.Parent:
                        source_id = source.Attributes.Parent.InstanceGuid.ToString()
                        nodes[node_id]["inputs"].append(source_id)
                        edges.append((source_id, node_id))

            # Iterate through output parameters
            for output_param in obj.Params.Output:
                for recipient in output_param.Recipients:
                    if recipient.Attributes and recipient.Attributes.Parent:
                        recipient_id = recipient.Attributes.Parent.InstanceGuid.ToString()
                        nodes[node_id]["outputs"].append(recipient_id)
                        edges.append((node_id, recipient_id))

    return nodes, edges

# Example usage
nodes, edges = traverse_grasshopper_graph()

# Convert nodes to record format
record_nodes = {}
for node_id, node_data in nodes.items():
    inputs = "".join('<tr><td port="in{0}">{1}</td></tr>'.format(i, node_data["inputs"][i]) for i in range(len(node_data["inputs"])))
    outputs = "".join('<tr><td port="out{0}">{1}</td></tr>'.format(i, node_data["outputs"][i]) for i in range(len(node_data["outputs"])))
    label = '<table border="0" cellborder="1" cellspacing="0" cellpadding="4"><tr><td colspan="2">{}</td></tr>{}{}</table>'.format(node_data['name'], inputs, outputs)
    record_nodes[node_id] = '"{}\\n{}" [shape=record, label=<{}>]'.format(node_data["name"], node_id, label)

# Convert edges to dot format
dot_edges = []
for source_id, target_id in edges:
    source_node = nodes[source_id]
    target_node = nodes[target_id]
    source_port = "out{0}".format(source_node['outputs'].index(target_id))
    target_port = "in{0}".format(target_node['inputs'].index(source_id))
    dot_edges.append('"{}\\n{}":{} -> "{}\\n{}":{}'.format(source_node["name"], source_id, source_port, target_node["name"], target_id, target_port))

# Print nodes and edges in dot format
print("Nodes:")
for node in record_nodes.values():
    print(node)

print("Edges:")
for edge in dot_edges:
    print(edge)

nodes = record_nodes.values()
edges = dot_edges
