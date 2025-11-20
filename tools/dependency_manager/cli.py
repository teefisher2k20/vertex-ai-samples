"""CLI for Dependency Manager."""

import click
from pathlib import Path
import sys

from .scanner.notebook_scanner import NotebookScanner
from .checker.vulnerability_checker import VulnerabilityChecker
from .updater.update_generator import UpdateGenerator


@click.group()
def cli():
    """Dependency Management Tool for Notebooks."""
    pass


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("--check-vulns/--no-check-vulns", default=True)
def scan(directory: str, check_vulns: bool):
    """Scan directory for dependencies and vulnerabilities."""
    scanner = NotebookScanner()
    checker = VulnerabilityChecker()
    
    path = Path(directory)
    click.echo(f"Scanning {path}...")
    
    dependencies = scanner.scan_directory(path)
    click.echo(f"Found {len(dependencies)} dependencies.")
    
    if check_vulns:
        click.echo("Checking for vulnerabilities...")
        vulns = checker.check_vulnerabilities(dependencies)
        
        if vulns:
            click.echo(f"\nFound {len(vulns)} vulnerabilities:")
            for v in vulns:
                click.echo(f"  [HIGH] {v.package_name} {v.current_version} -> {v.fixed_in[0]}")
                click.echo(f"         {v.description} ({v.vuln_id})")
            sys.exit(1)
        else:
            click.echo("\nNo vulnerabilities found.")


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
def update(directory: str):
    """Generate update plans for vulnerabilities."""
    scanner = NotebookScanner()
    checker = VulnerabilityChecker()
    generator = UpdateGenerator()
    
    path = Path(directory)
    dependencies = scanner.scan_directory(path)
    vulns = checker.check_vulnerabilities(dependencies)
    
    plans = generator.generate_security_updates(dependencies, vulns)
    
    if not plans:
        click.echo("No updates needed.")
        return
        
    click.echo(f"Generated {len(plans)} update plans:")
    for plan in plans:
        click.echo(f"\nUpdate {plan.dependency.name}:")
        click.echo(f"  File: {plan.dependency.file_path}")
        click.echo(f"  Current: {plan.dependency.version}")
        click.echo(f"  Target: {plan.target_version}")
        click.echo(f"  Reason: {plan.reason}")


if __name__ == "__main__":
    cli()
