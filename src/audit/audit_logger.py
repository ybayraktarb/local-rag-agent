import json
import os
from datetime import datetime, timezone
from pathlib import Path

from src.config import settings


def _driver():
    try:
        from sqlcipher3 import dbapi2 as sqlite
    except ImportError as exc:
        raise RuntimeError(
            "Şifreli audit için audit extra'sını kurun: pip install -e '.[audit]'"
        ) from exc
    return sqlite


class AuditLogger:
    """SQLCipher-backed query audit log."""

    def __init__(self, db_path=None, key=None):
        self.db_path = str(db_path or Path(settings.AUDIT_DIR) / "audit_log.db")
        self.key = key if key is not None else settings.AUDIT_DB_KEY
        if len(self.key.strip()) < 16:
            raise ValueError("Audit anahtarı en az 16 karakter olmalıdır.")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._initialize()
        try:
            os.chmod(Path(self.db_path).parent, 0o700)
            os.chmod(self.db_path, 0o600)
        except OSError:
            pass

    def _connect(self):
        conn = _driver().connect(self.db_path)
        # SQLCipher's PRAGMA does not support DB-API placeholders. Hex encoding
        # keeps user-controlled key text out of the SQL grammar.
        hex_key = self.key.encode("utf-8").hex()
        conn.execute(f"PRAGMA key = \"x'{hex_key}'\"")
        conn.execute("PRAGMA cipher_memory_security = ON")
        return conn

    def _initialize(self):
        with self._connect() as conn:
            conn.execute("SELECT count(*) FROM sqlite_master")
            conn.execute("""CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, query TEXT NOT NULL,
                answer TEXT NOT NULL, sources TEXT NOT NULL, confidence_score REAL NOT NULL,
                success INTEGER NOT NULL DEFAULT 1)""")

    def log_query(self, query, answer, sources, confidence_score, success=True):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO audit_logs(created_at,query,answer,sources,confidence_score,success) VALUES(?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), query, answer,
                 json.dumps(sources, ensure_ascii=False), float(confidence_score), int(success)),
            )

    def fetch_all_logs(self):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id,created_at,query,answer,sources,confidence_score,success FROM audit_logs ORDER BY id"
            ).fetchall()
        return [{"id": r[0], "created_at": r[1], "query": r[2], "answer": r[3],
                 "sources": json.loads(r[4]), "confidence_score": r[5], "success": bool(r[6])}
                for r in rows]
