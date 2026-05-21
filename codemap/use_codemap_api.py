#!/usr/bin/env python3
"""
Test the three main APIs of codemap on the 'test_project' directory.
"""

import os
from codemap import build_dependency_graph, build_call_graph, build_heatmap

# Path to the test project (adjust if needed)
PROJECT_ROOT = "../test_project"
ENTRY_FILE = os.path.join(PROJECT_ROOT, "main.py")
ENTRY_FUNCTION = "start"
OUTDIR = "api_results"

def test_dependency_graph():
    """1. Build and render the dependency graph."""
    print("\n=== 1. Dependency Graph ===")
    graph = build_dependency_graph(PROJECT_ROOT)
    print(f"Number of module nodes: {len(graph.nodes)}")
    print(f"Number of dependencies (edges): {len(graph.edges)}")
    if graph.nodes:
        print(f"Sample nodes: {list(graph.nodes)[:5]}")
    if graph.edges:
        print(f"Sample edges: {graph.edges[:5]}")
    output_file = OUTDIR + "/" + "test_deps.html"
    graph.render(output_file, show_isolated=True)
    print(f"Dependency graph saved to {output_file}")

def test_call_graph():
    """2. Build and display the function call graph."""
    print("\n=== 2. Function Call Graph ===")
    call_graph = build_call_graph(ENTRY_FILE, ENTRY_FUNCTION, max_depth=5)
    print(f"Root function: {call_graph.root}")
    print(f"Number of caller functions: {len(call_graph.calls)}")
    # Output Mermaid format (can be copied into Markdown)
    mermaid = call_graph.to_mermaid()
    print("\nMermaid representation:")
    print(mermaid)
    # Also save as JSON
    json_out = call_graph.to_json()
    output_file = OUTDIR + "/" + "test_calls.json"
    with open(output_file, "w") as f:
        f.write(json_out)
    print(f"Call graph JSON saved to {output_file}")

def test_heatmap():
    """3. Build and save the complexity heatmap."""
    print("\n=== 3. Code Heatmap (Complexity) ===")
    heatmap = build_heatmap(PROJECT_ROOT, metric="complexity")
    print(f"Number of files analyzed: {len(heatmap.filenames)}")
    print(f"Metric: {heatmap.metric_name}")
    print(f"Min value: {min(heatmap.values):.2f}, Max value: {max(heatmap.values):.2f}")
    output_file = OUTDIR + "/" +"test_heatmap.html"
    heatmap.save(output_file)
    print(f"Heatmap saved to {output_file}")
    # Optionally also generate a lines-of-code heatmap
    print("\n--- Also generating lines-of-code heatmap ---")
    loc_heatmap = build_heatmap(PROJECT_ROOT, metric="lines")
    output_file = OUTDIR + "/" +"test_heatmap_lines.html"
    loc_heatmap.save(output_file)
    print(f"Lines-of-code heatmap saved to {output_file}")

if __name__ == "__main__":
    # Ensure the test_project exists
    if not os.path.isdir(PROJECT_ROOT):
        print(f"Error: Directory '{PROJECT_ROOT}' not found.")
        print("Please create a 'test_project' folder with some Python files, or adjust the PROJECT_ROOT variable.")
    else:
        test_dependency_graph()
        test_call_graph()
        test_heatmap()
        print("\nAll tests completed. Open the generated HTML files in a browser.")