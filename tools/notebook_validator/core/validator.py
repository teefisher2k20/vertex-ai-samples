"""Core notebook validation orchestrator."""

import time
from pathlib import Path
from typing import List, Optional, Dict
import nbformat
import yaml

from .models import NotebookValidationReport, ValidationResult, ValidationSeverity
from .metadata_extractor import MetadataExtractor
from ..validators.structure_validator import StructureValidator
from ..validators.content_validator import ContentValidator
from ..validators.metadata_validator import MetadataValidator
from ..validators.dependency_validator import DependencyValidator


class NotebookValidator:
    """Main orchestrator for notebook validation."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize validator with configuration.

        Args:
            config_path: Path to validation rules YAML file
        """
        self.config = self._load_config(config_path)
        self.metadata_extractor = MetadataExtractor()
        
        # Initialize validators
        self.validators = {
            "structure": StructureValidator(self.config.get("structure", {})),
            "content": ContentValidator(self.config.get("content", {})),
            "metadata": MetadataValidator(self.config.get("metadata", {})),
            "dependencies": DependencyValidator(self.config.get("dependencies", {})),
        }

    def _load_config(self, config_path: Optional[Path]) -> Dict:
        """Load validation configuration from YAML file."""
        if config_path and config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Get default validation configuration."""
        return {
            "structure": {"enabled": True},
            "content": {"enabled": True},
            "metadata": {"enabled": True},
            "dependencies": {"enabled": True},
        }

    def validate_notebook(
        self,
        notebook_path: Path,
        validators: Optional[List[str]] = None,
    ) -> NotebookValidationReport:
        """
        Validate a single notebook.

        Args:
            notebook_path: Path to the notebook file
            validators: List of validator names to run (None = all enabled)

        Returns:
            NotebookValidationReport with all validation results
        """
        start_time = time.time()
        
        # Parse notebook
        try:
            with open(notebook_path, "r", encoding="utf-8") as f:
                notebook = nbformat.read(f, as_version=4)
        except Exception as e:
            return NotebookValidationReport(
                notebook_path=str(notebook_path),
                is_valid=False,
                validation_results=[
                    ValidationResult(
                        rule_id="parse_error",
                        severity=ValidationSeverity.ERROR,
                        message=f"Failed to parse notebook: {str(e)}",
                    )
                ],
                execution_time=time.time() - start_time,
            )

        # Extract metadata
        metadata = None
        try:
            metadata = self.metadata_extractor.extract_metadata(notebook, notebook_path)
        except Exception as e:
            # Non-fatal, continue with validation
            pass

        # Run validators
        all_results = []
        validators_to_run = validators or list(self.validators.keys())
        
        for validator_name in validators_to_run:
            if validator_name not in self.validators:
                continue
            
            validator = self.validators[validator_name]
            if not self._is_validator_enabled(validator_name):
                continue
            
            try:
                results = validator.validate(notebook, notebook_path)
                all_results.extend(results)
            except Exception as e:
                all_results.append(
                    ValidationResult(
                        rule_id=f"{validator_name}_error",
                        severity=ValidationSeverity.ERROR,
                        message=f"Validator {validator_name} failed: {str(e)}",
                    )
                )

        # Determine overall validity
        has_errors = any(r.severity == ValidationSeverity.ERROR for r in all_results)
        is_valid = not has_errors

        execution_time = time.time() - start_time

        return NotebookValidationReport(
            notebook_path=str(notebook_path),
            is_valid=is_valid,
            validation_results=all_results,
            metadata=metadata,
            execution_time=execution_time,
        )

    def validate_directory(
        self,
        directory_path: Path,
        recursive: bool = True,
        pattern: str = "*.ipynb",
    ) -> List[NotebookValidationReport]:
        """
        Validate all notebooks in a directory.

        Args:
            directory_path: Directory to scan
            recursive: Whether to scan subdirectories
            pattern: Glob pattern for notebook files

        Returns:
            List of validation reports
        """
        reports = []
        
        if recursive:
            notebooks = directory_path.rglob(pattern)
        else:
            notebooks = directory_path.glob(pattern)

        for notebook_path in notebooks:
            # Skip checkpoint files
            if ".ipynb_checkpoints" in str(notebook_path):
                continue
            
            report = self.validate_notebook(notebook_path)
            reports.append(report)

        return reports

    def _is_validator_enabled(self, validator_name: str) -> bool:
        """Check if a validator is enabled in config."""
        validator_config = self.config.get(validator_name, {})
        return validator_config.get("enabled", True)
