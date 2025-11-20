# Notebook Validator

Automated validation and metadata extraction system for Jupyter notebooks in the Vertex AI samples repository.

## Features

- **Structure Validation**: Ensures notebooks have proper organization (title, overview, setup sections)
- **Content Validation**: Checks for hardcoded values, large outputs, broken links, and documentation quality
- **Metadata Validation**: Verifies required metadata fields, Colab links, and license information
- **Dependency Validation**: Checks version pinning, deprecated APIs, and import availability
- **Metadata Extraction**: Automatically extracts structured metadata from notebooks

## Installation

```bash
cd tools/notebook_validator
pip install -r requirements.txt
```

## Usage

### Validate a Single Notebook

```bash
python -m tools.notebook_validator.cli validate path/to/notebook.ipynb
```

### Validate a Directory

```bash
python -m tools.notebook_validator.cli validate-dir notebooks/
```

### Extract Metadata

```bash
python -m tools.notebook_validator.cli extract-metadata path/to/notebook.ipynb
```

### Generate Configuration

```bash
python -m tools.notebook_validator.cli init-config --output my_rules.yaml
```

## Configuration

Create a `validation_rules.yaml` file to customize validation rules:

```yaml
structure:
  enabled: true
  rules:
    require_title:
      enabled: true
      severity: error
    require_overview:
      enabled: true
      severity: warning

content:
  enabled: true
  rules:
    hardcoded_values:
      enabled: true
      severity: error
    output_cells:
      enabled: true
      severity: warning
      max_output_size: 10000

metadata:
  enabled: true
  rules:
    required_fields:
      enabled: true
      severity: error
      fields:
        - title
        - description
        - tags

dependencies:
  enabled: true
  rules:
    version_pinning:
      enabled: true
      severity: warning
      allow_unpinned:
        - google-cloud-aiplatform
```

## CLI Options

### validate

```bash
python -m tools.notebook_validator.cli validate NOTEBOOK_PATH [OPTIONS]

Options:
  --config PATH          Path to config file
  --validators TEXT      Specific validators to run (can be repeated)
  --format [console|json]  Output format
  --output PATH          Output file for report
  --strict               Fail on warnings
```

### validate-dir

```bash
python -m tools.notebook_validator.cli validate-dir DIRECTORY_PATH [OPTIONS]

Options:
  --recursive/--no-recursive  Scan subdirectories
  --pattern TEXT             Glob pattern for notebooks
  --config PATH              Path to config file
  --format [console|json]    Output format
  --output PATH              Output file for report
  --fail-fast                Stop on first failure
```

## GitHub Actions Integration

The validator automatically runs on pull requests that modify notebooks. See `.github/workflows/notebook_validation.yml`.

## Validation Rules

### Structure Rules

- **require_title**: Notebook must have a title (H1 heading)
- **require_overview**: Notebook should have an overview section
- **require_setup_section**: Notebook should have setup instructions
- **check_cell_order**: Imports should come before other code
- **check_section_headers**: Headers should follow proper hierarchy

### Content Rules

- **hardcoded_values**: Detects hardcoded project IDs, regions, credentials
- **output_cells**: Warns about large output cells
- **markdown_links**: Validates markdown links
- **documentation**: Ensures adequate markdown documentation

### Metadata Rules

- **required_fields**: Checks for required metadata (title, description, tags)
- **colab_links**: Verifies Colab/Workbench links (for official notebooks)
- **license_info**: Checks for license information

### Dependency Rules

- **version_pinning**: Warns about unpinned dependencies
- **deprecated_apis**: Detects usage of deprecated Vertex AI APIs
- **import_availability**: Verifies imports match declared dependencies

## Output Formats

### Console Output

```
Validating: notebooks/official/automl/automl_image_classification.ipynb
================================================================================

Errors:
  ● Hardcoded value: project_id at cell 5, line 3
    → Use: project_id = os.environ.get("PROJECT_ID", "YOUR_PROJECT_ID")

Warnings:
  ⚠ Unpinned dependency: google-cloud-storage
    → Pin version: !pip install google-cloud-storage==x.y.z

================================================================================
Summary:
  ✗ 1 errors
  ⚠ 1 warnings
  ℹ 0 info

✗ Validation: FAILED
```

### JSON Output

```json
{
  "summary": {
    "total_notebooks": 1,
    "passed": 0,
    "failed": 1,
    "total_errors": 1,
    "total_warnings": 1,
    "total_info": 0
  },
  "reports": [
    {
      "notebook_path": "notebooks/official/automl/automl_image_classification.ipynb",
      "is_valid": false,
      "validation_results": [
        {
          "rule_id": "content.hardcoded_values",
          "severity": "error",
          "message": "Hardcoded project_id found",
          "cell_index": 5,
          "line_number": 3,
          "suggestion": "Use environment variable"
        }
      ]
    }
  ]
}
```

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Validators

1. Create a new validator class in `validators/`
2. Implement the `validate()` method
3. Register in `core/validator.py`
4. Add configuration options
5. Write tests

## License

Apache 2.0
