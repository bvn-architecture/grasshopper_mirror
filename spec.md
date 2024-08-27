# GH2DOT

I've started hacking on this, with a pretty copilot heavy process.

The ideal is that it'll give us something that we're able to keep with GH files that is able to be version controlled.

Here's the spec that I got copilot to prompt me for details:

---

It's a tool that inspects/reflects the graph of grasshopper components on the canvas.
It will output a dot file that captures the topology of the graph. 
The graph nodes have multiple inputs and outputs, so it'll probably need a Record-based Node because where the edge is connected matters. But I'm open to other suggestions on how to construct each node. It may be a subgraph or cluster.

Ideally I'll be written in python and run in a python node in the graph, or be a C# component.

The dot file will be put into a folder with the .gh file. That folder will then be initialised as a git repo and pushed to github.

This version won't worry about the data that's passed through the nodes, but it might capture the values of input leaf-nodes if they're easily serialisable (e.g. numbers or strings). Values that aren't easily serialised should contain 100 chars or so of the python repr version of their data value.

The edges don't have any special values, other than the nodes that they connect.

Each node can have multiple input sockets and multiple output sockets.
Each output socket can have multiple edges coming out of it, and each Input socket can have multiple edges going into it. 
However, a node can't be connected to itself, and any given pair of sockets can have 1 or 0 edges between them.

I'd prefer it to be python, as I'm more comfortable with that, as are more grasshopper users. However, there may be elements of the sdk that aren't accessible through python.

It should be packaged as a node, that is added to the canvas. The the configuration details are added to the input components of that node. 

The github repo will have protection on the main branch, but have a very loose permissions structure on the branches.

The dot file will be called <filename>_topology.dot where filename is the name of the grasshopper file, without the .gh extension. 

Each folder should also have a readme.md that has some details about the grasshoper file, and a docs folder that will contain images that are referenced into the readme file.

There are no performance concerns. Grasshopper graphs are relatively small. Less than 100 nodes usually.

> Yes, I think you have enough detail to start writing a prototype in Python! Here's a summary of your spec to guide you:


**Tool Description:**
- **Purpose:** Inspect and reflect the graph of Grasshopper components on the canvas.
- **Output:** Generates a dot file capturing the topology of the graph.

**Graph Structure:**
- **Nodes:** 
  - Multiple input and output sockets.
  - Record-based nodes to capture where edges are connected.
  - No self-connections.
  - Each pair of sockets can have at most one edge between them.
- **Edges:** 
  - No special values, only connect nodes.

**Implementation:**
- **Language:** Python.
- **Integration:** Packaged as a node added to the Grasshopper canvas. Configuration details are added to the input components of this node.

**Output Details:**
- **Dot File:**
  - Named `<filename>_topology.dot` where `<filename>` is the Grasshopper file name without the `.gh` extension.
  - Stored in the same folder as the `.gh` file.
- **Serialization:**
  - Capture values of input leaf-nodes if easily serializable (e.g., numbers, strings).
  - For non-serializable values, include up to 100 characters of the Python `repr` version of the data value.

**Git Integration:**
- **Repository Initialization:**
  - Initialize the folder as a git repository.
  - Push to GitHub.
  - Main branch protection with loose permissions on other branches.
- **Additional Files:**
  - `README.md` with details about the Grasshopper file.
  - `docs` folder containing images referenced in the `README.md`.

**Error Handling:**
- Throw standard Python errors or create an error node colored red.
- Maintain as much topology as possible.

**Configuration:**
- Handled through input components.

**Performance:**
- No significant concerns as Grasshopper graphs are typically small (less than 100 nodes).

The code in `main.py` starts work on making it a proper piece of software, and the code in `traverse.py` is starting to be able to reflect a grasshopper file from within.

## Example diagrams

This shows that graphviz can show a structured node that parallels a grasshopper node.

![](docs\structured_nodes.png)

