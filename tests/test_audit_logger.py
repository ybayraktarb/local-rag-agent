import os
import pytest
from src.audit.audit_logger import AuditLogger
from src.audit.audit_export import export_audit_logs

TEST_AUDIT_KEY = "test_key_password"
TEST_AUDIT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../audit_test"))
TEST_DB_PATH = os.path.join(TEST_AUDIT_DIR, "audit_log_test.db")
TEST_CSV_PATH = os.path.join(TEST_AUDIT_DIR, "audit_export.csv")
TEST_XLSX_PATH = os.path.join(TEST_AUDIT_DIR, "audit_export.xlsx")

@pytest.fixture(scope="function")
def clean_audit_env():
    """
    Clean up test database and export files before and after runs.
    """
    import shutil
    if os.path.exists(TEST_AUDIT_DIR):
        shutil.rmtree(TEST_AUDIT_DIR, ignore_errors=True)
    os.makedirs(TEST_AUDIT_DIR, exist_ok=True)
    yield
    if os.path.exists(TEST_AUDIT_DIR):
        shutil.rmtree(TEST_AUDIT_DIR, ignore_errors=True)

def test_audit_logger_write_read_export(clean_audit_env):
    """
    Verify writing logs, reading logs, decryption failure with wrong key,
    and exporting to CSV/Excel formats.
    """
    # 1. Initialize and write a log
    logger = AuditLogger(db_path=TEST_DB_PATH, key=TEST_AUDIT_KEY)
    
    mock_sources = [
        {"source": "mevduat_proseduru.pdf", "page": 2},
        {"source": "faiz_oranlari.pdf", "page": 1}
    ]
    logger.log_query(
        query="Faiz güncellemesi kuralları nedir?",
        answer="Yönetim kurulu onayı gereklidir.",
        sources=mock_sources,
        confidence_score=0.78
    )
    
    # 2. Read log back and verify
    logs = logger.fetch_all_logs()
    assert len(logs) == 1
    assert logs[0]["query"] == "Faiz güncellemesi kuralları nedir?"
    assert logs[0]["answer"] == "Yönetim kurulu onayı gereklidir."
    assert logs[0]["sources"] == mock_sources
    assert logs[0]["confidence_score"] == pytest.approx(0.78)
    
    # 3. Verify decryption failure with incorrect key
    # Opening the database file with a wrong key must raise an exception when querying
    with pytest.raises(Exception):
        wrong_logger = AuditLogger(db_path=TEST_DB_PATH, key="incorrect_secret_password")
        # Fetching logs should trigger decryption failure
        wrong_logger.fetch_all_logs()

    # 4. Verify CSV Export
    export_audit_logs(export_path=TEST_CSV_PATH, db_path=TEST_DB_PATH, key=TEST_AUDIT_KEY, format="csv")
    assert os.path.exists(TEST_CSV_PATH)
    with open(TEST_CSV_PATH, "r", encoding="utf-8-sig") as f:
        csv_content = f.read()
        assert "Faiz güncellemesi kuralları nedir?" in csv_content
        assert "Yönetim kurulu onayı gereklidir." in csv_content
        assert "mevduat_proseduru.pdf (S.2)" in csv_content
        assert "faiz_oranlari.pdf (S.1)" in csv_content

    # 5. Verify Excel Export
    export_audit_logs(export_path=TEST_XLSX_PATH, db_path=TEST_DB_PATH, key=TEST_AUDIT_KEY, format="xlsx")
    assert os.path.exists(TEST_XLSX_PATH)
