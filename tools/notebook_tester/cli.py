"""CLI for Notebook Tester."""

import click
import sys
from pathlib import Path
from .executor.notebook_executor import NotebookExecutor
from .core.models import TestStatus


@click.group()
def cli():
    """Notebook Execution Testing Tool."""
    pass


@cli.command()
@click.argument("notebook_path", type=click.Path(exists=True))
@click.option("--timeout", default=600, help="Execution timeout in seconds")
def run(notebook_path: str, timeout: int):
    """Execute a single notebook."""
    executor = NotebookExecutor(timeout=timeout)
    
    click.echo(f"Executing {notebook_path}...")
    result = executor.execute(Path(notebook_path))
    
    if result.status == TestStatus.PASSED:
        click.echo(f"✓ Passed ({result.total_duration:.2f}s)")
        sys.exit(0)
    else:
        click.echo(f"✗ Failed ({result.total_duration:.2f}s)")
        if result.error_message:
            click.echo(f"Error: {result.error_message}")
            
        for cell in result.failed_cells:
            click.echo(f"\nCell {cell.index} failed:")
            click.echo(f"  {cell.error_name}: {cell.error_value}")
            
        sys.exit(1)


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("--timeout", default=600)
def run_dir(directory: str, timeout: int):
    """Execute all notebooks in a directory."""
    executor = NotebookExecutor(timeout=timeout)
    path = Path(directory)
    
    passed = 0
    failed = 0
    
    for notebook_path in path.rglob("*.ipynb"):
        if ".ipynb_checkpoints" in str(notebook_path):
            continue
            
        click.echo(f"Executing {notebook_path.name}...", nl=False)
        result = executor.execute(notebook_path)
        
        if result.status == TestStatus.PASSED:
            click.echo(f" ✓ ({result.total_duration:.2f}s)")
            passed += 1
        else:
            click.echo(f" ✗")
            failed += 1
            
    click.echo(f"\nSummary: {passed} passed, {failed} failed")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    cli()
