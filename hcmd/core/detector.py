"""OS detection module for the hcmd tool."""
import platform
import os
import sys
from typing import Tuple

from ..constants import OS, SYSTEM_DIRECTORIES

def detect_os() -> Tuple[OS, str]:
    """
    Detect the current operating system and shell.
    
    Returns:
        Tuple[OS, str]: A tuple containing the detected OS and shell name.
    """
    system = platform.system()  # Don't convert to lowercase for more accurate comparison
    shell = None
    
    if system == 'Windows':
        os_type = OS.WINDOWS
        # Check if PowerShell exists, otherwise default to cmd.exe
        powershell_path = os.path.join(os.environ.get('SYSTEMROOT', 'C:\\Windows'), 
                                       'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
        shell = 'powershell.exe' if os.path.exists(powershell_path) else 'cmd.exe'
    elif system == 'Darwin':
        os_type = OS.MACOS
        shell = os.environ.get('SHELL', '/bin/zsh')
    elif system == 'Linux':
        os_type = OS.LINUX
        shell = os.environ.get('SHELL', '/bin/bash')
    else:
        os_type = OS.UNKNOWN
        shell = 'bash'
    
    # Clean up the shell path to just the executable name
    if shell:
        shell = os.path.basename(shell)
    
    return os_type, shell

def get_system_directory(directory_name: str, os_type: OS = None) -> str:
    """
    Get the system directory path for the current OS.
    
    Args:
        directory_name: Name of the directory (e.g., 'home', 'downloads')
        os_type: Optional OS type, will detect if not provided
        
    Returns:
        str: The path to the requested system directory
    """
    if os_type is None:
        os_type, _ = detect_os()
    
    directory_name = directory_name.lower()
    if directory_name in SYSTEM_DIRECTORIES:
        return SYSTEM_DIRECTORIES[directory_name].get(os_type.value, '')
    return ''

# Cache for OS detection
_os_cache = None
_shell_cache = None

def get_os() -> OS:
    """Get the current OS (cached)."""
    global _os_cache
    if _os_cache is None:
        _os_cache, _ = detect_os()
    return _os_cache

def get_shell() -> str:
    """Get the current shell (cached)."""
    global _shell_cache
    if _shell_cache is None:
        _, _shell_cache = detect_os()
    return _shell_cache