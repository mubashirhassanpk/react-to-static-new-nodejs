"""
Port auto-detection utility for standalone desktop application
"""
import socket
from typing import Optional

def find_available_port(start_port: int = 8000, end_port: int = 9000) -> Optional[int]:
    """
    Find an available port in the specified range
    
    Args:
        start_port: Starting port number
        end_port: Ending port number
    
    Returns:
        Available port number or None if no port is available
    """
    for port in range(start_port, end_port):
        if is_port_available(port):
            return port
    return None


def is_port_available(port: int) -> bool:
    """
    Check if a port is available
    
    Args:
        port: Port number to check
    
    Returns:
        True if port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return True
    except OSError:
        return False


def get_backend_url(port: int) -> str:
    """
    Get the backend URL for a given port
    
    Args:
        port: Port number
    
    Returns:
        Complete backend URL
    """
    return f"http://127.0.0.1:{port}"
