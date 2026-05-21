"""Runtime call tracing via static analysis: infer object types and method calls."""

import ast
import os
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path

from .utils import find_python_files

class ClassInfo:
    """Store information about a class: methods, parent, etc."""
    def __init__(self, name: str, module: str):
        self.name = name
        self.module = module
        self.methods: List[str] = []
        self.parent: Optional[str] = None

class TraceGraph:
    """
    Represents a sequence diagram of method calls between classes.
    Participants are classes. Edges are method calls: ClassA.method1 -> ClassB.method2.
    """
    def __init__(self, entry_function: str):
        self.entry = entry_function
        self.calls: List[Tuple[str, str, str, str]] = []  # (caller_class, caller_method, callee_class, callee_method)

    def add_call(self, caller_class: str, caller_method: str, callee_class: str, callee_method: str):
        self.calls.append((caller_class, caller_method, callee_class, callee_method))

    def to_mermaid(self) -> str:
        """Generate Mermaid sequence diagram."""
        lines = ["sequenceDiagram"]
        participants: Set[str] = set()
        for cc, cm, clc, clm in self.calls:
            participants.add(cc)
            participants.add(clc)
        for p in participants:
            lines.append(f"    participant {p}")
        for cc, cm, clc, clm in self.calls:
            lines.append(f"    {cc}->>{clc}: {cm}() calls {clm}()")
        return "\n".join(lines)

    def to_json(self) -> dict:
        return {"entry": self.entry, "calls": self.calls}


class TypeInferenceVisitor(ast.NodeVisitor):
    """
    Visitor that builds a map from variable names to possible classes.
    Also records method calls and tries to link them to class types.
    """
    def __init__(self, module_name: str, all_classes: Dict[str, ClassInfo]):
        self.module = module_name
        self.all_classes = all_classes  # global class registry (name -> ClassInfo)
        self.var_types: Dict[str, Set[str]] = {}  # var name -> set of class names
        self.method_calls: List[Tuple[str, str, str, str]] = []  # (caller_class, caller_method, callee_class, callee_method)
        self.current_class: Optional[str] = None
        self.current_method: Optional[str] = None

    def visit_Assign(self, node):
        """Track variable assignments like obj = MyClass() or obj = some_function()"""
        if isinstance(node.value, ast.Call):
            # Check if it's a class instantiation
            func = node.value.func
            class_name = None
            if isinstance(func, ast.Name):
                class_name = func.id
            elif isinstance(func, ast.Attribute):
                class_name = func.attr
            if class_name and class_name in self.all_classes:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.var_types[target.id] = {class_name}
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        old_class = self.current_class
        old_method = self.current_method
        if old_class is None:
            # function, not method
            self.current_method = node.name
        else:
            self.current_method = node.name
        self.generic_visit(node)
        self.current_class = old_class
        self.current_method = old_method

    def visit_ClassDef(self, node):
        old_class = self.current_class
        self.current_class = node.name
        # Record methods
        if node.name in self.all_classes:
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    self.all_classes[node.name].methods.append(item.name)
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Call(self, node):
        """Method or function call: try to resolve callee class."""
        if self.current_class is None or self.current_method is None:
            self.generic_visit(node)
            return

        # Determine callee: could be something like obj.method()
        if isinstance(node.func, ast.Attribute):
            obj = node.func.value
            method_name = node.func.attr
            # Try to infer class of obj
            obj_var = None
            if isinstance(obj, ast.Name):
                obj_var = obj.id
            elif isinstance(obj, ast.Attribute):
                # Maybe obj.attr, we simplify to last part
                obj_var = obj.attr
            if obj_var and obj_var in self.var_types:
                callee_classes = self.var_types[obj_var]
                for callee_class in callee_classes:
                    # Record call: current_class.current_method -> callee_class.method_name
                    self.method_calls.append((self.current_class, self.current_method, callee_class, method_name))
            else:
                # Cannot infer, maybe it's a function, skip
                pass
        self.generic_visit(node)


def build_trace_graph(entry_file: str, entry_function: str, project_root: Optional[str] = None) -> TraceGraph:
    """
    Build a trace graph by analyzing all Python files, tracking object types.
    Args:
        entry_file: starting file
        entry_function: starting function name (usually "main")
        project_root: root of project (defaults to entry file's parent)
    Returns:
        TraceGraph object
    """
    if project_root is None:
        project_root = str(Path(entry_file).parent)

    # Step 1: collect all class definitions globally
    all_classes: Dict[str, ClassInfo] = {}
    py_files = find_python_files(project_root)
    for file in py_files:
        module = Path(file).stem
        try:
            with open(file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = ClassInfo(node.name, module)
                    all_classes[node.name] = class_info
        except:
            pass

    # Step 2: analyze each file with TypeInferenceVisitor
    all_calls: List[Tuple[str, str, str, str]] = []
    for file in py_files:
        module = Path(file).stem
        try:
            with open(file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            visitor = TypeInferenceVisitor(module, all_classes)
            visitor.visit(tree)
            all_calls.extend(visitor.method_calls)
        except:
            pass

    # Step 3: build graph from entry point (we only include calls reachable from entry? For simplicity, include all)
    graph = TraceGraph(entry_function)
    for call in all_calls:
        graph.add_call(*call)
    return graph