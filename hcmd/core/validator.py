"""Command validation module for the hcmd tool."""
import re
from typing import List, Optional, Tuple

from ..constants import DANGEROUS_PATTERNS, CommandType

def is_command_safe(command: str) -> Tuple[bool, str]:
    """
    Check if a command is safe to execute.
    
    Args:
        command: The command to validate
        
    Returns:
        Tuple[bool, str]: (is_safe, reason)
    """
    if not command or not command.strip():
        return False, "Empty command"
    
    # Check against dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Matches dangerous pattern: {pattern}"
    
    # Check for suspicious command sequences
    suspicious_sequences = ['&&', ';', '|', '`', '$(']
    for seq in suspicious_sequences:
        if seq in command:
            return False, f"Contains suspicious sequence: {seq}"
    
    # Additional safety checks
    if command.startswith('sudo'):
        return False, "Sudo commands are not allowed"
    
    if 'rm ' in command or 'del ' in command:
        # Only allow removing specific files, not patterns like *
        if any(char in command for char in ['*', '?', '{', '}', '..']):
            return False, "Potentially dangerous file pattern"
    
    return True, ""

def validate_command_type(command_type: CommandType, args: List[str]) -> Tuple[bool, str]:
    """
    Validate command arguments based on command type.
    
    Args:
        command_type: Type of the command
        args: List of command arguments
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if command_type == CommandType.NAVIGATION:
        if not args or not args[0]:
            return False, "No target directory specified"
    
    elif command_type == CommandType.DELETE:
        if not args or not args[0]:
            return False, "No target specified for deletion"
        
        # Additional safety for delete operations
        if any(arg.strip() in ('', '/', '/*', '\\', 'C:\\', 'C:/') for arg in args):
            return False, "Attempting to delete root or system directories is not allowed"
    
    elif command_type in (CommandType.MOVE, CommandType.COPY):
        if len(args) < 2:
            return False, f"{command_type.name} requires source and destination"
        
        # Prevent moving/copying to system directories
        dest = args[-1].lower()
        if any(dest.startswith(d) for d in ['/system', '/usr', '/bin', 'c:\\windows']):
            return False, f"{command_type.name} to system directory not allowed"
    
    return True, ""

def sanitize_input(input_str: str) -> str:
    """
    Sanitize user input to prevent command injection.
    
    Args:
        input_str: Input string to sanitize
        
    Returns:
        str: Sanitized string
    """
    if not input_str:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = [';', '&', '|', '`', '$', '>', '<', '!']
    for char in dangerous_chars:
        input_str = input_str.replace(char, '')
    
    # Remove command substitution patterns
    input_str = re.sub(r'\$\([^)]*\)', '', input_str)
    input_str = re.sub(r'`[^`]*`', '', input_str)
    
    return input_str.strip()

def extract_paths(text: str) -> List[str]:
    """
    Extract potential file/directory paths from text.
    
    Args:
        text: Input text
        
    Returns:
        List of potential paths
    """
    paths = []
    
    # Common navigation phrases to remove
    nav_phrases = [
        'go to', 'navigate to', 'change to', 'cd to', 'open directory',
        'show me', 'take me to', 'browse to', 'goto'
    ]
    
    # List command phrases - these should NOT extract paths
    list_phrases = [
        'list files', 'show files', 'list directory', 'show contents',
        'what\'s in', 'what is in'
    ]
    
    # Words that are NOT paths (command keywords)
    excluded_words = {
        'files', 'file', 'directory', 'directories', 'folder', 'folders',
        'list', 'show', 'contents', 'here', 'current', 'this', 'all',
        'ls', 'dir', 'pwd'
    }
    
    text_lower = text.lower().strip()
    
    # If it's a list command, return empty (no path needed)
    if any(phrase in text_lower for phrase in list_phrases):
        return []
    
    # Remove navigation phrases from text
    remaining_text = text
    for phrase in nav_phrases:
        if phrase in text_lower:
            # Split on the phrase and take everything after it
            parts = text_lower.split(phrase, 1)
            if len(parts) > 1:
                # Get the corresponding portion from original text (to preserve case)
                idx = text_lower.index(phrase) + len(phrase)
                remaining_text = text[idx:].strip()
                break
    
    # If we extracted something after a nav phrase, use that as the path
    if remaining_text and remaining_text != text:
        # Clean up quotes and extra spaces
        path = remaining_text.strip().strip('"').strip("'").strip()
        if path and path.lower() not in excluded_words:
            paths.append(path)
            return paths
    
    # Pattern 1: Absolute paths (starts with /, ~, or drive letter)
    abs_path_pattern = r'(?:[a-zA-Z]:|~|/)[\w\\/.-]+'
    abs_matches = re.finditer(abs_path_pattern, text)
    
    for match in abs_matches:
        path = match.group(0)
        if len(path) > 2 and not any(c in path for c in ['*', '?']):
            paths.append(path)
    
    # Pattern 2: Relative paths (word characters with slashes/dots)
    # This will match things like "projects/snlp" or "../folder" or "./file"
    rel_path_pattern = r'(?:\.\.?/)?[\w.-]+(?:/[\w.-]+)+'
    rel_matches = re.finditer(rel_path_pattern, text)
    
    for match in rel_matches:
        path = match.group(0)
        # Skip if it looks like a URL or email
        if not any(c in path for c in ['*', '?', '@']) and '://' not in path:
            paths.append(path)
    
    # Pattern 3: Single directory/file names (as fallback)
    # Only if no other paths were found and it's not an excluded word
    if not paths:
        # Special handling for simple "cd" commands
        if text_lower.startswith('cd '):
            path = text[3:].strip().strip('"').strip("'")
            if path and path.lower() not in excluded_words:
                paths.append(path)
        else:
            # Look for words after navigation keywords
            words = text.split()
            if words:
                # Take the last word as a potential path, but not if it's an excluded word
                last_word = words[-1].strip('"').strip("'")
                if (last_word and 
                    not any(c in last_word for c in ['*', '?', '@']) and
                    last_word.lower() not in excluded_words):
                    paths.append(last_word)
    
    return paths