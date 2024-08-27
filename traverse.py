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

# from future import print_function


def traverse_grasshopper_graph():
    # Get the active Grasshopper document
    gh_doc = gh.Instances.ActiveCanvas.Document

    # Dictionary to store nodes and edges
    nodes = {}
    edges = []

    # Iterate through all objects in the document
    for obj in gh_doc.Objects:
        if isinstance(obj, ghk.IGH_Component):
            # Add node
            node_id = obj.InstanceGuid.ToString()
            nodes[node_id] = {
                "name": obj.Name,
                "inputs": [],
                "outputs": [],
                "value": None,  # Placeholder for node value
            }

            # Iterate through input parameters
            for input_param in obj.Params.Input:
                for source in input_param.Sources:
                    if source.Attributes != None:
                        if source.Attributes.Parent != None:
                            source_id = source.Attributes.Parent.InstanceGuid.ToString()
                            nodes[node_id]["inputs"].append(source_id)
                            edges.append((source_id, node_id))

            # Iterate through output parameters
            for output_param in obj.Params.Output:
                for recipient in output_param.Recipients:
                    if recipient.Attributes != None:
                        if recipient.Attributes.Parent != None:
                            recipient_id = (
                                recipient.Attributes.Parent.InstanceGuid.ToString()
                            )
                            nodes[node_id]["outputs"].append(recipient_id)
                            edges.append((node_id, recipient_id))

    return nodes, edges


# Example usage
nodes, edges = traverse_grasshopper_graph()

print("Nodes:", nodes)
node_names = {}
for k, v in nodes.items():
    node_names[k] = v["name"].replace(" ", "_") + "\n" + k
print("node_names", node_names)
nodes = node_names.values()

new_edges = []
for e in edges:
    new_edges.append(
        '"' + node_names[e[0]] + '"' + " -> " + '"' + node_names[e[1]] + '"'
    )
edges = new_edges
print("Edges:", new_edges)
