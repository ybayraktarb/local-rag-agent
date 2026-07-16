import socket
import pytest
from src.security.network_guard import activate_network_guard, deactivate_network_guard

@pytest.fixture(scope="function")
def manage_guard():
    """
    Ensures network guard is reset after each test to prevent side-effects on other tests.
    """
    yield
    deactivate_network_guard()

def test_network_guard_blocks_external(manage_guard):
    """
    Tests that external domains and IPs are blocked with a PermissionError when guard is active.
    """
    activate_network_guard()
    
    # Verify domain block
    with pytest.raises(PermissionError) as excinfo:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("google.com", 80))
    assert "AĞ ERİŞİMİ ENGELLENDİ" in str(excinfo.value)
    
    # Verify direct IP block
    with pytest.raises(PermissionError) as excinfo2:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("8.8.8.8", 53))
    assert "AĞ ERİŞİMİ ENGELLENDİ" in str(excinfo2.value)

def test_network_guard_allows_localhost(manage_guard):
    """
    Tests that connections to localhost (127.0.0.1) are allowed when guard is active.
    """
    activate_network_guard()
    
    # Connection to 127.0.0.1 should not raise our guard's PermissionError.
    # The sandbox environment itself might raise standard PermissionError (operation not permitted)
    # or connection errors, which we ignore.
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect(("127.0.0.1", 11434))
    except PermissionError as e:
        if "AĞ ERİŞİMİ ENGELLENDİ" in str(e):
            pytest.fail("NetworkGuard, localhost (127.0.0.1) bağlantısını hatalı bir şekilde engelledi!")
    except Exception:
        # Other standard errors are expected and acceptable
        pass

def test_network_guard_deactivation(manage_guard):
    """
    Tests that deactivating the guard restores standard network connection behavior.
    """
    activate_network_guard()
    deactivate_network_guard()
    
    # After deactivation, connecting to external hosts must not trigger our guard's PermissionError
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect(("google.com", 80))
    except PermissionError as e:
        if "AĞ ERİŞİMİ ENGELLENDİ" in str(e):
            pytest.fail("NetworkGuard, deaktif edildikten sonra hala engelleme yapıyor!")
    except Exception:
        # Standard timeout or network error is acceptable
        pass
