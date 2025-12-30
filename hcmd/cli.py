#!/usr/bin/env python3
"""
Human to Command (hcmd) - Convert natural language to terminal commands
"""
import argparse
import json
import os
import sys
from typing import List, Optional

from . import __version__
from .constants import CommandType, OS
from .core.detector import get_os, get_shell
from .core.executor import CommandExecutor
from .core.generator import CommandGenerator
from .core.validator import is_command_safe, validate_command_type

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# System prompt for LLM translation
SYSTEM_PROMPT = """You are a terminal command translator.
Convert human language into valid terminal commands.
Follow OS-specific syntax.
Output only the command.
If unsafe: ERROR: Unsafe command
If ambiguous: ERROR: Ambiguous command

Examples:
Input: go to downloads
Output: cd ~/Downloads

Input: list files in current directory
Output: ls -la

Input: create a file named test.txt
Output: touch test.txt

Input: delete all files
Output: ERROR: Ambiguous command

Input: format c drive
Output: ERROR: Unsafe command
"""

def print_help():
    """Print help information."""
    print(f"{Colors.HEADER}{Colors.BOLD}hcmd - Human to Command{Colors.ENDC}")
    print(f"Version: {__version__}")
    print("\nConvert natural language to terminal commands.")
    print("\nExamples:")
    print(f"  {Colors.OKCYAN}hcmd go to downloads{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}hcmd list files in current directory{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}hcmd create a file named test.txt{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}hcmd 'delete file.txt' --dry-run{Colors.ENDC}")
    print("\nOptions:")
    print(f"  {Colors.OKGREEN}--dry-run{Colors.ENDC}    Show the command without executing it")
    print(f"  {Colors.OKGREEN}--json{Colors.ENDC}       Output in JSON format")
    print(f"  {Colors.OKGREEN}--version{Colors.ENDC}    Show version and exit")
    print(f"  {Colors.OKGREEN}--help{Colors.ENDC}       Show this help message and exit")

def parse_args(args: List[str] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Convert natural language to terminal commands',
        add_help=False
    )
    
    # Positional argument for the command
    parser.add_argument(
        'command',
        nargs='*',
        help='Natural language command to convert'
    )
    
    # Optional arguments
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show the command without executing it'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )
    parser.add_argument(
        '--version',
        action='store_true',
        help='Show version and exit'
    )
    parser.add_argument(
        '--help',
        action='store_true',
        help='Show this help message and exit'
    )
    
    return parser.parse_args(args)

def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the hcmd CLI."""
    # Parse command line arguments
    parsed_args = parse_args(args)
    
    # Handle help and version flags
    if parsed_args.help or not parsed_args.command:
        print_help()
        return 0
    
    if parsed_args.version:
        print(f"hcmd {__version__}")
        return 0
    
    # Join the command parts
    command_text = ' '.join(parsed_args.command)
    
    # Initialize components
    generator = CommandGenerator()
    executor = CommandExecutor(dry_run=parsed_args.dry_run)
    
    # Interpret the natural language command
    command_type, command_args = generator.interpret_natural_language(command_text)
    
    # Generate the command
    if command_type == CommandType.UNKNOWN:
        # If we couldn't determine the command type, try to generate a command directly
        # This handles cases where the input is already a command
        generated_command = command_text
        command_type = None
    else:
        # Generate the command based on the interpreted type and arguments
        generated_command = generator.generate_command(command_type, command_args)
    
    # Validate the generated command
    is_safe, safety_reason = is_command_safe(generated_command)
    
    # Prepare the result
    result = {
        'input': command_text,
        'command': generated_command,
        'safe': is_safe,
        'dry_run': parsed_args.dry_run,
        'executed': False,
        'success': False,
        'output': None,
        'error': None
    }
    
    # Check if the command is safe to execute
    if not is_safe:
        result['error'] = f"ERROR: Unsafe command: {safety_reason}"
    elif not generated_command:
        result['error'] = "ERROR: Could not generate a command for the input"
    else:
        # Execute the command if it's safe and not a dry run
        if not parsed_args.dry_run:
            success, output = executor.execute(generated_command)
            result['executed'] = True
            result['success'] = success
            
            if success:
                result['output'] = output
            else:
                result['error'] = output
    
    # Output the result
    if parsed_args.json:
        # Output as JSON
        print(json.dumps(result, indent=2))
    else:
        # Output as human-readable text
        if 'error' in result and result['error']:
            print(f"{Colors.FAIL}{result['error']}{Colors.ENDC}", file=sys.stderr)
            return 1
        
        if generated_command:
            # Check if it's a cd command
            is_cd_command = generated_command.lower().strip().startswith('cd ')
            
            if is_cd_command:
                # For cd commands, just print the command once (no color)
                # The output from executor.execute() already contains the cd command
                if result.get('output'):
                    print(result['output'])
                else:
                    print(generated_command)
            else:
                # For non-cd commands, print with color
                print(f"{Colors.OKGREEN}{generated_command}{Colors.ENDC}")
                
                if parsed_args.dry_run:
                    print(f"{Colors.WARNING}Dry run: Command not executed{Colors.ENDC}")
                elif result.get('executed') and result.get('output'):
                    print("\n" + result['output'])
    
    return 0 if (result.get('success') or parsed_args.dry_run) else 1

def run():
    """Entry point for the console script."""
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.FAIL}Error: {str(e)}{Colors.ENDC}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    run()