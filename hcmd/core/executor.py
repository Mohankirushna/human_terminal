import subprocess
import os
import platform

class CommandExecutor:

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.is_windows = platform.system() == "Windows"

    def execute(self, command: str):
        if self.dry_run:
            return True, f"[DRY RUN] {command}"

        # cd must be printed for parent shell
        if command.startswith("cd "):
            print(command)
            return True, command

        try:
            if self.is_windows:
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", command],
                    text=True,
                    capture_output=True
                )
            else:
                # Linux / macOS
                result = subprocess.run(
                    command,
                    shell=True,
                    text=True,
                    capture_output=True,
                    cwd=os.getcwd()
                )

            if result.returncode != 0:
                return False, result.stderr.strip()

            return True, result.stdout.strip()

        except Exception as e:
            return False, str(e)
