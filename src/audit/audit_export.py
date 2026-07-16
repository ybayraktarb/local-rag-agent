import csv
from pathlib import Path

from src.audit.audit_logger import AuditLogger


def _safe(value):
    text = str(value)
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text


def export_audit_logs(export_path, db_path=None, key=None, format="csv"):
    logs = AuditLogger(db_path=db_path, key=key).fetch_all_logs()
    rows = []
    for item in logs:
        sources = ", ".join(f"{s.get('source', '')} (S.{s.get('page', '')})" for s in item["sources"])
        rows.append([item["created_at"], _safe(item["query"]), _safe(item["answer"]),
                     _safe(sources), item["confidence_score"], item["success"]])
    path = Path(export_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = ["created_at", "query", "answer", "sources", "confidence_score", "success"]
    if format == "csv":
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle); writer.writerow(headers); writer.writerows(rows)
    elif format == "xlsx":
        from openpyxl import Workbook
        book = Workbook(); sheet = book.active; sheet.append(headers)
        for row in rows: sheet.append(row)
        book.save(path)
    else:
        raise ValueError("format 'csv' veya 'xlsx' olmalıdır")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return str(path)