```
graph mygraph {
  node [shape=record, fontsize=10, fontname=Arial];
  rankdir=LR;
  ranksep=0.5;
  rank=max;
  splines=true;
  overlap=false;
  mindist=0.2;

  node1 [shape=record, margin=0, label=<
    <table border="0" cellborder="1" cellspacing="0" cellpadding="4">
      <tr><td port="1">1</td><td rowspan="3">Node1</td><td port="A">A</td></tr>
      <tr><td port="2">2</td><td port="B">B</td></tr>
      <tr><td port="3">3</td><td port="C">C</td></tr>
    </table>>];

  node2 [shape=record, margin=0, label=<
    <table border="0" cellborder="1" cellspacing="0" cellpadding="4">
      <tr><td port="1">1</td><td rowspan="3">Node2</td><td port="A">A</td></tr>
      <tr><td port="2">2</td><td port="B">B</td></tr>
      <tr><td port="3">3</td><td port="C">C</td></tr>
    </table>>];
    

  node1:A -> node2:1 [color=blue, penwidth=3, tooltip="node1:A -- node2:1", URL="#"];
  node1:B -> node2:2 [color=blue, penwidth=3, tooltip="node1:B -- node2:2", URL="#"];
  node1:C -> node2:3 [color=blue, penwidth=3, tooltip="node1:C -- node2:3", URL="#"];
}
```

And this example shows that we're actually able to parse a grasshopper file for the topology.

![](docs\nodes_from_gh.png)

![](docs\GH_source_file.PNG)

```
digraph G {
    node [fontsize=10, fontname=Arial];
    rankdir=LR;
    ranksep=0.5;
    rank=max;
    splines=true;
    overlap=false;
    mindist=0.2;
    "XY_Plane\ncdffa07a-a8b6-4077-978a-eda881b24570" -> "Ellipse\n5ad19c48-1e9f-4067-8bc7-fa66cd4a694e"
    "Cluster\na6456689-42ae-4206-a7a4-5324d1a4934a" -> "Ellipse\n5ad19c48-1e9f-4067-8bc7-fa66cd4a694e"
    "Cluster\n10f0c688-9b64-4a5b-97aa-419aa174c25c" -> "Ellipse\n5ad19c48-1e9f-4067-8bc7-fa66cd4a694e"
    "Radians\n59cb3897-f400-43f3-9461-0701f2ceb61b" -> "Cluster\n10f0c688-9b64-4a5b-97aa-419aa174c25c"
    "Radians\n2a326121-470f-4022-9477-ef4b47e3853d" -> "Cluster\na6456689-42ae-4206-a7a4-5324d1a4934a"
    "Move\nd8a179fc-7fab-4814-b4b9-20be26bfe82c" -> "XY_Plane\ncdffa07a-a8b6-4077-978a-eda881b24570"
    "XY_Plane\ncdffa07a-a8b6-4077-978a-eda881b24570" -> "Ellipse\n5ad19c48-1e9f-4067-8bc7-fa66cd4a694e"
    "End_Points\n71ee981e-b545-4cb0-907c-8955b015922f" -> "Move\nd8a179fc-7fab-4814-b4b9-20be26bfe82c"
    "Amplitude\n296e8b38-2af3-4633-aa6e-20cd8f0bcac8" -> "Move\nd8a179fc-7fab-4814-b4b9-20be26bfe82c"
    "Move\nd8a179fc-7fab-4814-b4b9-20be26bfe82c" -> "XY_Plane\ncdffa07a-a8b6-4077-978a-eda881b24570"
    "End_Points\n71ee981e-b545-4cb0-907c-8955b015922f" -> "Move\nd8a179fc-7fab-4814-b4b9-20be26bfe82c"
    "Amplitude\n296e8b38-2af3-4633-aa6e-20cd8f0bcac8" -> "Move\nd8a179fc-7fab-4814-b4b9-20be26bfe82c"
    "Radians\n59cb3897-f400-43f3-9461-0701f2ceb61b" -> "Cluster\n10f0c688-9b64-4a5b-97aa-419aa174c25c"
    "Cluster\n10f0c688-9b64-4a5b-97aa-419aa174c25c" -> "Ellipse\n5ad19c48-1e9f-4067-8bc7-fa66cd4a694e"
    "Radians\n2a326121-470f-4022-9477-ef4b47e3853d" -> "Cluster\na6456689-42ae-4206-a7a4-5324d1a4934a"
    "Cluster\na6456689-42ae-4206-a7a4-5324d1a4934a" -> "Ellipse\n5ad19c48-1e9f-4067-8bc7-fa66cd4a694e"
}
```

It leaves out a lot of nodes, and it could definitely be clearer (i.e. hiding the node uid, and just showing the name, and also parsing it into records that look like the gh node.)

BUT IT'S A START

Please, pick this up and hack some more