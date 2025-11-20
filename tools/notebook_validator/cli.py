"""Command-line interface for notebook validator."""

import click
import json
import sys
from pathlib import Path
from typing import Optional

from .core.validator import NotebookValidator
from .core.metadata_extractor import MetadataExtractor
from .reporters.console_reporter import ConsoleReporter
from .reporters.json_reporter import JSONReporter


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Vertex AI Notebook Validator CLI"""
    pass


@cli.command()
@click.argument("notebook_path", type=click.Path(exists=True))
@click.option("--config", type=click.Path(exists=True), help="Path to config file")
@click.option("--validators", multiple=True, help="Specific validators to run")
@click.option(
    "--format",
    type=click.Choice(["console", "json"]),
    default="console",
    help="Output format",
)
@click.option("--output", type=click.Path(), help="Output file for report")
@click.option("--strict/--no-strict", default=False, help="Fail on warnings")
def validate(
    notebook_path: str,
    config: Optional[str],
    validators: tuple,
    format: str,
    output: Optional[str],
    strict: bool,
):
    """
    Validate a single notebook.

    Examples:

        notebook-validator validate my_notebook.ipynb

        notebook-validator validate my_notebook.ipynb --format json --output report.json

        notebook-validator validate my_notebook.ipynb --validators structure --validators content
    """
    config_path = Path(config) if config else None
    validator = NotebookValidator(config_path)

    # Run validation
    report = validator.validate_notebook(
        Path(notebook_path),
        validators=list(validators) if validators else None,
    )

    # Generate report
    if format == "console":
        reporter = ConsoleReporter()
        report_text = reporter.generate_report([report])
        
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(report_text)
        else:
            click.echo(report_text)
    else:  # json
        reporter = JSONReporter()
        report_data = reporter.generate_report([report])
        
        if output:
            with open(output, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2)
        else:
            click.echo(json.dumps(report_data, indent=2))

    # Exit with appropriate code
    if not report.is_valid:
        sys.exit(1)
    elif strict and report.warning_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)


@cli.command()
@click.argument("directory_path", type=click.Path(exists=True))
@click.option("--recursive/--no-recursive", default=True)
@click.option("--pattern", default="*.ipynb", help="Glob pattern for notebooks")
@click.option("--config", type=click.Path(exists=True))
@click.option(
    "--format",
    type=click.Choice(["console", "json"]),
    default="console",
)
@click.option("--output", type=click.Path())
@click.option("--fail-fast/--no-fail-fast", default=False)
def validate_dir(
    directory_path: str,
    recursive: bool,
    pattern: str,
    config: Optional[str],
    format: str,
    output: Optional[str],
    fail_fast: bool,
):
    """
    Validate all notebooks in a directory.

    Examples:

        notebook-validator validate-dir ./notebooks

        notebook-validator validate-dir ./notebooks --pattern "official/**/*.ipynb"
    """
    config_path = Path(config) if config else None
    validator = NotebookValidator(config_path)

    # Run validation
    reports = validator.validate_directory(
        Path(directory_path),
        recursive=recursive,
        pattern=pattern,
    )

    if not reports:
        click.echo("No notebooks found matching pattern")
        sys.exit(0)

    # Generate report
    if format == "console":
        reporter = ConsoleReporter()
        report_text = reporter.generate_report(reports)
        
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(report_text)
        else:
            click.echo(report_text)
    else:  # json
        reporter = JSONReporter()
        report_data = reporter.generate_report(reports)
        
        if output:
            with open(output, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2)
        else:
            click.echo(json.dumps(report_data, indent=2))

    # Exit with appropriate code
    failed_count = sum(1 for r in reports if not r.is_valid)
    if failed_count > 0:
        click.echo(f"\n{failed_count}/{len(reports)} notebooks failed validation", err=True)
        sys.exit(1)
    else:
        click.echo(f"\nAll {len(reports)} notebooks passed validation")
        sys.exit(0)


@cli.command()
@click.argument("notebook_path", type=click.Path(exists=True))
@click.option("--format", type=click.Choice(["json", "yaml"]), default="json")
@click.option("--output", type=click.Path())
def extract_metadata(notebook_path: str, format: str, output: Optional[str]):
    """
    Extract metadata from a notebook.

    Examples:

        notebook-validator extract-metadata my_notebook.ipynb

        notebook-validator extract-metadata my_notebook.ipynb --format yaml --output metadata.yaml
    """
    import nbformat

    # Load notebook
    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)

    # Extract metadata
    extractor = MetadataExtractor()
    metadata = extractor.extract_metadata(notebook, Path(notebook_path))

    # Output
    if format == "json":
        data = json.dumps(metadata.to_dict(), indent=2)
    else:  # yaml
        import yaml
        data = yaml.dump(metadata.to_dict(), default_flow_style=False)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(data)
    else:
        click.echo(data)


@cli.command()
@click.option("--output", type=click.Path(), default="validation_rules.yaml")
def init_config(output: str):
    """
    Generate default configuration file.

    Examples:

        notebook-validator init-config

        notebook-validator init-config --output custom_rules.yaml
    """
    import yaml

    default_config = {
        "version": "1.0",
        "settings": {
            "strict_mode": False,
        },
        "structure": {
            "enabled": True,
            "rules": {
                "require_title": {"enabled": True, "severity": "error"},
                "require_overview": {"enabled": True, "severity": "warning"},
                "require_setup_section": {"enabled": True, "severity": "warning"},
                "check_cell_order": {"enabled": True, "severity": "warning"},
                "check_section_headers": {"enabled": True, "severity": "info"},
            },
        },
        "content": {
            "enabled": True,
            "rules": {
                "hardcoded_values": {"enabled": True, "severity": "error"},
                "output_cells": {
                    "enabled": True,
                    "severity": "warning",
                    "max_output_size": 10000,
                },
                "markdown_links": {"enabled": True, "severity": "warning"},
                "documentation": {
                    "enabled": True,
                    "severity": "info",
                    "min_markdown_ratio": 0.2,
                },
            },
        },
        "metadata": {
            "enabled": True,
            "rules": {
                "required_fields": {
                    "enabled": True,
                    "severity": "error",
                    "fields": ["title", "description", "tags"],
                },
                "colab_links": {
                    "enabled": True,
                    "severity": "warning",
                    "require_for_official": True,
                },
                "license_info": {"enabled": True, "severity": "warning"},
            },
        },
        "dependencies": {
            "enabled": True,
            "rules": {
                "version_pinning": {
                    "enabled": True,
                    "severity": "warning",
                    "allow_unpinned": ["google-cloud-aiplatform"],
                },
                "deprecated_apis": {"enabled": True, "severity": "error"},
                "import_availability": {"enabled": True, "severity": "error"},
            },
        },
    }

    with open(output, "w", encoding="utf-8") as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

    click.echo(f"Created configuration file: {output}")


if __name__ == "__main__":
    cli()
