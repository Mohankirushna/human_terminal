"""
Core functionality for the hcmd tool.

This module contains the core components for the hcmd command-line tool,
including command generation, execution, and validation.
"""

# Import core modules to make them available when importing from hcmd.core
from .detector import get_os, get_shell, get_system_directory
from .generator import CommandGenerator
from .executor import CommandExecutor
from .validator import is_command_safe, validate_command_type, extract_paths, sanitize_input

# Define __all__ to specify the public API
__all__ = [
    'get_os',
    'get_shell',
    'get_system_directory',
    'CommandGenerator',
    'CommandExecutor',
    'is_command_safe',
    'validate_command_type',
    'extract_paths',
    'sanitize_input'
]
