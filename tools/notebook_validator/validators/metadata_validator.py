"""Metadata validation for notebooks."""

from pathlib import Path
from typing import List, Dict
import nbformat

from ..core.models import ValidationResult, ValidationSeverity


class MetadataValidator:
    """Validates notebook metadata completeness."""

    def __init__(self, config: Dict):
        """Initialize with configuration."""
        self.config = config
        self.rules = config.get("rules", {})

    def validate(
        self,
        notebook: nbformat.NotebookNode,
        notebook_path: Path,
    ) -> List[ValidationResult]:
        """Run all metadata validation checks."""
        results = []

        if self._is_rule_enabled("required_fields"):
            results.extend(self.check_required_metadata(notebook, notebook_path))

        if self._is_rule_enabled("colab_links"):
            result = self.check_colab_links(notebook, notebook_path)
            if result:
                results.append(result)

        if self._is_rule_enabled("license_info"):
            result = self.check_license_info(notebook)
            if result:
                results.append(result)

        return results

    def check_required_metadata(
        self,
        notebook: nbformat.NotebookNode,
        notebook_path: Path,
    ) -> List[ValidationResult]:
        """Verify required metadata fields are present."""
        results = []
        
        required_fields = self.rules.get("required_fields", {}).get("fields", ["title", "description"])
        
        # Check for title
        if "title" in required_fields:
            has_title = False
            
            # Check metadata
            if "title" in notebook.metadata:
                has_title = True
            else:
                # Check for H1 in first few cells
                for cell in notebook.cells[:5]:
                    if cell.cell_type == "markdown" and cell.source.strip().startswith("# "):
                        has_title = True
                        break
            
            if not has_title:
                results.append(
                    ValidationResult(
                        rule_id="metadata.required_fields",
                        severity=self._get_severity("required_fields"),
                        message="Missing required field: title",
                        suggestion="Add a title as the first H1 heading",
                    )
                )

        # Check for description
        if "description" in required_fields:
            has_description = False
            
            if "description" in notebook.metadata:
                has_description = True
            else:
                # Look for description-like content
                for cell in notebook.cells[:10]:
                    if cell.cell_type == "markdown":
                        # Check if cell has substantial content
                        if len(cell.source.strip()) > 50:
                            has_description = True
                            break
            
            if not has_description:
                results.append(
                    ValidationResult(
                        rule_id="metadata.required_fields",
                        severity=self._get_severity("required_fields"),
                        message="Missing required field: description",
                        suggestion="Add a description explaining what the notebook does",
                    )
                )

        # Check for author (if required for official notebooks)
        if "author" in required_fields:
            if "author" not in notebook.metadata:
                # Check if this is an official notebook
                if "official" in str(notebook_path):
                    results.append(
                        ValidationResult(
                            rule_id="metadata.required_fields",
                            severity=self._get_severity("required_fields"),
                            message="Missing required field: author (required for official notebooks)",
                            suggestion="Add author information to notebook metadata",
                        )
                    )

        # Check for tags
        if "tags" in required_fields:
            if "tags" not in notebook.metadata or not notebook.metadata["tags"]:
                results.append(
                    ValidationResult(
                        rule_id="metadata.required_fields",
                        severity=self._get_severity("required_fields"),
                        message="Missing required field: tags",
                        suggestion="Add tags to help categorize the notebook",
                    )
                )

        return results

    def check_colab_links(
        self,
        notebook: nbformat.NotebookNode,
        notebook_path: Path,
    ) -> ValidationResult:
        """Verify Colab/Workbench links are present and valid."""
        require_for_official = self.rules.get("colab_links", {}).get("require_for_official", True)
        
        # Only check for official notebooks if configured
        if require_for_official and "official" not in str(notebook_path):
            return None

        # Look for Colab or Workbench links
        has_colab = False
        has_workbench = False

        for cell in notebook.cells[:10]:
            if cell.cell_type == "markdown":
                if "colab.research.google.com" in cell.source:
                    has_colab = True
                if "console.cloud.google.com/vertex-ai/workbench" in cell.source:
                    has_workbench = True

        if not has_colab and not has_workbench:
            return ValidationResult(
                rule_id="metadata.colab_links",
                severity=self._get_severity("colab_links"),
                message="Missing Colab or Workbench links",
                suggestion="Add links to open the notebook in Colab or Workbench",
            )

        return None

    def check_license_info(self, notebook: nbformat.NotebookNode) -> ValidationResult:
        """Verify license information is included."""
        # Look for license information
        license_keywords = ["license", "copyright", "apache", "mit"]

        for cell in notebook.cells[:10]:
            if cell.cell_type == "markdown":
                content_lower = cell.source.lower()
                if any(keyword in content_lower for keyword in license_keywords):
                    return None  # Found license info

        return ValidationResult(
            rule_id="metadata.license_info",
            severity=self._get_severity("license_info"),
            message="No license information found",
            suggestion="Add license information (e.g., Apache 2.0) to the notebook",
        )

    def _is_rule_enabled(self, rule_name: str) -> bool:
        """Check if a rule is enabled."""
        rule_config = self.rules.get(rule_name, {})
        return rule_config.get("enabled", True)

    def _get_severity(self, rule_name: str) -> ValidationSeverity:
        """Get severity level for a rule."""
        rule_config = self.rules.get(rule_name, {})
        severity_str = rule_config.get("severity", "warning")
        
        severity_map = {
            "error": ValidationSeverity.ERROR,
            "warning": ValidationSeverity.WARNING,
            "info": ValidationSeverity.INFO,
        }
        
        return severity_map.get(severity_str, ValidationSeverity.WARNING)
