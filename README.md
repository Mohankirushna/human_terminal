# hcmd - Human to Command

A next-generation command-line tool that converts natural language instructions into terminal commands using advanced machine learning models. Write commands in plain English and let hcmd intelligently translate them to native shell syntax across Windows, macOS, and Linux.

## Core Features

### AI-Powered Natural Language Processing
- **Intent Recognition**: Uses fine-tuned transformer models to understand command intentions (navigation, file operations, git commands, system info, and more)
- **Span Extraction**: Intelligent extraction of command parameters using specialized NLP models:
  - Directory/navigation paths
  - Source and destination files
  - File/directory names and rename targets
  - Git repositories, branches, and files to stage
  - Process targets and command arguments
- **Confidence Scoring**: Built-in confidence thresholds to ensure accurate command interpretation
- **Pattern Matching**: Regex-based pattern detection for complex multi-step operations

### Cross-Platform Command Generation
- **Windows (PowerShell)**: Generates native PowerShell commands
- **macOS/Linux (Bash/Zsh)**: Generates POSIX-compliant shell commands
- Automatic path normalization across operating systems
- Smart handling of special directories (Downloads, Documents, Desktop)

### File System Operations
- Navigate to directories and manage paths
- List, create, delete, copy, move, and rename files
- Create and delete directories recursively
- Read file contents
- Pattern-based bulk operations on multiple files

### Git Integration
- Repository status and branch management
- Clone, pull, and push operations
- Staging files for commits
- Branch checkout and management
- Repository-aware safety checks

### System Information & Process Management
- Display system information
- List and monitor running processes
- Terminate processes by name or ID
- Network information and diagnostics

### Safety & Validation
- **Protected Path Detection**: Prevents operations on critical system directories
- **Confirmation Prompts**: Multi-step commands require explicit user confirmation
- **Command Validation**: Validates all commands before execution
- **Git Repository Awareness**: Detects non-repository operations and warns users
- **Destructive Operation Warnings**: Special alerts for delete operations

### Intelligent Disambiguation
- **Ambiguity Detection**: Identifies ambiguous instructions and requests clarification
- **Option Selection**: Presents multiple interpretations when command intent is unclear
- **Context Awareness**: Uses system context and working directory to disambiguate

### Command Memory & Execution
- **Command Caching**: Remembers previously executed commands
- **Multi-Step Execution**: Plans and executes complex multi-step operations
- **Atomic Operations**: Ensures related operations complete together
- **Real-time Feedback**: Displays command output and error messages

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

## 📦 Installation (Portable)

### Windows

```bash
setup_windows.bat
```

### Linux / macOS

```bash
chmod +x setup_linux.sh
./setup_linux.sh
```

### ▶ Run

```bash
python hcmd/main.py
```

### 🌍 Make It Global (Optional)

#### Windows

Add project folder to PATH

Restart terminal

Run anywhere:

```bash
hcmd
```

#### Linux/macOS

```bash
mv hcmd ~/.local/bin/
chmod +x ~/.local/bin/hcmd
```

## Usage

### Basic Command Syntax

```bash
hcmd "your natural language command"
```

### File Operations Examples

```bash
# Navigate to common directories
hcmd "go to documents"
hcmd "change to downloads folder"
hcmd "navigate to desktop"

# List and explore
hcmd "list files in current directory"
hcmd "show all files"
hcmd "list everything here"

# Create files and directories
hcmd "create a file named test.txt"
hcmd "create a directory named my_project"
hcmd "make a new folder called data"

# Move, copy, and delete
hcmd "move file.txt to documents"
hcmd "copy image.jpg to pictures"
hcmd "rename report.pdf to annual_report.pdf"
hcmd "delete old_backup.zip"

# Read file contents
hcmd "read config.json"
hcmd "show me the contents of README.md"
```

### Git Operations

```bash
# Repository management
hcmd "check git status"
hcmd "show current branch"
hcmd "show git log"

# Cloning and pulling
hcmd "clone repository from https://github.com/user/repo.git"
hcmd "pull latest changes"
hcmd "push to remote"

# Staging and branching
hcmd "stage file.py for commit"
hcmd "add changes.txt to git"
hcmd "checkout main branch"
hcmd "create and switch to feature branch"
```

### System Operations

