"""Command execution module for the hcmd tool."""
import os
import platform
import shlex
import subprocess
import sys
from typing import Optional, Tuple

from ..constants import OS
from .detector import get_os, get_shell
from .validator import is_command_safe

class CommandExecutor:
    """Handles execution of terminal commands with safety checks."""
    
    def __init__(self, dry_run: bool = False, os_type: Optional[OS] = None):
        """
        Initialize the command executor.
        
        Args:
            dry_run: If True, only print commands without executing them
            os_type: The operating system type. If not provided, it will be detected.
        """
        self.os_type = os_type if os_type is not None else get_os()
        print(f"DEBUG: Executor initialized with OS type: {self.os_type}", file=sys.stderr)  # Print to stderr
        self.dry_run = dry_run
        self.platform = platform.system().lower()
    
    def _get_shell_command(self, command: str) -> Tuple[str, list]:
        """
        Get the appropriate shell command and arguments for the current platform.
        
        Args:
            command: The command to execute
            
        Returns:
            Tuple of (shell_executable, shell_args)
        """
        if self.os_type == OS.WINDOWS:
            shell = get_shell()
            if 'powershell' in shell.lower():
                return shell, ['-NoProfile', '-NonInteractive', '-Command', command]
            else:
                return shell, ['/c', command]
        else:
            shell = os.environ.get('SHELL', '/bin/zsh' if self.os_type == OS.MACOS else '/bin/bash')
            
            # Handle specific commands
            command_lower = command.lower().strip()
            
            # Handle list files command
            if 'list' in command_lower and ('file' in command_lower or 'directory' in command_lower):
                path = '.'
                if ' in ' in command_lower:
                    dir_part = command.split(' in ')[-1].strip()
                    if dir_part:
                        path = dir_part
                return shell, ['-c', f'ls -la {path}']
                
            # Handle cd command
            if command_lower.startswith('cd '):
                return shell, ['-c', command]
                
            # Default case - pass the command as is
            return shell, ['-c', command]
    
    def execute(self, command: str, cwd: Optional[str] = None) -> Tuple[bool, str]:
        """
        Execute a shell command with safety checks.

        IMPORTANT:
        - `cd` commands are NOT executed here.
        - They are returned so the parent shell can eval them.
        """
        if not command or not command.strip():
            return False, "ERROR: Empty command"

        command = command.strip()
        command_lower = command.lower()

        # Handle list files command
        if 'list' in command_lower and ('file' in command_lower or 'directory' in command_lower):
            # If the command is just 'list files', use current directory
            if command_lower.strip() in ['list files', 'list file', 'list directory', 'list files in .', 'list file in .', 'list directory in .']:
                command = 'ls -la .'
            # If the command has a specific directory
            elif ' in ' in command_lower:
                dir_part = command.split(' in ')[-1].strip()
                if dir_part and dir_part.lower() not in ['here', 'current directory']:
                    command = f'ls -la {dir_part}'
                else:
                    command = 'ls -la .'
            else:
                command = 'ls -la .'
        # Handle cd commands specially - return them for the parent shell to execute
        elif command_lower.startswith('cd '):
            # Safety check still applies
            is_safe, reason = is_command_safe(command)
            if not is_safe:
                return False, f"ERROR: Unsafe command: {reason}"

            # Return cd command as-is for parent shell
            return True, command

        # Safety check for all other commands
        is_safe, reason = is_command_safe(command)
        if not is_safe:
            return False, f"ERROR: Unsafe command: {reason}"

        try:
            shell, shell_args = self._get_shell_command(command)

            if self.dry_run:
                return True, f"[DRY RUN] {command}"

            result = subprocess.run(
                [shell] + shell_args,
                cwd=cwd,
                capture_output=True,
                text=True,
                shell=False
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if result.returncode != 0:
                return False, stderr or stdout

            return True, stdout

        except Exception as e:
            return False, f"Error executing command: {str(e)}"
    
    def execute_interactive(self, command: str, cwd: Optional[str] = None) -> int:
        """
        Execute a command in interactive mode (with user input and output).
        
        Args:
            command: The command to execute
            cwd: Working directory for the command
            
        Returns:
            The exit code of the command (0 for success, 1 for error)
        """
        if not command or not command.strip():
            print("ERROR: Empty command", file=sys.stderr)
            return 1

        command = command.strip()
        command_lower = command.lower()

        # Handle list files command
        if 'list' in command_lower and ('file' in command_lower or 'directory' in command_lower):
            # If the command is just 'list files', use current directory
            if command_lower.strip() in ['list files', 'list file', 'list directory', 'list files in .', 'list file in .', 'list directory in .']:
                command = 'ls -la .'
            # If the command has a specific directory
            elif ' in ' in command_lower:
                dir_part = command.split(' in ')[-1].strip()
                if dir_part and dir_part.lower() not in ['here', 'current directory']:
                    command = f'ls -la {dir_part}'
                else:
                    command = 'ls -la .'
            else:
                command = 'ls -la .'
        # Handle cd commands specially - print them ONCE for the parent shell to execute
        elif command_lower.startswith('cd '):
            # Safety check still applies
            is_safe, reason = is_command_safe(command)
            if not is_safe:
                print(f"ERROR: Unsafe command: {reason}", file=sys.stderr)
                return 1

            # Print cd command ONCE for parent shell to execute
            print(command)
            return 0
        
        # Check if command is safe to execute
        is_safe, reason = is_command_safe(command)
        if not is_safe:
            print(f"ERROR: Unsafe command: {reason}", file=sys.stderr)
            return 1
        
        # Print the command in dry-run mode
        if self.dry_run:
            print(f"[DRY RUN] Would execute: {command}")
            return 0
        
        try:
            # For list commands, we want to capture and print the output
            if command.startswith('ls'):
                result = subprocess.run(
                    command,
                    cwd=cwd or os.getcwd(),
                    shell=True,
                    text=True,
                    capture_output=True
                )
                if result.returncode != 0:
                    print(result.stderr, file=sys.stderr)
                    return 1
                print(result.stdout)
                return 0
            
            # For other commands, execute interactively
            shell, shell_args = self._get_shell_command(command)
            process = subprocess.Popen(
                [shell] + shell_args,
                cwd=cwd or os.getcwd(),
                shell=False
            )
            
            return process.wait()
            
        except Exception as e:
            print(f"Error executing command: {str(e)}", file=sys.stderr)
            return 1