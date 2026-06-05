"""Dependency graph builder: modules and their imports."""

import json
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path

from .utils import find_python_files, extract_imports, get_relative_module_name


class DependencyGraph:
    """Represent a graph of module dependencies."""

    def __init__(self) -> None:
        self.nodes: Set[str] = set()
        self.edges: List[Tuple[str, str]] = []

    def add_dependency(self, from_module: str, to_module: str) -> None:
        """Record that from_module imports to_module."""
        self.nodes.add(from_module)
        self.nodes.add(to_module)
        self.edges.append((from_module, to_module))

    def _filter_nodes_and_edges(self, show_isolated: bool) -> Tuple[List[str], List[Tuple[str, str]]]:
        """Return (filtered_nodes, filtered_edges) based on show_isolated flag."""
        if show_isolated:
            return list(self.nodes), self.edges.copy()

        # Keep only nodes that appear in at least one edge
        connected_nodes: Set[str] = set()
        for src, dst in self.edges:
            connected_nodes.add(src)
            connected_nodes.add(dst)

        filtered_edges = [
            (src, dst) for src, dst in self.edges
            if src in connected_nodes and dst in connected_nodes
        ]
        return list(connected_nodes), filtered_edges

    def _generate_html(self, nodes_list: List[str], edges_list: List[Tuple[str, str]]) -> str:
        """Generate HTML content using vis.js."""
        # Prepare data structures for vis.js
        vis_nodes = [{"id": node, "label": node, "title": node} for node in nodes_list]
        vis_edges = [{"from": src, "to": dst, "arrows": "to"} for src, dst in edges_list]

        nodes_json = json.dumps(vis_nodes, indent=2)
        edges_json = json.dumps(vis_edges, indent=2)

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
        return html_template.replace("$nodes", nodes_json).replace("$edges", edges_json)

    def render(self, output_path: str = "deps.html", show_isolated: bool = True) -> None:
        """Generate an interactive HTML graph using vis.js (no pyvis dependency issues)."""
        nodes_to_show, edges_to_show = self._filter_nodes_and_edges(show_isolated)
        html_content = self._generate_html(nodes_to_show, edges_to_show)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Dependency graph saved to {output_path}")


def build_dependency_graph(
    project_root: str,
    exclude_dirs: Optional[Set[str]] = None
) -> DependencyGraph:
    """Parse all Python files in project_root and build a module dependency graph."""
    if exclude_dirs is None:
        exclude_dirs = {'venv', 'env', '.venv', '__pycache__', 'tests', 'test', 'dist', 'build'}

    py_files = find_python_files(project_root, exclude_dirs)
    graph = DependencyGraph()

    # Map module name to its file path
    module_to_file: Dict[str, str] = {}
    for f in py_files:
        mod = get_relative_module_name(f, project_root)
        module_to_file[mod] = f

    # Extract dependencies
    for f in py_files:
        from_mod = get_relative_module_name(f, project_root)
        imports = extract_imports(f)
        for imp in imports:
            # Check if imported module is a local module
            for candidate in module_to_file.keys():
                if candidate == imp or candidate.startswith(imp + '.'):
                    graph.add_dependency(from_mod, imp)
                    break

    return graph
