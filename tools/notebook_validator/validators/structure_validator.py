"""Structure validation for notebooks."""

from pathlib import Path
from typing import List, Dict
import nbformat
import re

from ..core.models import ValidationResult, ValidationSeverity


class StructureValidator:
    """Validates notebook structure and organization."""

    def __init__(self, config: Dict):
        """Initialize with configuration."""
        self.config = config
        self.rules = config.get("rules", {})

    def validate(
        self,
        notebook: nbformat.NotebookNode,
        notebook_path: Path,
    ) -> List[ValidationResult]:
        """
        Run all structure validation checks.

        Returns:
            List of validation results
        """
        results = []

        # Run enabled checks
        if self._is_rule_enabled("require_title"):
            results.append(self.check_has_title(notebook))

        if self._is_rule_enabled("require_overview"):
            results.append(self.check_has_overview(notebook))

        if self._is_rule_enabled("require_setup_section"):
            results.append(self.check_has_setup_section(notebook))

        if self._is_rule_enabled("check_cell_order"):
            results.extend(self.check_cell_order(notebook))

        if self._is_rule_enabled("check_section_headers"):
            results.extend(self.check_section_headers(notebook))

        # Filter out None results
        return [r for r in results if r is not None]

    def check_has_title(self, notebook: nbformat.NotebookNode) -> ValidationResult:
        """Verify notebook has a title in first markdown cell."""
        if not notebook.cells:
            return ValidationResult(
                rule_id="structure.require_title",
                severity=self._get_severity("require_title"),
                message="Notebook has no cells",
            )

        # Check first few cells for H1 heading
        for i, cell in enumerate(notebook.cells[:5]):
            if cell.cell_type == "markdown":
                if re.search(r"^#\s+.+", cell.source, re.MULTILINE):
                    return None  # Valid, no issue

        return ValidationResult(
            rule_id="structure.require_title",
            severity=self._get_severity("require_title"),
            message="Notebook should have a title (# heading) in the first markdown cell",
            suggestion="Add a title using: # Your Notebook Title",
        )

    def check_has_overview(self, notebook: nbformat.NotebookNode) -> ValidationResult:
        """Verify notebook has an overview/objective section."""
        overview_keywords = [
            "overview",
            "objective",
            "introduction",
            "what you'll learn",
            "goals",
        ]

        for cell in notebook.cells[:10]:  # Check first 10 cells
            if cell.cell_type == "markdown":
                content_lower = cell.source.lower()
                if any(keyword in content_lower for keyword in overview_keywords):
                    return None  # Found overview

        return ValidationResult(
            rule_id="structure.require_overview",
            severity=self._get_severity("require_overview"),
            message="Notebook should have an overview or objectives section",
            suggestion="Add a section describing what the notebook covers",
        )

    def check_has_setup_section(self, notebook: nbformat.NotebookNode) -> ValidationResult:
        """Verify notebook has installation/setup instructions."""
        setup_keywords = [
            "setup",
            "installation",
            "install",
            "requirements",
            "prerequisites",
        ]

        for cell in notebook.cells[:15]:
            if cell.cell_type == "markdown":
                content_lower = cell.source.lower()
                if any(keyword in content_lower for keyword in setup_keywords):
                    return None  # Found setup section

        return ValidationResult(
            rule_id="structure.require_setup_section",
            severity=self._get_severity("require_setup_section"),
            message="Notebook should have a setup/installation section",
            suggestion="Add a section explaining how to set up the environment",
        )

    def check_cell_order(self, notebook: nbformat.NotebookNode) -> List[ValidationResult]:
        """Verify logical cell ordering (imports before usage, etc.)."""
        results = []
        
        # Check that imports come before other code
        found_non_import_code = False
        import_pattern = r"^\s*(?:import|from)\s+"

        for i, cell in enumerate(notebook.cells):
            if cell.cell_type != "code":
                continue

            has_import = bool(re.search(import_pattern, cell.source, re.MULTILINE))
            has_other_code = bool(
                re.search(r"^\s*[^#\s]", cell.source, re.MULTILINE)
                and not has_import
            )

            if has_other_code:
                found_non_import_code = True

            if found_non_import_code and has_import:
                results.append(
                    ValidationResult(
                        rule_id="structure.check_cell_order",
                        severity=self._get_severity("check_cell_order"),
                        message=f"Import statement found after code execution at cell {i}",
                        cell_index=i,
                        suggestion="Move all imports to the beginning of the notebook",
                    )
                )

        return results

    def check_section_headers(self, notebook: nbformat.NotebookNode) -> List[ValidationResult]:
        """Verify proper markdown header hierarchy."""
        results = []
        last_level = 0

        for i, cell in enumerate(notebook.cells):
            if cell.cell_type != "markdown":
                continue

            # Find all headers in this cell
            headers = re.findall(r"^(#{1,6})\s+.+", cell.source, re.MULTILINE)
            
            for header in headers:
                level = len(header)
                
                # Check for skipped levels (e.g., h1 -> h3)
                if last_level > 0 and level > last_level + 1:
                    results.append(
                        ValidationResult(
                            rule_id="structure.check_section_headers",
                            severity=self._get_severity("check_section_headers"),
                            message=f"Skipped header level from h{last_level} to h{level} at cell {i}",
                            cell_index=i,
                            suggestion=f"Use h{last_level + 1} instead of h{level}",
                        )
                    )
                
                last_level = level

        return results

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
