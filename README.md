# hcmd - Human to Command

A command-line tool that converts natural language instructions into terminal commands.

## Features

- Converts natural language to terminal commands
- Cross-platform support (macOS, Linux, Windows)
- Safety checks to prevent dangerous commands
- Dry-run mode to preview commands before execution
- JSON output option for scripting

## Installation

### Using pip

```bash
pip install -e .
```

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/hcmd.git
   cd hcmd
   ```

2. Install the package:
   ```bash
   python setup.py install
   ```

## Usage

### Basic Usage

```bash
hcmd "go to downloads folder"
```

### Examples

```bash
# Navigate to directories
hcmd "go to documents"

# List files
hcmd "list files in current directory"

# Create files and directories
hcmd "create a file named test.txt"
hcmd "create a directory named my_folder"

# Move and copy files
hcmd "move file.txt to documents"
hcmd "copy image.jpg to pictures"

# Delete files (with safety checks)
hcmd "delete old_file.txt"

# Dry run (show command without executing)
hcmd "delete file.txt" --dry-run

# JSON output
hcmd "list files" --json
```

### Shell Integration

For a more natural experience, you can create an alias in your shell configuration:

#### Bash/Zsh (macOS/Linux)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias hcmd='hcmd "$@"'
```

#### PowerShell (Windows)

Add to your PowerShell profile (`$PROFILE`):

```powershell
function hcmd { python -m hcmd $args }
```

## Safety Features

- Blocks dangerous commands (e.g., `rm -rf /`, `format C:`)
- Validates file operations
- Prevents command injection
- Dry-run mode to preview commands

## Development

### Setup

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

### Running Tests

```bash
pytest
```

### Code Style

```bash
black .
isort .
flake8
mypy .
```

## License

MIT

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Acknowledgments

- Inspired by the need for more intuitive command-line interfaces
- Built with Python's standard library for maximum compatibility
