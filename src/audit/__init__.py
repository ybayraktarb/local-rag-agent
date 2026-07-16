"""Optional encrypted audit support."""
from typing import Any

from src.config import settings


class NoOpAuditLogger:
    def log_query(self, *args: Any, **kwargs: Any) -> None:
        return None

    def fetch_all_logs(self):
        return []


def create_audit_logger():
    if not settings.AUDIT_ENABLED:
        return NoOpAuditLogger()
    settings.validate_audit_settings()
    from src.audit.audit_logger import AuditLogger
    return AuditLogger()
