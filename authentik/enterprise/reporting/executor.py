from structlog.stdlib import get_logger

from authentik.enterprise.reporting.models import Report


class ReportExecutor:
    """Execute a report"""

    def __init__(self, report: Report) -> None:
        self.report = report
        self.logger = get_logger().bind(report=self.report)

    def execute(self):
        # 1. Run through policies bound to report itself
        # 2. Get all bound components by running through ReportComponentBinding,
        #   while evaluating policies bound to each
        # 3. render the actual components
        # 4. Store the final data...somewhere??
        # 5. Optionally render PDF via chromedriver (special frontend that uses API)
        #   (not required for MVP)
        # 6. Send out link to CSV/PDF or attach to email via delivery
        pass
