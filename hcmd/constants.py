from enum import Enum, auto

class OS(Enum):
    WINDOWS = "windows"
    MACOS = "darwin"
    LINUX = "linux"
    UNKNOWN = "unknown"

class CommandType(Enum):
    NAVIGATION = auto()
    LIST_FILES = auto()
    CREATE = auto()
    DELETE = auto()
    COPY = auto()
    MOVE = auto()
    UNKNOWN = auto()

SYSTEM_DIRECTORIES = {
    "home": {
        "windows": "%USERPROFILE%",
        "darwin": "~",
        "linux": "~"
    },
    "downloads": {
        "windows": "%USERPROFILE%\\Downloads",
        "darwin": "~/Downloads",
        "linux": "~/Downloads"
    },
    "desktop": {
        "windows": "%USERPROFILE%\\Desktop",
        "darwin": "~/Desktop",
        "linux": "~/Desktop"
    },
    "documents": {
        "windows": "%USERPROFILE%\\Documents",
        "darwin": "~/Documents",
        "linux": "~/Documents"
    }
}
