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
    OPEN = auto()
    MOVE = auto()
    COPY = auto()
    UNKNOWN = auto()

# Common system directories with platform-agnostic placeholders
SYSTEM_DIRECTORIES = {
    'home': {
        'windows': '%USERPROFILE%',
        'darwin': '~',
        'linux': '~'
    },
    'desktop': {
        'windows': '%USERPROFILE%\\Desktop',
        'darwin': '~/Desktop',
        'linux': '~/Desktop'
    },
    'documents': {
        'windows': '%USERPROFILE%\\Documents',
        'darwin': '~/Documents',
        'linux': '~/Documents'
    },
    'downloads': {
        'windows': '%USERPROFILE%\\Downloads',
        'darwin': '~/Downloads',
        'linux': '~/Downloads'
    },
    'pictures': {
        'windows': '%USERPROFILE%\\Pictures',
        'darwin': '~/Pictures',
        'linux': '~/Pictures'
    },
    'music': {
        'windows': '%USERPROFILE%\\Music',
        'darwin': '~/Music',
        'linux': '~/Music'
    },
    'videos': {
        'windows': '%USERPROFILE%\\Videos',
        'darwin': '~/Movies',
        'linux': '~/Videos'
    }
}

# Known dangerous commands and patterns
DANGEROUS_PATTERNS = [
    r'rm\s+-[^\s]*(r|f|rf|fr)',
    r'del\s+[\\/]?[a-zA-Z]:[\\/]',
    r'format\s+[a-zA-Z]:?',
    r'shutdown\s+',
    r'diskpart',
    r'mkfs',
    r'dd\s+if=',
    r'chmod\s+[0-7]{3,4}\s+',
    r'chown\s+-[^\s]*R',
    r'\|\s*\b(rm|shutdown|halt|poweroff|reboot|dd|mkfs|:(){:|:&};:|wget\s+http|curl\s+http|bash\s+<\s*\()'  # noqa: E501
]
