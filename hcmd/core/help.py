def show_help(topic: str | None = None):
    if not topic:
        print("""
HCMD — Natural Language Command Interface

You can control your system using natural language.

Examples:
  hcmd "create a.txt"
  hcmd "move a.txt to docs"
  hcmd "delete this"
  hcmd "create a folder and move files into it"
  hcmd "git add and commit"

Core features:
• File & folder operations
• Multi-step commands using "and"
• Pronoun resolution (this / that / it)
• Dry-run mode (--dry-run)
• Rollback support (rollback)
• Git-aware commands
• Offline-first execution

Try:
  hcmd help files
  hcmd help pronouns
  hcmd help git
  hcmd help explain
""")
        return

    topic = topic.lower()

    if topic == "files":
        print("""
File Operations:
• create a.txt
• delete a.txt
• move a.txt to docs
• copy a.txt to backup
• rename a.txt to b.txt
• delete this

Supports:
• folders
• wildcards (*.txt)
• pronouns (this / that)
""")

    elif topic == "pronouns":
        print("""
Pronouns:
• this / that / it → most recent file or folder
• there → last directory

Example:
  hcmd "move a.txt to docs"
  hcmd "delete this"
""")

    elif topic == "git":
        print("""
Git Commands:
• git status
• git add file.txt
• commit
• checkout branch
• clone <repo>

Git follow-ups work without repeating 'git'.
""")

    elif topic == "explain":
        print("""
Explainability:
Use --explain to understand what HCMD thinks.

Example:
  hcmd "delete this" --explain

Shows:
• detected intent
• resolved pronouns
• execution plan
• safety checks
""")

    else:
        print(f"No help available for '{topic}'")
