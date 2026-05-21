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

if __name__ == "__main__":
    cli()