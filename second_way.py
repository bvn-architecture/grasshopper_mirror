import Grasshopper as gh
import Grasshopper.Kernel as ghk

# Get the active Grasshopper document
gh_doc = gh.Instances.ActiveCanvas.Document

subgraphs = ""

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
        params_dot = '"{}" [label="{}", fillcolor="pink", fontsize=20];\n    '.format(fq_name, nn)
        for input_param in obj.Params.Input:
            node_name = '"{}_in_{}"'.format(input_param.NickName, node_id)
            params_dot += '{} [label="{} \\n{}"];\n    '.format(node_name, input_param.NickName, type(input_param).__name__)
            internal_connections_dot += '{} -> "{}";\n    '.format(node_name, fq_name)
        
        # Enumerate outputs
        for output_param in obj.Params.Output:
            node_name = '"{}_out_{}"'.format(output_param.NickName, node_id)
            params_dot += '{} [label="{} \\n{}"];\n    '.format(node_name, output_param.NickName, type(input_param).__name__)
            internal_connections_dot += '"{}" -> {};\n    '.format(fq_name, node_name)

        subgraphs += """
subgraph "cluster_{0}" {{
    node [style=filled];
    label = "{1}";
    {2}
    
    {3}
  }}""".format(node_id, nn, params_dot, internal_connections_dot)
    else:
        print("____does not have Params property")
        if hasattr(obj, 'Sources'):
            # Access the value
            try:
                value = obj.VolatileData.get_Branch(0)[0]
            except:
                value = obj.VolatileData
            print("____Value: {}".format(value))
            
            # Inspect connections
            for source in obj.Sources:
                print("____Connected to: {}, Type: {}".format(source.NickName, type(source).__name__))
            for recipient in obj.Recipients:
                print("____Recipient: {}, Type: {}".format(recipient.NickName, type(recipient).__name__))
                
                
graph = """digraph G {{
    rankdir = LR;
    
    {}
}}""".format(subgraphs)