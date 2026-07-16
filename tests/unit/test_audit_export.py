import pytest

from src.audit.audit_export import _safe


@pytest.mark.parametrize("value", ["=1+1", "+cmd", "-2+3", "@SUM(A1:A2)", "  =1+1"])
def test_spreadsheet_formula_injection_is_neutralized(value):
    assert _safe(value).startswith("'")
