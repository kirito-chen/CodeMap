"""Call tree builder: generate hierarchical tree from entry function."""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Optional, Any

from .utils import find_python_files

# Built-in function names to skip (partial list)
BUILTIN_FUNCTIONS = {
    'print', 'len', 'range', 'open', 'type', 'str', 'int', 'float', 'bool',
    'list', 'dict', 'set', 'tuple', 'enumerate', 'zip', 'map', 'filter',
    'sorted', 'min', 'max', 'sum', 'any', 'all', 'abs', 'round', 'pow',
    'isinstance', 'issubclass', 'hasattr', 'getattr', 'setattr', 'delattr',
    '__import__', 'eval', 'exec', 'compile', 'globals', 'locals', 'vars',
    'dir', 'help', 'id', 'hash', 'callable', 'chr', 'ord', 'bin', 'hex',
    'oct', 'format', 'input', 'exit', 'quit', '__name__', '__file__',
}

class CallTreeNode:
    """Node in the call tree."""
    def __init__(self, name: str, file_path: str = "", line: int = 0):
        self.name = name          # function name
        self.file = file_path     # file where defined
        self.line = line          # line number (approx)
        self.children: List['CallTreeNode'] = []

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "name": self.name,
            "file": self.file,
            "line": self.line,
            "children": [c.to_dict() for c in self.children]
        }

def _extract_calls_from_function(file_path: str, func_name: str, 
                                  defined_functions: Set[str]) -> List[str]:
    """
    Parse a specific function in a file and return list of called function names.
    Only returns names that are in defined_functions (user-defined).
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
    except (SyntaxError, UnicodeDecodeError):
        return []

    class CallFinder(ast.NodeVisitor):
        def __init__(self, target_name: str, defined: Set[str]):
            self.target = target_name
            self.defined = defined
            self.in_target = False
            self.calls = []

        def visit_FunctionDef(self, node):
            if node.name == self.target:
                self.in_target = True
                self.generic_visit(node)
                self.in_target = False
            else:
                self.generic_visit(node)

        def visit_Call(self, node):
            if self.in_target:
                # Extract function name
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    # For method calls like obj.method(), we skip for simplicity
                    # (we only track plain function calls)
                    pass
                if func_name and func_name in self.defined and func_name not in BUILTIN_FUNCTIONS:
                    self.calls.append(func_name)
            self.generic_visit(node)

    finder = CallFinder(func_name, defined_functions)
    finder.visit(tree)
    return list(dict.fromkeys(finder.calls))  # preserve order but remove duplicates

def build_call_tree(entry_file: str, entry_function: str, 
                    project_root: Optional[str] = None) -> CallTreeNode:
    """
    Recursively build a call tree starting from entry_function.
    
    Args:
        entry_file: Path to file containing entry_function.
        entry_function: Name of the starting function.
        project_root: Root of the project (for finding function definitions).
    
    Returns:
        Root CallTreeNode.
    """
    if project_root is None:
        project_root = str(Path(entry_file).parent)

    # Step 1: build a mapping from function name to file path
    func_to_file: Dict[str, str] = {}
    py_files = find_python_files(project_root)
    for f in py_files:
        try:
            with open(f, "r", encoding="utf-8") as src:
                tree = ast.parse(src.read(), filename=f)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name not in func_to_file:
                        func_to_file[node.name] = f
        except:
            pass

    # Also include the entry function if not found (should be found above)
    if entry_function not in func_to_file:
        func_to_file[entry_function] = entry_file

    defined_functions = set(func_to_file.keys())

    # Step 2: DFS to build tree
    visited: Set[str] = set()  # prevent infinite recursion in cycles

    def dfs(func_name: str, file_path: str) -> CallTreeNode:
        node = CallTreeNode(func_name, file_path)
        # Avoid cycles: if already visited, stop (do not add children again)
        if func_name in visited:
            return node
        visited.add(func_name)
        callees = _extract_calls_from_function(file_path, func_name, defined_functions)
        for callee in callees:
            callee_file = func_to_file.get(callee, "")
            child = dfs(callee, callee_file)
            node.children.append(child)
        # Remove from visited to allow other paths (but careful for cycles)
        # Actually we keep visited to prevent infinite loops, but that may cut off valid calls from other branches.
        # For tree we want each function to appear only once as a child of a given parent.
        # However, if the same function is called from two different places, we want two separate nodes.
        # So we should NOT use a global visited across all DFS; instead we use path-based detection.
        # Let's reimplement without global visited but with local path set to detect cycles.
        return node

    # Reimplement DFS with path set to avoid infinite recursion
    def dfs_no_cycle(func_name: str, file_path: str, path: Set[str]) -> CallTreeNode:
        node = CallTreeNode(func_name, file_path)
        if func_name in path:
            # Cycle detected: stop recursion
            return node
        path.add(func_name)
        callees = _extract_calls_from_function(file_path, func_name, defined_functions)
        for callee in callees:
            callee_file = func_to_file.get(callee, "")
            child = dfs_no_cycle(callee, callee_file, path.copy())  # pass a copy to avoid modifying parent's set
            node.children.append(child)
        return node

    root_file = func_to_file.get(entry_function, entry_file)
    root = dfs_no_cycle(entry_function, root_file, set())
    return root