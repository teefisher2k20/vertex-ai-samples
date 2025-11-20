"""Console reporter for validation results."""

from typing import List
from ..core.models import NotebookValidationReport, ValidationSeverity


class ConsoleReporter:
    """Generate console-formatted validation reports."""

    # ANSI color codes
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def generate_report(self, reports: List[NotebookValidationReport]) -> str:
        """
        Generate console report for validation results.

        Args:
            reports: List of validation reports

        Returns:
            Formatted console output
        """
        if len(reports) == 1:
            return self._generate_single_report(reports[0])
        else:
            return self._generate_summary_report(reports)

    def _generate_single_report(self, report: NotebookValidationReport) -> str:
        """Generate report for a single notebook."""
        lines = []
        
        # Header
        lines.append(f"\n{self.BOLD}Validating:{self.RESET} {report.notebook_path}")
        lines.append("=" * 80)
        
        # Group results by severity
        errors = [r for r in report.validation_results if r.severity == ValidationSeverity.ERROR]
        warnings = [r for r in report.validation_results if r.severity == ValidationSeverity.WARNING]
        infos = [r for r in report.validation_results if r.severity == ValidationSeverity.INFO]

        # Errors
        if errors:
            lines.append(f"\n{self.RED}{self.BOLD}Errors:{self.RESET}")
            for result in errors:
                lines.append(self._format_result(result, self.RED))

        # Warnings
        if warnings:
            lines.append(f"\n{self.YELLOW}{self.BOLD}Warnings:{self.RESET}")
            for result in warnings:
                lines.append(self._format_result(result, self.YELLOW))

        # Info
        if infos:
            lines.append(f"\n{self.BLUE}{self.BOLD}Info:{self.RESET}")
            for result in infos:
                lines.append(self._format_result(result, self.BLUE))

        # Summary
        lines.append("\n" + "=" * 80)
        lines.append(f"{self.BOLD}Summary:{self.RESET}")
        lines.append(f"  {self.RED}✗{self.RESET} {len(errors)} errors")
        lines.append(f"  {self.YELLOW}⚠{self.RESET} {len(warnings)} warnings")
        lines.append(f"  {self.BLUE}ℹ{self.RESET} {len(infos)} info")
        
        # Overall status
        if report.is_valid:
            lines.append(f"\n{self.GREEN}{self.BOLD}✓ Validation: PASSED{self.RESET}")
        else:
            lines.append(f"\n{self.RED}{self.BOLD}✗ Validation: FAILED{self.RESET}")
            lines.append(f"\n{self.YELLOW}Fix the errors above and re-run validation.{self.RESET}")

        lines.append(f"\nExecution time: {report.execution_time:.2f}s")
        
        return "\n".join(lines)

    def _generate_summary_report(self, reports: List[NotebookValidationReport]) -> str:
        """Generate summary report for multiple notebooks."""
        lines = []
        
        # Header
        lines.append(f"\n{self.BOLD}Validation Summary{self.RESET}")
        lines.append("=" * 80)
        
        # Overall stats
        total = len(reports)
        passed = sum(1 for r in reports if r.is_valid)
        failed = total - passed
        
        total_errors = sum(r.error_count for r in reports)
        total_warnings = sum(r.warning_count for r in reports)
        total_infos = sum(r.info_count for r in reports)

        lines.append(f"\nTotal notebooks: {total}")
        lines.append(f"  {self.GREEN}✓{self.RESET} Passed: {passed}")
        lines.append(f"  {self.RED}✗{self.RESET} Failed: {failed}")
        lines.append(f"\nTotal issues:")
        lines.append(f"  {self.RED}✗{self.RESET} Errors: {total_errors}")
        lines.append(f"  {self.YELLOW}⚠{self.RESET} Warnings: {total_warnings}")
        lines.append(f"  {self.BLUE}ℹ{self.RESET} Info: {total_infos}")

        # Failed notebooks
        if failed > 0:
            lines.append(f"\n{self.RED}{self.BOLD}Failed Notebooks:{self.RESET}")
            for report in reports:
                if not report.is_valid:
                    lines.append(
                        f"  {self.RED}✗{self.RESET} {report.notebook_path} "
                        f"({report.error_count} errors, {report.warning_count} warnings)"
                    )

        # Passed notebooks
        if passed > 0:
            lines.append(f"\n{self.GREEN}{self.BOLD}Passed Notebooks:{self.RESET}")
            for report in reports:
                if report.is_valid:
                    status = f"({report.warning_count} warnings)" if report.warning_count > 0 else ""
                    lines.append(f"  {self.GREEN}✓{self.RESET} {report.notebook_path} {status}")

        return "\n".join(lines)

    def _format_result(self, result, color: str) -> str:
        """Format a single validation result."""
        lines = []
        
        # Main message
        location = ""
        if result.cell_index is not None:
            location = f" (cell {result.cell_index}"
            if result.line_number is not None:
                location += f", line {result.line_number}"
            location += ")"
        
        lines.append(f"  {color}●{self.RESET} {result.message}{location}")
        
        # Suggestion
        if result.suggestion:
            lines.append(f"    {self.BLUE}→{self.RESET} {result.suggestion}")
        
        return "\n".join(lines)
