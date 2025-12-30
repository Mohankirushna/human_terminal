"""
hcmd - Human to Command

A command-line tool that converts natural language instructions into terminal commands.
"""

__version__ = "0.1.0"

# Import core components
from .core import detector, generator, executor, validator

# Re-export commonly used functions and classes
from .core.detector import get_os, get_shell, get_system_directory
from .core.generator import CommandGenerator
from .core.executor import CommandExecutor
from .core.validator import is_command_safe, validate_command_type

# Export public API
__all__ = [
    'get_os',
    'get_shell',
    'get_system_directory',
    'CommandGenerator',
    'CommandExecutor',
    'is_command_safe',
    'validate_command_type',
    'detector',
    'generator',
    'executor',
    'validator'
]
