"""Dependency graph builder: modules and their imports."""

import json
from typing import Dict, List, Set
from pathlib import Path

from .utils import find_python_files, extract_imports, get_relative_module_name

class DependencyGraph:
    """Represent a graph of module dependencies."""

    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: List[tuple] = []

    def add_dependency(self, from_module: str, to_module: str):
        self.nodes.add(from_module)
        self.nodes.add(to_module)
        self.edges.append((from_module, to_module))

    def render(self, output_path: str = "deps.html", show_isolated: bool = True):
        """Generate an interactive HTML graph using vis.js (no pyvis dependency issues)."""
        # Filter nodes
        nodes_to_show = self.nodes
        if not show_isolated:
            connected = set()
            for a, b in self.edges:
                connected.add(a)
                connected.add(b)
            nodes_to_show = connected

        # Prepare data for vis.js
        nodes_list = [{"id": node, "label": node, "title": node} for node in nodes_to_show]
        edges_list = [{"from": src, "to": dst, "arrows": "to"} for src, dst in self.edges
                      if src in nodes_to_show and dst in nodes_to_show]

        # HTML template with vis.js
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>CodeMap Dependency Graph</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js"></script>
    <style>
        #mynetwork {
            width: 100%;
            height: 750px;
            border: 1px solid lightgray;
        }
    </style>
</head>
<body>
    <h2>Dependency Graph</h2>
    <div id="mynetwork"></div>
    <script>
        var nodes = new vis.DataSet($nodes);
        var edges = new vis.DataSet($edges);
        var container = document.getElementById('mynetwork');
        var data = { nodes: nodes, edges: edges };
        var options = {
            physics: { enabled: true },
            edges: { arrows: { to: true } }
        };
        var network = new vis.Network(container, data, options);
    </script>
</body>
</html>
        """
        # Replace placeholders
        nodes_json = json.dumps(nodes_list, indent=2)
        edges_json = json.dumps(edges_list, indent=2)
        html = html_template.replace("$nodes", nodes_json).replace("$edges", edges_json)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Dependency graph saved to {output_path}")


def build_dependency_graph(project_root: str, exclude_dirs: Set[str] = None) -> DependencyGraph:
    if exclude_dirs is None:
        exclude_dirs = {'venv', 'env', '.venv', '__pycache__', 'tests', 'test', 'dist', 'build'}

    py_files = find_python_files(project_root, exclude_dirs)
    graph = DependencyGraph()

    module_to_file = {}
    for f in py_files:
        mod = get_relative_module_name(f, project_root)
        module_to_file[mod] = f

    for f in py_files:
        from_mod = get_relative_module_name(f, project_root)
        imports = extract_imports(f)
        for imp in imports:
            for candidate in module_to_file.keys():
                if candidate == imp or candidate.startswith(imp + '.'):
                    graph.add_dependency(from_mod, imp)
                    break
    return graph