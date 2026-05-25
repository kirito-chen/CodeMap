"""Function call graph builder with cross-file support."""
# todo
import json
from pathlib import Path
from typing import Dict, List, Set, Optional

from .utils import get_function_calls, build_function_to_file_map

class CallGraph:
    """Call graph from an entry function."""

    def __init__(self, root_function: str):
        self.root = root_function
        self.calls: Dict[str, List[str]] = {}

    def add_call(self, caller: str, callee: str):
        if caller not in self.calls:
            self.calls[caller] = []
        if callee not in self.calls[caller]:
            self.calls[caller].append(callee)

    def to_mermaid(self) -> str:
        """Return Mermaid flowchart definition."""
        def sanitize(name: str) -> str:
            return name.replace('.', '_').replace('-', '_').replace(' ', '_')

        lines = ["graph TD"]
        for caller, callees in self.calls.items():
            safe_caller = sanitize(caller)
            for callee in callees:
                safe_callee = sanitize(callee)
                lines.append(f"    {safe_caller} --> {safe_callee}")

        if not self.calls:
            lines.append(f"    {sanitize(self.root)}")

        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {"root": self.root, "calls": self.calls}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def build_call_graph(entry_file: str, entry_function: str,
                     max_depth: int = 5, project_root: Optional[str] = None) -> CallGraph:
    """Recursively build call graph from entry function."""
    if project_root is None:
        project_root = str(Path(entry_file).parent)

    func_to_file = build_function_to_file_map(project_root)
    if entry_function not in func_to_file:
        func_to_file[entry_function] = entry_file

    graph = CallGraph(entry_function)
    visited = set()

    def dfs(func_name: str, depth: int):
        if depth > max_depth or func_name in visited:
            return
        visited.add(func_name)
        file_path = func_to_file.get(func_name)
        if not file_path:
            return
        callees = get_function_calls(file_path, func_name)
        for callee in callees:
            graph.add_call(func_name, callee)
            dfs(callee, depth + 1)

    dfs(entry_function, 0)
    return graph