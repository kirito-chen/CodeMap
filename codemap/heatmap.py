"""Generate a heatmap showing complexity or lines of code per file."""

import os
import base64
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Set, Tuple

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import radon.complexity as radon_comp
import radon.raw as radon_raw
from jinja2 import Template

from .utils import find_python_files


class Heatmap:
    """
    Represent a rectangular heatmap of metric values for files.

    Files are sorted alphabetically and displayed as a grid of 8 columns.
    """

    DEFAULT_COLS = 8

    def __init__(self, metric_name: str, filenames: List[str], values: List[float]) -> None:
        self.metric_name = metric_name
        self.filenames = filenames
        self.values = values
        self.cols = self.DEFAULT_COLS
        self.rows = (len(values) + self.cols - 1) // self.cols if values else 0

    def _make_grid(self) -> List[List[float]]:
        """Convert flat values into a 2D grid (rows x cols)."""
        grid = np.full((self.rows, self.cols), np.nan)
        for idx, val in enumerate(self.values):
            r = idx // self.cols
            c = idx % self.cols
            grid[r, c] = val
        return grid

    def _make_labels_grid(self) -> List[List[str]]:
        """Create grid of short file names for tooltips."""
        grid = [["" for _ in range(self.cols)] for _ in range(self.rows)]
        for idx, name in enumerate(self.filenames):
            r = idx // self.cols
            c = idx % self.cols
            # Shorten long paths
            short = Path(name).name if len(name) < 50 else "..." + name[-47:]
            grid[r][c] = short
        return grid

    def _plot_to_base64(self, grid: List[List[float]]) -> str:
        """Render heatmap with matplotlib and return base64 encoded PNG."""
        fig, ax = plt.subplots(figsize=(12, max(4, self.rows * 0.5)))
        cmap = plt.cm.viridis
        masked = np.ma.masked_where(np.isnan(grid), grid)
        im = ax.imshow(masked, cmap=cmap, aspect='auto')

        # Colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(self.metric_name)

        # Ticks
        ax.set_xticks(np.arange(self.cols))
        ax.set_yticks(np.arange(self.rows))
        ax.set_xticklabels(range(1, self.cols + 1))
        ax.set_yticklabels(range(1, self.rows + 1))

        # Annotate each cell with its value
        for i in range(self.rows):
            for j in range(self.cols):
                if not np.isnan(grid[i][j]):
                    text = f"{grid[i][j]:.1f}"
                    ax.text(j, i, text, ha="center", va="center",
                            color="white" if grid[i][j] > np.nanmax(masked) / 2 else "black")

        ax.set_title(f"Code {self.metric_name.capitalize()} Heatmap (file per cell)")
        ax.set_xlabel("Column")
        ax.set_ylabel("Row")

        # Save to bytes
        img_stream = BytesIO()
        plt.tight_layout()
        plt.savefig(img_stream, format='png', dpi=100)
        img_stream.seek(0)
        img_b64 = base64.b64encode(img_stream.read()).decode('utf-8')
        plt.close(fig)
        return img_b64

    def _generate_html(self, img_b64: str, labels: List[List[str]]) -> str:
        """Generate the final HTML page with image map."""
        # Compute approximate pixel sizes for the image map
        # The matplotlib figure width is ~1200px, height ~800px (approx)
        width = 1200 // self.cols
        height = int(800 / self.rows) if self.rows else 50

        html_template = """
        <!DOCTYPE html>
        <html>
        <head><title>Code Heatmap</title>
        <style>
            .tooltip { position: relative; display: inline-block; border-bottom: 1px dotted black; }
            .tooltip .tooltiptext { visibility: hidden; background-color: #555; color: #fff; text-align: center; padding: 5px; border-radius: 6px; position: absolute; z-index: 1; bottom: 125%; left: 50%; margin-left: -60px; opacity: 0; transition: opacity 0.3s; }
            .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
            table { border-collapse: collapse; margin: 20px auto; }
            td { width: 100px; height: 60px; text-align: center; vertical-align: middle; border: 1px solid #ccc; }
        </style>
        </head>
        <body>
        <h2>Code {{ metric }} Heatmap</h2>
        <p>Each cell represents a file. Hover to see filename.</p>
        <img src="data:image/png;base64,{{ img_b64 }}" alt="heatmap" usemap="#heatmap_map">
        <map name="heatmap_map">
        {% for i in range(rows) %}
          {% for j in range(cols) %}
            <area shape="rect" coords="{{ j*width }},{{ i*height }},{{ (j+1)*width }},{{ (i+1)*height }}" alt="{{ labels[i][j] }}" title="{{ labels[i][j] }}">
          {% endfor %}
        {% endfor %}
        </map>
        <p>Rows and columns correspond to the grid positions above.</p>
        </body>
        </html>
        """
        tmpl = Template(html_template)
        return tmpl.render(
            metric=self.metric_name,
            img_b64=img_b64,
            rows=self.rows,
            cols=self.cols,
            labels=labels,
            width=width,
            height=height
        )

    def save(self, output_path: str = "heatmap.html") -> None:
        """Save the heatmap as an interactive HTML page."""
        if not self.filenames:
            print("No data to generate heatmap.")
            return

        grid = self._make_grid()
        labels = self._make_labels_grid()
        img_b64 = self._plot_to_base64(grid)
        html = self._generate_html(img_b64, labels)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Heatmap saved to {output_path}")


def build_heatmap(
    project_root: str,
    metric: str = "complexity",
    exclude_dirs: Optional[Set[str]] = None
) -> Heatmap:
    """
    Compute metric for each Python file and generate a heatmap.

    Args:
        project_root: Root directory.
        metric: Either 'complexity' (cyclomatic complexity) or 'lines' (LOC).
        exclude_dirs: Directories to skip.

    Returns:
        Heatmap instance.
    """
    if exclude_dirs is None:
        exclude_dirs = {'venv', 'env', '.venv', '__pycache__', 'tests', 'test', 'dist', 'build'}

    py_files = find_python_files(project_root, exclude_dirs)
    filenames: List[str] = []
    values: List[float] = []

    for f in py_files:
        try:
            with open(f, "r", encoding="utf-8") as src:
                content = src.read()
        except (IOError, OSError, UnicodeDecodeError):
            continue

        if metric == "complexity":
            try:
                blocks = radon_comp.cc_visit(content)
                total_complexity = sum(b.complexity for b in blocks)
                values.append(float(total_complexity))
                filenames.append(f)
            except Exception:
                # Skip files that cannot be parsed
                continue
        elif metric == "lines":
            raw = radon_raw.analyze(content)
            values.append(float(raw.loc))
            filenames.append(f)
        else:
            raise ValueError(f"Unknown metric: {metric}. Use 'complexity' or 'lines'.")

    # Sort by filename for consistent order
    paired = sorted(zip(filenames, values), key=lambda x: x[0])
    if paired:
        filenames, values = zip(*paired)
        filenames = list(filenames)
        values = list(values)
    else:
        filenames = []
        values = []

    return Heatmap(metric, filenames, values)
