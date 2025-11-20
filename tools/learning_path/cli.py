"""CLI for Learning Path Generator."""

import click
import json
from pathlib import Path
from .analyzer.content_analyzer import ContentAnalyzer
from .generator.path_generator import PathGenerator
from .core.models import Difficulty


@click.group()
def cli():
    """Learning Path Generator Tool."""
    pass


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("--output", type=click.Path(), default="learning_paths.json")
def generate(directory: str, output: str):
    """Generate learning paths from notebooks in a directory."""
    analyzer = ContentAnalyzer()
    generator = PathGenerator()
    
    path = Path(directory)
    click.echo(f"Analyzing notebooks in {path}...")
    
    nodes = []
    for notebook_path in path.rglob("*.ipynb"):
        if ".ipynb_checkpoints" in str(notebook_path):
            continue
        nodes.append(analyzer.analyze_notebook(notebook_path))
        
    click.echo(f"Analyzed {len(nodes)} notebooks.")
    
    click.echo("Generating paths...")
    paths = generator.generate_all_paths(nodes)
    
    # Serialize
    output_data = []
    for p in paths:
        output_data.append({
            "title": p.title,
            "description": p.description,
            "difficulty": p.difficulty.name,
            "total_time_mins": p.total_time_mins,
            "steps": [
                {
                    "title": n.title,
                    "path": n.path,
                    "difficulty": n.difficulty.name,
                    "time": n.estimated_time_mins
                }
                for n in p.nodes
            ]
        })
        
    with open(output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
        
    click.echo(f"Generated {len(paths)} paths in {output}")


if __name__ == "__main__":
    cli()
