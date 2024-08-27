import os
import json
import subprocess
from graphviz import Digraph


class GrasshopperGraphInspector:
    def __init__(self, gh_file_path):
        self.gh_file_path = gh_file_path
        self.graph = Digraph(comment="Grasshopper Graph")
        self.nodes = {}
        self.edges = []

    def inspect_graph(self):
        # Placeholder for inspecting the Grasshopper graph
        # This should be replaced with actual code to inspect the Grasshopper canvas
        # For now, we'll use a mock graph structure
        self.nodes = {
            "A": {"inputs": [], "outputs": ["B", "C"], "value": 42},
            "B": {"inputs": ["A"], "outputs": ["D"], "value": "Hello"},
            "C": {"inputs": ["A"], "outputs": ["D"], "value": [1, 2, 3]},
            "D": {"inputs": ["B", "C"], "outputs": [], "value": None},
        }
        self.edges = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")]

    def generate_dot_file(self):
        for node, data in self.nodes.items():
            label = f"{node}\nValue: {self.serialize_value(data['value'])}"
            self.graph.node(node, label=label)

        for edge in self.edges:
            self.graph.edge(edge[0], edge[1])

        dot_file_path = os.path.splitext(self.gh_file_path)[0] + "_topology.dot"
        self.graph.save(dot_file_path)
        print(f"Dot file saved to {dot_file_path}")

    def serialize_value(self, value):
        if isinstance(value, (int, float, str)):
            return value
        else:
            return repr(value)[:100]

    def initialize_git_repo(self):
        folder_path = os.path.dirname(self.gh_file_path)
        subprocess.run(["git", "init"], cwd=folder_path)
        subprocess.run(["git", "add", "."], cwd=folder_path)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=folder_path)
        subprocess.run(["git", "branch", "-M", "main"], cwd=folder_path)
        subprocess.run(
            ["git", "remote", "add", "origin", "<your-github-repo-url>"],
            cwd=folder_path,
        )
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=folder_path)
        print("Git repository initialized and pushed to GitHub")

    def create_readme_and_docs(self):
        folder_path = os.path.dirname(self.gh_file_path)
        readme_content = f"# {os.path.basename(self.gh_file_path)}\n\nDetails about the Grasshopper file."

        with open(os.path.join(folder_path, "README.md"), "w") as readme_file:
            readme_file.write(readme_content)

        docs_folder = os.path.join(folder_path, "docs")
        os.makedirs(docs_folder, exist_ok=True)

        # Placeholder for adding images to the docs folder
        # This should be replaced with actual code to generate and save images

        print("README.md and docs folder created")

    def run(self):
        try:
            self.inspect_graph()
            self.generate_dot_file()
            self.initialize_git_repo()
            self.create_readme_and_docs()
        except Exception as e:
            print(f"Error: {e}")
            # Placeholder for creating an error node and coloring it red
            # This should be replaced with actual code to handle errors in Grasshopper


# Example usage
gh_file_path = "example.gh"
inspector = GrasshopperGraphInspector(gh_file_path)
inspector.run()
