from enum import Enum, auto
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

INTENT_MODEL_PATH = os.path.join(PROJECT_ROOT, "intent_model")
NAVIGATION_SPAN_MODEL_PATH = os.path.join(PROJECT_ROOT, "directory_span_model")
SRC_SPAN_MODEL_PATH = os.path.join(PROJECT_ROOT, "src_span_model")
DST_SPAN_MODEL_PATH = os.path.join(PROJECT_ROOT, "dst_span_model")
OBJECT_SPAN_MODEL_PATH = os.path.join(PROJECT_ROOT, "object_span_model")
RENAME_SPAN_MODEL_PATH = os.path.join(PROJECT_ROOT, "rename_span_model")
GIT_ADD_MODEL_PATH = os.path.join(PROJECT_ROOT, "git_add_model")
GIT_CHECKOUT_MODEL_PATH = os.path.join(PROJECT_ROOT, "git_checkout_model")
GIT_CLONE_MODEL_PATH = os.path.join(PROJECT_ROOT, "git_clone_model")

INTENT_CONF_THRESHOLD = 0.30
SPAN_CONF_THRESHOLD = 0.25

INTENTS = {
    "NAVIGATION",
    "LIST_FILES",
    "PWD",
    "CREATE_FILE",
    "CREATE_DIR",
    "DELETE_FILE",
    "COPY_FILE",
    "MOVE_FILE",
    "RENAME_FILE",
    "READ_FILE",
    "GIT_STATUS",
    "GIT_BRANCH",
}


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
