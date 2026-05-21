"""Package installer for codemap."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="codemap",
    version="0.1.0",
    author="Your Name",
    description="Visualize Python code: dependency graph, call graph, complexity heatmap",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourname/codemap",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0.0",
        "pyvis>=0.3.0",
        "graphviz>=0.20.0",
        "radon>=6.0.0",
        "jinja2>=3.0.0",
        "matplotlib>=3.5.0",
    ],
    entry_points={
        "console_scripts": [
            "codemap=codemap.cli:cli",
        ],
    },
)