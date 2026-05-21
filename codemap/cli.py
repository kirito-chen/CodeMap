"""Command line interface for codemap."""

import click
from pathlib import Path
import sys

from .deps import build_dependency_graph
from .calls import build_call_graph
from .heatmap import build_heatmap

@click.group()
def cli():
    """CodeMap – visualize your Python code structure."""
    pass

@cli.command()
@click.argument("project_root", type=click.Path(exists=True, file_okay=False))
@click.option("--output", "-o", default="deps.html", help="Output HTML file")
@click.option("--exclude", multiple=True, default=["venv", "__pycache__", "tests"],
              help="Directory names to exclude (can be used multiple times)")
def deps(project_root, output, exclude):
    """Generate interactive dependency graph."""
    exclude_set = set(exclude)
    click.echo(f"Analyzing dependencies in {project_root} ...")
    graph = build_dependency_graph(project_root, exclude_set)
    graph.render(output, show_isolated=True)
    click.echo(f"Done. Open {output} in browser.")

@cli.command()
@click.argument("entry_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--entry", "-e", required=True, help="Name of the entry function")
@click.option("--format", "-f", "fmt", type=click.Choice(["mermaid", "json"]), default="mermaid",
              help="Output format")
@click.option("--max-depth", type=int, default=5, help="Maximum recursion depth")
def calls(entry_file, entry, fmt, max_depth):
    """Generate function call graph starting from entry function."""
    click.echo(f"Building call graph for {entry} in {entry_file} ...")
    graph = build_call_graph(entry_file, entry, max_depth)
    if fmt == "mermaid":
        click.echo(graph.to_mermaid())
    else:
        import json
        click.echo(json.dumps(graph.to_dict(), indent=2))

@cli.command()
@click.argument("project_root", type=click.Path(exists=True, file_okay=False))
@click.option("--metric", "-m", type=click.Choice(["complexity", "lines"]), default="complexity",
              help="Metric to visualise")
@click.option("--output", "-o", default="heatmap.html", help="Output HTML file")
@click.option("--exclude", multiple=True, default=["venv", "__pycache__", "tests"],
              help="Directory names to exclude")
def heatmap(project_root, metric, output, exclude):
    """Generate complexity / lines heatmap."""
    exclude_set = set(exclude)
    click.echo(f"Computing {metric} for files in {project_root} ...")
    hm = build_heatmap(project_root, metric, exclude_set)
    hm.save(output)
    # click.echo(f"Heatmap saved to {output}")


@cli.command()
@click.argument("entry_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--entry", "-e", required=True, help="Entry function name")
@click.option("--output", "-o", default="call_tree.html", help="Output HTML file")
def tree(entry_file, entry, output):
    """Generate an interactive call tree HTML (mind-map style)."""
    from .tree import build_call_tree
    import json
    from pathlib import Path

    click.echo(f"Building call tree from {entry} in {entry_file}...")
    root = build_call_tree(entry_file, entry)

    data = root.to_dict()

    # Use triple quotes and escape braces properly
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Call Tree - {entry}</title>
    <style>
        .node circle {{ fill: #fff; stroke: steelblue; stroke-width: 3px; }}
        .node text {{ font: 12px sans-serif; }}
        .link {{ fill: none; stroke: #ccc; stroke-width: 2px; }}
        .tooltip {{ position: absolute; background: #fff; border: 1px solid #ccc; padding: 5px; border-radius: 5px; font-size: 12px; pointer-events: none; opacity: 0; }}
    </style>
</head>
<body>
    <h1>Call Tree from {entry}</h1>
    <div id="tree-container" style="width:100%; height:800px; overflow:auto; border:1px solid #ccc;"></div>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
        const treeData = {json_data};

        // Set dimensions and margins
        const width = 1200;
        const height = 800;
        const margin = {{ top: 20, right: 120, bottom: 20, left: 120 }};
        const innerWidth = width - margin.left - margin.right;
        const innerHeight = height - margin.top - margin.bottom;

        const svg = d3.select("#tree-container")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .append("g")
            .attr("transform", `translate(${{margin.left}},${{margin.top}})`);

        // Create a tree layout
        const root = d3.hierarchy(treeData);
        const treeLayout = d3.tree().size([innerHeight, innerWidth]);
        treeLayout(root);

        // Add links
        svg.selectAll(".link")
            .data(root.links())
            .enter()
            .append("path")
            .attr("class", "link")
            .attr("d", d3.linkHorizontal()
                .x(d => d.y)
                .y(d => d.x)
            );

        // Add nodes
        const nodes = svg.selectAll(".node")
            .data(root.descendants())
            .enter()
            .append("g")
            .attr("class", "node")
            .attr("transform", d => `translate(${{d.y}},${{d.x}})`);

        nodes.append("circle")
            .attr("r", 8);

        nodes.append("text")
            .attr("dy", ".35em")
            .attr("x", d => d.children ? -12 : 12)
            .style("text-anchor", d => d.children ? "end" : "start")
            .text(d => d.data.name);

        // Tooltip on hover
        const tooltip = d3.select("body").append("div").attr("class", "tooltip");
        nodes.on("mouseover", function(event, d) {{
            tooltip.style("opacity", 1)
                .html(`<strong>${{d.data.name}}</strong><br/>File: ${{d.data.file || "unknown"}}<br/>Line: ${{d.data.line || "?"}}`)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 20) + "px");
        }}).on("mouseout", function() {{
            tooltip.style("opacity", 0);
        }});
    </script>
</body>
</html>"""

    with open(output, "w", encoding="utf-8") as f:
        f.write(html_template.format(entry=entry, json_data=json.dumps(data, indent=2)))
    click.echo(f"Call tree saved to {output}")

@cli.command()
@click.argument("entry_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--entry", "-e", required=True, help="Entry function name (e.g., main)")
@click.option("--format", "-f", "fmt", type=click.Choice(["mermaid", "json"]), default="mermaid",
              help="Output format")
def trace(entry_file, entry, fmt):
    """Trace method calls between classes (sequence diagram)."""
    from .trace import build_trace_graph
    click.echo(f"Tracing method calls from {entry} in {entry_file}...")
    graph = build_trace_graph(entry_file, entry)
    if fmt == "mermaid":
        click.echo(graph.to_mermaid())
    else:
        import json
        click.echo(json.dumps(graph.to_json(), indent=2))

if __name__ == "__main__":
    cli()