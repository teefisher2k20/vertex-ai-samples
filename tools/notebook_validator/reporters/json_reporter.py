"""JSON reporter for validation results."""

from typing import List, Dict, Any
from ..core.models import NotebookValidationReport


class JSONReporter:
    """Generate JSON-formatted validation reports."""

    def generate_report(self, reports: List[NotebookValidationReport]) -> Dict[str, Any]:
        """
        Generate JSON report for validation results.

        Args:
            reports: List of validation reports

        Returns:
            Dictionary suitable for JSON serialization
        """
        total = len(reports)
        passed = sum(1 for r in reports if r.is_valid)
        failed = total - passed

        return {
            "summary": {
                "total_notebooks": total,
                "passed": passed,
                "failed": failed,
                "total_errors": sum(r.error_count for r in reports),
                "total_warnings": sum(r.warning_count for r in reports),
                "total_info": sum(r.info_count for r in reports),
            },
            "reports": [report.to_dict() for report in reports],
        }
