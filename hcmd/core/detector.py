import platform
import os
from ..constants import OS, SYSTEM_DIRECTORIES

def get_os() -> OS:
    sys = platform.system()
    if sys == "Windows":
        return OS.WINDOWS
    if sys == "Darwin":
        return OS.MACOS
    if sys == "Linux":
        return OS.LINUX
    return OS.UNKNOWN

def get_shell() -> str:
    if get_os() == OS.WINDOWS:
        return "powershell"
    return os.environ.get("SHELL", "/bin/bash")

def get_system_directory(name: str, os_type: OS) -> str:
    return SYSTEM_DIRECTORIES.get(name, {}).get(os_type.value, "")
