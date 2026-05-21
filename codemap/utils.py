"""Shared utilities: file walking, AST helpers, etc."""

import os
import ast
from pathlib import Path
from typing import List, Set, Optional, Dict

def find_python_files(root: str, exclude_dirs: Optional[Set[str]] = None) -> List[str]:
    """Recursively find all .py files in a directory."""
    if exclude_dirs is None:
        exclude_dirs = {'venv', 'env', '.venv', '__pycache__', 'tests', 'test', 'dist', 'build'}

    py_files = []
    root_path = Path(root).resolve()
    for entry in root_path.rglob("*.py"):
        if any(part in exclude_dirs for part in entry.parts):
            continue
        py_files.append(str(entry))
    return py_files

def extract_imports_old(file_path: str) -> List[str]:
    """Extract imported module names from a Python file using AST."""
    imports = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
    except (SyntaxError, UnicodeDecodeError):
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split('.')[0])
    return list(set(imports))

def extract_imports(file_path: str) -> List[str]:
    """Extract imported top-level module names from a Python file using AST."""
    imports = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
    except (SyntaxError, UnicodeDecodeError):
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split('.')[0]
                imports.append(top)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # 处理相对导入：去掉开头的点
                module = node.module.lstrip('.')
                if module:
                    top = module.split('.')[0]
                    imports.append(top)
    return list(set(imports))


def get_relative_module_name(file_path: str, root_dir: str) -> str:
    """Convert file path to dot-separated module name relative to root_dir."""
    root = Path(root_dir).resolve()
    full = Path(file_path).resolve()
    rel = full.relative_to(root)
    return str(rel.with_suffix('')).replace(os.sep, '.')

def get_function_calls(file_path: str, function_name: str) -> List[str]:
    """
    Extract all function calls inside the body of a specific function.
    
    Args:
        file_path: Path to Python file.
        function_name: Name of the function to analyze.
    
    Returns:
        List of called function names (simple names, no module prefix).
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
    except (SyntaxError, UnicodeDecodeError):
        return []

    class CallFinder(ast.NodeVisitor):
        def __init__(self, target_name: str):
            self.target = target_name
            self.in_target = False
            self.calls = []

        def visit_FunctionDef(self, node):
            # Only descend into the target function
            if node.name == self.target:
                self.in_target = True
                self.generic_visit(node)
                self.in_target = False
            else:
                # Skip other functions
                pass

        def visit_Call(self, node):
            if self.in_target:
                # Try to extract the function name
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    # For calls like obj.method(), we take 'method'
                    func_name = node.func.attr
                if func_name:
                    self.calls.append(func_name)
            self.generic_visit(node)

    finder = CallFinder(function_name)
    finder.visit(tree)
    return list(set(finder.calls))


def build_function_to_file_map(project_root: str, exclude_dirs: Set[str] = None) -> Dict[str, str]:
    """
    Scan all Python files and build a mapping from function name to file path.
    If multiple files define the same function name, the first occurrence wins.
    """
    mapping = {}
    py_files = find_python_files(project_root, exclude_dirs)
    for file_path in py_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=file_path)
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name not in mapping:
                    mapping[node.name] = file_path
    return mapping