```bash
# System information
hcmd "show system information"
hcmd "get system info"
hcmd "display network configuration"

# Process management
hcmd "list all running processes"
hcmd "show active processes"
hcmd "kill process by name firefox"
hcmd "terminate process with PID 1234"
```

### Multi-Step Operations

hcmd intelligently handles complex operations:

```bash
# Multi-step file operations
hcmd "move all .txt files from documents to archive"
hcmd "copy project folder to backup and compress it"
```

The tool will:
1. Display the planned steps
2. Request confirmation before execution
3. Execute each step in sequence
4. Report any errors or issues

## Shell Integration

For seamless natural language command execution, create aliases in your shell:

### Bash/Zsh (macOS/Linux)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias hcmd='hcmd "$@"'
```

### PowerShell (Windows)

Add to your PowerShell profile (`$PROFILE`):

```powershell
function hcmd { python -m hcmd $args }
```

Then reload your shell:

```bash
# Bash/Zsh
source ~/.bashrc  # or ~/.zshrc

# PowerShell
& $PROFILE
```

## Advanced Features

### Confidence Thresholds
The tool uses configurable confidence thresholds for both intent recognition (30%) and span extraction (25%) to ensure accurate interpretations. Low-confidence commands are flagged for review.

### Context Resolution
- **Current Working Directory**: Commands respect your current location
- **System Context**: OS-aware command generation
- **Git Context**: Detects if you're in a git repository
- **Path Normalization**: Handles relative and absolute paths automatically

### Pattern Execution
Batch operations using pattern matching:
- Glob patterns for file selection
- Recursive directory operations
- Wildcard-based file operations

## Architecture

The system uses a modular pipeline:

1. **Intent Recognition**: Transformer-based sequence classification to identify command type
2. **Span Extraction**: Question-answering models extract specific parameters from natural language
3. **Command Building**: Template-based command generation from extracted intents and parameters
4. **Safety Validation**: Pre-execution checks for dangerous operations
5. **Execution**: OS-specific command execution with error handling

## Safety & Guardrails

hcmd includes multiple safety layers:

- **Protected Paths**: System directories are protected from accidental deletion
- **Destructive Operation Warnings**: Delete commands always require confirmation
- **Git Safety**: Warns when running git commands outside a repository
- **Command Injection Prevention**: Proper escaping and validation of all user input
- **Interactive Confirmation**: Multi-step operations require explicit user approval

## Development

### Setup Development Environment

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

### Model Training

The project includes scripts for training custom intent and span extraction models:

- `dataset_creation/dataset_creation.py` - Generate training datasets
- `model_training/model_training.py` - Train intent recognition models
- `span_extraction/` - Train specialized span extraction models for different command types

### Testing

```bash
pytest
```

### Code Quality

```bash
black .        # Code formatting
isort .        # Import sorting
flake8         # Linting
mypy .         # Type checking
```

## Supported Intents (Complete Reference)

### Navigation & Directory Operations
- **NAVIGATION**: Change current working directory
  - Natural language: "go to documents", "navigate to desktop", "change directory to folder"
  - Windows: `cd "path"`
  - Unix: `cd "path"`

- **PWD**: Print working directory
  - Natural language: "show current directory", "where am i", "current path"
  - Windows: `Get-Location`
  - Unix: `pwd`

### File Operations
- **LIST_FILES**: List files in directory
  - Natural language: "list files", "show all files", "ls"
  - Windows: `Get-ChildItem`
  - Unix: `ls -la`

- **CREATE_FILE**: Create a new file
  - Natural language: "create file test.txt", "make a new file"
  - Windows: `New-Item -ItemType File "filename"`
  - Unix: `touch "filename"`

- **READ_FILE**: Read file contents
  - Natural language: "read config.json", "show contents of file"
  - Requires file path extraction

- **DELETE_FILE**: Delete a file (safety warning required)
  - Natural language: "delete old_file.txt", "remove backup.zip"
  - Windows: `del "path"`
  - Unix: `rm "path"`

- **COPY_FILE**: Copy file to destination
  - Natural language: "copy image.jpg to pictures", "copy file.txt to documents"
  - Windows: `Copy-Item "src" "dst"`
  - Unix: `cp "src" "dst"`

- **MOVE_FILE**: Move file to destination
  - Natural language: "move file.txt to documents", "relocate backup to archive"
  - Windows: `Move-Item "src" "dst"`
  - Unix: `mv "src" "dst"`

- **RENAME_FILE**: Rename a file
  - Natural language: "rename report.pdf to annual_report.pdf", "change filename"
  - Windows: `Rename-Item "src" "dst"`
  - Unix: `mv "src" "dst"`

### Directory Operations
- **CREATE_DIR**: Create a new directory
  - Natural language: "create directory my_project", "make folder data"
  - Windows: `New-Item -ItemType Directory "dirname"`
  - Unix: `mkdir "dirname"`

- **DELETE_DIR**: Delete directory recursively
  - Natural language: "delete folder old_project", "remove directory tree"
  - Windows: `Remove-Item -Recurse -Force "path"`
  - Unix: `rm -r "path"`

### System Information
- **SYSTEM_INFO**: Display system information
  - Natural language: "show system info", "display computer specs"
  - Windows: `systeminfo`
  - Unix: `uname -a`

- **PROCESS_LIST**: List running processes
  - Natural language: "list processes", "show running programs", "ps aux"
  - Windows: `tasklist`
  - Unix: `ps aux`

- **NETWORK_INFO**: Display network configuration
  - Natural language: "show network info", "display ip config"
  - Windows: `ipconfig`
  - Unix: `ifconfig`

- **PROCESS_KILL**: Terminate a process
  - Natural language: "kill process firefox", "terminate process by PID 1234"
  - Windows: `taskkill /PID {pid} /F` or `taskkill /IM {name}.exe /F`
  - Unix: `kill {pid}` or `killall {name}`

### Git Operations
- **GIT_STATUS**: Show repository status
  - Natural language: "check git status", "show repo status"
  - Command: `git status`

- **GIT_BRANCH**: List branches
  - Natural language: "show branches", "list git branches"
  - Command: `git branch`

- **GIT_LOG**: Show commit history
  - Natural language: "show git log", "display commit history"
  - Command: `git log --oneline --decorate --graph`

- **GIT_ADD**: Stage file for commit
  - Natural language: "stage file.py", "add changes.txt to git"
  - Command: `git add "path"`
  - Requires file path extraction

- **GIT_CHECKOUT**: Switch branch
  - Natural language: "checkout main branch", "switch to feature branch"
  - Command: `git checkout "branch"`
  - Requires branch name extraction

- **GIT_CLONE**: Clone repository
  - Natural language: "clone repository from https://github.com/user/repo.git"
  - Command: `git clone "repo_url"`
  - Requires repository URL extraction

- **GIT_PULL**: Pull latest changes
  - Natural language: "pull latest changes", "fetch and merge"
  - Command: `git pull`

- **GIT_PUSH**: Push changes to remote
  - Natural language: "push to remote", "upload changes"
  - Command: `git push`

- **GIT_RESET**: Reset repository state
  - Natural language: "reset changes", "reset to commit"
  - Command: `git reset`

- **GIT_STASH**: Stash changes
  - Natural language: "stash changes", "save work in progress"
  - Command: `git stash`

## Intent Processing Pipeline

For each intent, the system:
1. **Extracts parameters** using specialized span extraction models
2. **Validates context** (e.g., git operations check if in a repository)
3. **Normalizes paths** across platforms
4. **Generates commands** appropriate to the OS
5. **Validates safety** before execution
6. **Displays confirmation** for destructive operations
7. **Executes** the command and reports results

## Performance

- **GPU Support**: Automatically uses CUDA when available for faster inference
- **CPU Fallback**: Works efficiently on CPU-only systems
- **Model Size**: Optimized transformer models for quick inference
- **Memory**: Efficient model loading with proper resource cleanup

## Limitations & Future Work

- Currently focused on command-line operations
- Supports most common system administration and development tasks
- Future versions will expand to graphical operations and workflow automation

## Contributing

Contributions are welcome! Areas for contribution:
- New intent types and model training
- Additional span extraction models for new command types
- Cross-platform compatibility improvements
- Safety rule enhancements
- Command testing and validation

Please open an issue or submit a pull request to contribute.

## Acknowledgments

- Built using Hugging Face Transformers and PyTorch
- Inspired by the need for more intuitive command-line interfaces
- Leverages modern NLP advances for practical CLI enhancement
