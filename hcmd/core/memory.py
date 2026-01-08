import json
import os

MEMORY_FILE = os.path.expanduser("~/.hcmd_memory.json")

class Memory:
    def __init__(self):
        self.last_path = None
        self.last_src = None
        self.last_dst = None
        self.last_git_intent = None
        self._load()

    def _load(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r") as f:
                    data = json.load(f)
                    self.__dict__.update(data)
            except Exception:
                pass

    def save(self):
        with open(MEMORY_FILE, "w") as f:
            json.dump({
                "last_path": self.last_path,
                "last_src": self.last_src,
                "last_dst": self.last_dst,
                "last_git_intent": self.last_git_intent
            }, f)

memory = Memory()
