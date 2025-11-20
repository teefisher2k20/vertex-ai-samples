"""Dependency validation for notebooks."""

from pathlib import Path
from typing import List, Dict
import nbformat
import re

from ..core.models import ValidationResult, ValidationSeverity


class DependencyValidator:
    """Validates dependencies and compatibility."""

    # Known deprecated APIs
    DEPRECATED_APIS = {
        "google.cloud.automl_v1beta1": {
            "replacement": "google.cloud.automl_v1",
            "deprecated_since": "2023-01-01",
        },
        "google.cloud.aiplatform.gapic": {
            "replacement": "google.cloud.aiplatform",
            "deprecated_since": "2022-06-01",
        },
    }

    def __init__(self, config: Dict):
        """Initialize with configuration."""
        self.config = config
        self.rules = config.get("rules", {})

    def validate(
        self,
        notebook: nbformat.NotebookNode,
        notebook_path: Path,
    ) -> List[ValidationResult]:
        """Run all dependency validation checks."""
        results = []

        if self._is_rule_enabled("version_pinning"):
            results.extend(self.check_dependency_versions(notebook))

        if self._is_rule_enabled("deprecated_apis"):
            results.extend(self.check_deprecated_apis(notebook))

        if self._is_rule_enabled("import_availability"):
            results.extend(self.check_import_availability(notebook))

        return results

    def check_dependency_versions(self, notebook: nbformat.NotebookNode) -> List[ValidationResult]:
        """Verify dependencies have version pins."""
        results = []
        allow_unpinned = self.rules.get("version_pinning", {}).get("allow_unpinned", [])

        for i, cell in enumerate(notebook.cells):
            if cell.cell_type != "code":
                continue

            # Look for pip install commands
            pip_pattern = r"!pip\s+install\s+(.+)"
            matches = re.finditer(pip_pattern, cell.source)

            for match in matches:
                packages = match.group(1).strip()
                
                # Parse packages
                for pkg in packages.split():
                    pkg = pkg.strip()
                    if pkg.startswith("-"):  # Skip flags
                        continue

                    # Check if version is pinned
                    has_version = "==" in pkg or ">=" in pkg or "<=" in pkg or "~=" in pkg
                    
                    # Extract package name
                    pkg_name = re.split(r"[><=~!]", pkg)[0]

                    if not has_version and pkg_name not in allow_unpinned:
                        line_num = cell.source[:match.start()].count("\n") + 1
                        results.append(
                            ValidationResult(
                                rule_id="dependencies.version_pinning",
                                severity=self._get_severity("version_pinning"),
                                message=f"Unpinned dependency: {pkg_name}",
                                cell_index=i,
                                line_number=line_num,
                                suggestion=f"Pin version: !pip install {pkg_name}==x.y.z",
                            )
                        )

        return results

    def check_deprecated_apis(self, notebook: nbformat.NotebookNode) -> List[ValidationResult]:
        """Detect usage of deprecated Vertex AI APIs."""
        results = []

        # Get custom deprecated APIs from config
        custom_deprecated = self.rules.get("deprecated_apis", {}).get("deprecated_imports", [])
        
        # Merge with built-in deprecated APIs
        all_deprecated = dict(self.DEPRECATED_APIS)
        for item in custom_deprecated:
            all_deprecated[item["old"]] = {
                "replacement": item["new"],
                "deprecated_since": item.get("deprecated_since", "unknown"),
            }

        for i, cell in enumerate(notebook.cells):
            if cell.cell_type != "code":
                continue

            for old_api, info in all_deprecated.items():
                if old_api in cell.source:
                    line_num = cell.source.find(old_api)
                    line_num = cell.source[:line_num].count("\n") + 1
                    
                    results.append(
                        ValidationResult(
                            rule_id="dependencies.deprecated_apis",
                            severity=self._get_severity("deprecated_apis"),
                            message=f"Deprecated API usage: {old_api}",
                            cell_index=i,
                            line_number=line_num,
                            suggestion=f"Use {info['replacement']} instead (deprecated since {info['deprecated_since']})",
                        )
                    )

        return results

    def check_import_availability(self, notebook: nbformat.NotebookNode) -> List[ValidationResult]:
        """Verify all imports are in declared dependencies."""
        results = []

        # Extract all pip install packages
        installed_packages = set()
        for cell in notebook.cells:
            if cell.cell_type != "code":
                continue

            pip_pattern = r"!pip\s+install\s+(.+)"
            matches = re.finditer(pip_pattern, cell.source)
            
            for match in matches:
                packages = match.group(1).strip()
                for pkg in packages.split():
                    pkg = pkg.strip()
                    if not pkg.startswith("-"):
                        # Extract package name (before version specifier)
                        pkg_name = re.split(r"[><=~!]", pkg)[0]
                        installed_packages.add(pkg_name.lower())

        # Extract all imports
        import_pattern = r"^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)"
        
        for i, cell in enumerate(notebook.cells):
            if cell.cell_type != "code":
                continue

            matches = re.finditer(import_pattern, cell.source, re.MULTILINE)
            
            for match in matches:
                module = match.group(1).split(".")[0]  # Get top-level module
                
                # Skip standard library modules
                stdlib_modules = {
                    "os", "sys", "re", "json", "time", "datetime", "pathlib",
                    "typing", "collections", "itertools", "functools", "math",
                    "random", "io", "csv", "logging", "unittest", "dataclasses",
                }
                
                if module in stdlib_modules:
                    continue

                # Check if module is installed
                # Map common import names to package names
                package_map = {
                    "google": "google-cloud-aiplatform",
                    "sklearn": "scikit-learn",
                    "cv2": "opencv-python",
                    "PIL": "pillow",
                }
                
                package_name = package_map.get(module, module)
                
                if package_name.lower() not in installed_packages:
                    line_num = cell.source[:match.start()].count("\n") + 1
                    results.append(
                        ValidationResult(
                            rule_id="dependencies.import_availability",
                            severity=self._get_severity("import_availability"),
                            message=f"Import '{module}' not found in pip install commands",
                            cell_index=i,
                            line_number=line_num,
                            suggestion=f"Add: !pip install {package_name}",
                        )
                    )

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
