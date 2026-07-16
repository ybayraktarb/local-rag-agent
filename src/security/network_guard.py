import socket
import logging

logger = logging.getLogger(__name__)

# Keep a reference to the original socket connect method
_original_connect = socket.socket.connect

# Allowed localhost endpoints
ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}

def guard_connect(self, address):
    """
    Patched socket.connect method that intercept and block non-localhost connections.
    """
    host = address[0]
    is_allowed = False
    
    if host in ALLOWED_HOSTS:
        is_allowed = True
    else:
        try:
            # Resolve hostname to verify if it maps to localhost
            resolved_ip = socket.gethostbyname(host)
            if resolved_ip in ALLOWED_HOSTS:
                is_allowed = True
        except Exception:
            # Resolution failure indicates it is not localhost
            pass

    if not is_allowed:
        error_msg = (
            f"AĞ ERİŞİMİ ENGELLENDİ: '{host}' dış adresine erişim engellendi. "
            "Uygulama katmanındaki NetworkGuard yalnızca localhost bağlantılarına izin veriyor."
        )
        logger.error(error_msg)
        raise PermissionError(error_msg)
        
    return _original_connect(self, address)

def activate_network_guard():
    """
    Activates the network guard globally by monkeypatching socket connection calls.
    """
    socket.socket.connect = guard_connect
    logger.info("NetworkGuard Aktif: Dış ağ istekleri engellendi (Yalnızca localhost izinli).")

def deactivate_network_guard():
    """
    Deactivates the network guard (primarily for unit testing cleanup).
    """
    socket.socket.connect = _original_connect
    logger.info("NetworkGuard Devre Dışı: Dış ağ isteklerine izin veriliyor.")
