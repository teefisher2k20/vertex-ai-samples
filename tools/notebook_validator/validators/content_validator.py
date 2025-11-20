"""Content validation for notebooks."""

from pathlib import Path
from typing import List, Dict
import nbformat
import re

from ..core.models import ValidationResult, ValidationSeverity


class ContentValidator:
    """Validates notebook content quality."""

    def __init__(self, config: Dict):
        """Initialize with configuration."""
        self.config = config
        self.rules = config.get("rules", {})

    def validate(
        self,
        notebook: nbformat.NotebookNode,
        notebook_path: Path,
    ) -> List[ValidationResult]:
        """Run all content validation checks."""
        results = []

        if self._is_rule_enabled("hardcoded_values"):
            results.extend(self.check_hardcoded_values(notebook))

        if self._is_rule_enabled("output_cells"):
            results.extend(self.check_output_cells(notebook))

        if self._is_rule_enabled("markdown_links"):
            results.extend(self.check_markdown_links(notebook))

        if self._is_rule_enabled("documentation"):
            results.extend(self.check_documentation(notebook))

        return [r for r in results if r is not None]

    def check_hardcoded_values(self, notebook: nbformat.NotebookNode) -> List[ValidationResult]:
        """Detect hardcoded project IDs, regions, credentials."""
        results = []
        
        # Get patterns from config or use defaults
        patterns_config = self.rules.get("hardcoded_values", {}).get("patterns", [])
        
        default_patterns = [
            {
                "pattern": r'project_id\s*=\s*["\'](?!YOUR_PROJECT_ID|<|{)[^"\']+["\']',
                "message": "Hardcoded project_id found. Use environment variable or parameter",
                "suggestion": 'Use: project_id = os.environ.get("PROJECT_ID", "YOUR_PROJECT_ID")',
            },
            {
                "pattern": r'region\s*=\s*["\'](?!YOUR_REGION|<|{)[^"\']+["\']',
                "message": "Hardcoded region found. Use environment variable or parameter",
                "suggestion": 'Use: region = os.environ.get("REGION", "YOUR_REGION")',
            },
            {
                "pattern": r'(?:api_key|API_KEY)\s*=\s*["\'][^"\']+["\']',
                "message": "Hardcoded API key found. This is a security risk!",
                "suggestion": "Use environment variables or Secret Manager for credentials",
            },
        ]

        patterns = patterns_config if patterns_config else default_patterns

        for i, cell in enumerate(notebook.cells):
            if cell.cell_type != "code":
                continue

            for pattern_config in patterns:
                pattern = pattern_config["pattern"]
                matches = re.finditer(pattern, cell.source)
                
                for match in matches:
                    # Find line number
                    line_num = cell.source[:match.start()].count("\n") + 1
                    
                    results.append(
                        ValidationResult(
                            rule_id="content.hardcoded_values",
                            severity=self._get_severity("hardcoded_values"),
                            message=pattern_config["message"],
                            cell_index=i,
                            line_number=line_num,
                            suggestion=pattern_config.get("suggestion"),
                        )
                    )

        return results

    def check_output_cells(self, notebook: nbformat.NotebookNode) -> List[ValidationResult]:
        """Verify output cells are cleared or contain expected outputs."""
        results = []
        max_output_size = self.rules.get("output_cells", {}).get("max_output_size", 10000)

        for i, cell in enumerate(notebook.cells):
            if cell.cell_type != "code":
                continue

            if not hasattr(cell, "outputs") or not cell.outputs:
                continue

            # Check output size
            total_size = 0
            for output in cell.outputs:
                if "data" in output:
                    for key, value in output["data"].items():
                        if isinstance(value, str):
                            total_size += len(value)
                        elif isinstance(value, list):
                            total_size += sum(len(str(v)) for v in value)

            if total_size > max_output_size:
                results.append(
                    ValidationResult(
                        rule_id="content.output_cells",
                        severity=self._get_severity("output_cells"),
                        message=f"Large output ({total_size} bytes) at cell {i}. Consider clearing outputs",
                        cell_index=i,
                        suggestion="Clear outputs before committing: Cell -> All Output -> Clear",
                    )
                )

        return results

    def check_markdown_links(self, notebook: nbformat.NotebookNode) -> List[ValidationResult]:
        """Verify all markdown links are valid (not broken)."""
        results = []
        
        # Extract all markdown links
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'

        for i, cell in enumerate(notebook.cells):
            if cell.cell_type != "markdown":
                continue

            matches = re.finditer(link_pattern, cell.source)
            
            for match in matches:
                link_text = match.group(1)
                link_url = match.group(2)
                
                # Skip anchor links and relative paths (would need context to validate)
                if link_url.startswith("#") or not link_url.startswith("http"):
                    continue

                # Basic validation - check for common issues
                if " " in link_url:
                    results.append(
                        ValidationResult(
                            rule_id="content.markdown_links",
                            severity=self._get_severity("markdown_links"),
                            message=f"Link contains spaces: {link_url}",
                            cell_index=i,
                            suggestion="Encode spaces as %20 or remove them",
                        )
                    )

        return results

    def check_documentation(self, notebook: nbformat.NotebookNode) -> List[ValidationResult]:
        """Verify adequate documentation."""
        results = []
        
        if not notebook.cells:
            return results

        # Calculate markdown to code ratio
        markdown_cells = sum(1 for cell in notebook.cells if cell.cell_type == "markdown")
        code_cells = sum(1 for cell in notebook.cells if cell.cell_type == "code")
        
        if code_cells == 0:
            return results

        markdown_ratio = markdown_cells / (markdown_cells + code_cells)
        min_ratio = self.rules.get("documentation", {}).get("min_markdown_ratio", 0.2)

        if markdown_ratio < min_ratio:
            results.append(
                ValidationResult(
                    rule_id="content.documentation",
                    severity=self._get_severity("documentation"),
                    message=f"Low documentation ratio: {markdown_ratio:.1%} (minimum: {min_ratio:.1%})",
                    suggestion="Add more markdown cells to explain the code",
                )
            )

        # Check for code cells without preceding markdown
        last_was_markdown = True
        consecutive_code = 0

        for i, cell in enumerate(notebook.cells):
            if cell.cell_type == "markdown":
                last_was_markdown = True
                consecutive_code = 0
            elif cell.cell_type == "code":
                if not last_was_markdown:
                    consecutive_code += 1
                else:
                    consecutive_code = 1
                last_was_markdown = False

                # Warn if too many consecutive code cells
                if consecutive_code > 5:
                    results.append(
                        ValidationResult(
                            rule_id="content.documentation",
                            severity=ValidationSeverity.INFO,
                            message=f"Many consecutive code cells without explanation (cell {i})",
                            cell_index=i,
                            suggestion="Add markdown cells to explain what the code does",
                        )
                    )
                    consecutive_code = 0  # Reset to avoid duplicate warnings

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
