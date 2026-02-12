"""Command generation module for the hcmd tool."""
import os
import platform
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..constants import CommandType, SYSTEM_DIRECTORIES, OS
from .detector import get_os, get_shell, get_system_directory
from .validator import sanitize_input, extract_paths

class CommandGenerator:
    """Generates terminal commands from natural language input."""
    
    def __init__(self):
        self.os_type = get_os()
        self.shell = get_shell()
        self.platform = platform.system().lower()
        
        # Command templates by OS and command type
        self.templates = {
            'navigation': {
                'windows': 'cd {path}',
                'darwin': 'cd {path}',
                'linux': 'cd {path}'
            },
            'list_files': {
                'windows': 'Get-ChildItem',
                'darwin': 'ls -la',
                'linux': 'ls -la'
            },
            'create_file': {
                'windows': 'New-Item -ItemType File -Path "{path}"',
                'darwin': 'touch "{path}"',
                'linux': 'touch "{path}"'
            },
            'create_dir': {
                'windows': 'New-Item -ItemType Directory -Path "{path}"',
                'darwin': 'mkdir -p "{path}"',
                'linux': 'mkdir -p "{path}"'
            },
            'open': {
                'windows': 'Start-Process "{path}"',
                'darwin': 'open "{path}"',
                'linux': 'xdg-open "{path}"'
            },
            'delete_file': {
                'windows': 'Remove-Item -Path "{path}" -Force',
                'darwin': 'rm -f "{path}"',
                'linux': 'rm -f "{path}"'
            },
            'delete_dir': {
                'windows': 'Remove-Item -Path "{path}" -Recurse -Force',
                'darwin': 'rm -rf "{path}"',
                'linux': 'rm -rf "{path}"'
            },
            'move': {
                'windows': 'Move-Item -Path "{src}" -Destination "{dest}" -Force',
                'darwin': 'mv "{src}" "{dest}"',
                'linux': 'mv "{src}" "{dest}"'
            },
            'copy': {
                'windows': 'Copy-Item -Path "{src}" -Destination "{dest}" -Recurse -Force',
                'darwin': 'cp -r "{src}" "{dest}"',
                'linux': 'cp -r "{src}" "{dest}"'
            },
            'print_working_dir': {
                'windows': 'Get-Location',
                'darwin': 'pwd',
                'linux': 'pwd'
            },
            'docker_list_containers': {
                'windows': 'docker ps -a',
                'darwin': 'docker ps -a',
                'linux': 'docker ps -a'
            },
            'docker_list_images': {
                'windows': 'docker images',
                'darwin': 'docker images',
                'linux': 'docker images'
            },
            'docker_run': {
                'windows': 'docker run -d {image}',
                'darwin': 'docker run -d {image}',
                'linux': 'docker run -d {image}'
            },
            'docker_stop': {
                'windows': 'docker stop {container}',
                'darwin': 'docker stop {container}',
                'linux': 'docker stop {container}'
            },
            'docker_rm': {
                'windows': 'docker rm {container}',
                'darwin': 'docker rm {container}',
                'linux': 'docker rm {container}'
            },
            'docker_rmi': {
                'windows': 'docker rmi {image}',
                'darwin': 'docker rmi {image}',
                'linux': 'docker rmi {image}'
            },
            'docker_logs': {
                'windows': 'docker logs {container}',
                'darwin': 'docker logs {container}',
                'linux': 'docker logs {container}'
            }
        }
        
        # Common aliases and their corresponding system directories
        self.directory_aliases = {
            'home': 'home',
            '~': 'home',
            'desktop': 'desktop',
            'documents': 'documents',
            'downloads': 'downloads',
            'pictures': 'pictures',
            'music': 'music',
            'videos': 'videos',
            'movies': 'videos',
            'pics': 'pictures',
            'docs': 'documents',
            'dl': 'downloads'
        }
    
    def _get_platform_key(self) -> str:
        """Get the platform key for command templates."""
        # FIX: Use self.os_type instead of self.platform
        # Map OS enum to template keys
        if self.os_type == OS.WINDOWS:
            return 'windows'
        elif self.os_type == OS.MACOS:
            return 'darwin'
        elif self.os_type == OS.LINUX:
            return 'linux'
        else:
            # Default to linux for unknown OS
            return 'linux'
    
    def _resolve_path(self, path: str) -> str:
        """Resolve a path, handling special directories and environment variables."""
        if not path:
            return ""
            
        # Handle home directory
        if path == '~' or path.startswith('~/'):
            return os.path.expanduser(path)
            
        # Check if it's a system directory alias
        path_lower = path.lower()
        if path_lower in self.directory_aliases:
            sys_dir = self.directory_aliases[path_lower]
            return get_system_directory(sys_dir, self.os_type)
            
        # Handle Windows environment variables
        if self.os_type == OS.WINDOWS and '%' in path:
            return os.path.expandvars(path)
            
        return path
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path separators for the current OS."""
        if not path:
            return ""
            
        if self.os_type == OS.WINDOWS:
            # Convert forward slashes to backslashes for Windows
            path = path.replace('/', '\\')
            # Remove trailing backslash if present
            if path.endswith('\\'):
                path = path[:-1]
        else:
            # Convert backslashes to forward slashes for Unix-like systems
            path = path.replace('\\', '/')
            # Remove trailing slash if present
            if path.endswith('/') and path != '/':
                path = path[:-1]
                
        return path
    
    def generate_command(self, command_type: CommandType, args: List[str] = None) -> str:
        """
        Generate a command based on the command type and arguments.
        
        Args:
            command_type: Type of command to generate
            args: List of arguments for the command
            
        Returns:
            str: Generated command string
        """
        if args is None:
            args = []
            
        platform_key = self._get_platform_key()
        
        try:
            if command_type == CommandType.NAVIGATION:
                if not args:
                    return ""
                path = self._normalize_path(self._resolve_path(args[0]))
                return f"cd {path}"
                
            elif command_type == CommandType.LIST_FILES:
                path = self._normalize_path(self._resolve_path(args[0])) if args else "."
                return f"ls -la {path}" if path else "ls -la"
                
            elif command_type == CommandType.CREATE:
                if not args:
                    return ""
                path = self._normalize_path(self._resolve_path(args[0]))
                if not path:
                    return ""
                    
                # Check if it's a directory (ends with path separator or has an extension)
                is_dir = path.endswith(os.sep) or not os.path.splitext(path)[1]
                
                if is_dir:
                    return self.templates['create_dir'][platform_key].format(path=path)
                else:
                    return self.templates['create_file'][platform_key].format(path=path)
                    
            elif command_type in (CommandType.MOVE, CommandType.COPY):
                if len(args) < 2:
                    return ""
                    
                src = self._normalize_path(self._resolve_path(args[0]))
                dest = self._normalize_path(self._resolve_path(args[1]))
                
                if command_type == CommandType.MOVE:
                    return self.templates['move'][platform_key].format(src=src, dest=dest)
                else:
                    return self.templates['copy'][platform_key].format(src=src, dest=dest)
                    
            elif command_type == CommandType.DELETE:
                if not args:
                    return ""
                    
                path = self._normalize_path(self._resolve_path(args[0]))
                if not path:
                    return ""
                    
                # Check if it's a directory
                is_dir = os.path.isdir(path) if os.path.exists(path) else path.endswith(os.sep)
                
                if is_dir:
                    return self.templates['delete_dir'][platform_key].format(path=path)
                else:
                    return self.templates['delete_file'][platform_key].format(path=path)
                    
            elif command_type == CommandType.OPEN:
                if not args:
                    return ""
                path = self._normalize_path(self._resolve_path(args[0]))
                return self.templates['open'][platform_key].format(path=path)
                
            elif command_type == CommandType.DOCKER:
                if not args:
                    return ""
                
                subcommand = args[0]
                
                if subcommand == 'list_containers':
                    return self.templates['docker_list_containers'][platform_key]
                elif subcommand == 'list_images':
                    return self.templates['docker_list_images'][platform_key]
                elif subcommand == 'run':
                    if len(args) < 2: return ""
                    return self.templates['docker_run'][platform_key].format(image=args[1])
                elif subcommand == 'stop':
                    if len(args) < 2: return ""
                    return self.templates['docker_stop'][platform_key].format(container=args[1])
                elif subcommand == 'rm':
                    if len(args) < 2: return ""
                    return self.templates['docker_rm'][platform_key].format(container=args[1])
                elif subcommand == 'rmi':
                    if len(args) < 2: return ""
                    return self.templates['docker_rmi'][platform_key].format(image=args[1])
                elif subcommand == 'logs':
                    if len(args) < 2: return ""
                    return self.templates['docker_logs'][platform_key].format(container=args[1])
                else:
                    return ""

            else:
                return ""
                
        except Exception as e:
            print(f"Error generating command: {e}", file=sys.stderr)
            return ""
    
    def interpret_natural_language(self, text: str) -> Tuple[CommandType, List[str]]:
        """
        Interpret natural language input and determine the command type and arguments.
        
        Args:
            text: Natural language input
            
        Returns:
            Tuple[CommandType, List[str]]: Command type and list of arguments
        """
        if not text:
            return CommandType.UNKNOWN, []
            
        text = text.lower().strip()
        
        # Check for navigation commands
        nav_phrases = [
            'go to', 'navigate to', 'change to', 'cd to', 'open directory',
            'show me', 'take me to', 'browse to'
        ]
        
        list_phrases = [
            'list files', 'show files', 'list directory', 'ls', 'dir',
            'what\'s in', 'what is in', 'show contents of'
        ]
        
        create_phrases = [
            'create file', 'make file', 'new file', 'touch',
            'create directory', 'make directory', 'new directory', 'mkdir'
        ]
        
        delete_phrases = [
            'delete', 'remove', 'rm', 'del', 'erase', 'trash'
        ]
        
        move_phrases = [
            'move', 'mv', 'relocate', 'transfer'
        ]
        
        copy_phrases = [
            'copy', 'cp', 'duplicate', 'clone'
        ]
        
        open_phrases = [
            'open', 'launch', 'start', 'run', 'execute'
        ]
        
        # Extract potential paths from the text
        paths = extract_paths(text)
        
        # Check for Docker (High priority)
        if 'docker' in text or 'container' in text or ('image' in text and not any(p in text for p in ['jpg', 'png', 'gif'])):
            words = text.split()
            
            if 'list' in text or 'show' in text:
                if 'image' in text:
                    return CommandType.DOCKER, ['list_images']
                return CommandType.DOCKER, ['list_containers']
                
            if 'run' in text or 'start' in text:
                # heuristic: use word after 'run' or 'start' or last word
                target = words[-1]
                keyword = 'run' if 'run' in words else 'start'
                
                if keyword in words:
                    idx = words.index(keyword)
                    if idx + 1 < len(words):
                        target = words[idx+1]
                        # Skip keywords like 'docker' or 'container'
                        if target in ['docker', 'container'] and idx + 2 < len(words):
                            target = words[idx+2]
                            
                return CommandType.DOCKER, ['run', target]
                
            if 'stop' in text:
                return CommandType.DOCKER, ['stop', words[-1]]
                
            if 'delete' in text or 'remove' in text or 'rm' in text:
                if 'image' in text:
                    return CommandType.DOCKER, ['rmi', words[-1]]
                return CommandType.DOCKER, ['rm', words[-1]]

            if 'log' in text:
                return CommandType.DOCKER, ['logs', words[-1]]
        
        # Check for navigation
        if any(phrase in text for phrase in nav_phrases):
            return CommandType.NAVIGATION, paths[:1] if paths else [text.split()[-1]]
            
        # Check for list files
        if any(phrase in text for phrase in list_phrases):
            return CommandType.LIST_FILES, paths[:1] if paths else []
            
        # Check for create
        if any(phrase in text for phrase in create_phrases):
            return CommandType.CREATE, paths[:1] if paths else [text.split()[-1]]
            
        # Check for delete
        if any(phrase in text for phrase in delete_phrases):
            return CommandType.DELETE, paths[:1] if paths else []
            
        # Check for move
        if any(phrase in text for phrase in move_phrases):
            return CommandType.MOVE, paths[:2] if len(paths) >= 2 else []
            
        # Check for copy
        if any(phrase in text for phrase in copy_phrases):
            return CommandType.COPY, paths[:2] if len(paths) >= 2 else []
            
        # Check for open
        if any(phrase in text for phrase in open_phrases):
            return CommandType.OPEN, paths[:1] if paths else []
            
        # Default to navigation if a path is detected
        if paths:
            return CommandType.NAVIGATION, paths[:1]
            


        return CommandType.UNKNOWN, []