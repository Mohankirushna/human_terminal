import json
import os

MEMORY_FILE = os.path.expanduser("~/.hcmd_memory.json")


class Memory:
    def __init__(self):
        self.last_path = None
        self.last_src = None
        self.last_dst = None
        self.last_git_intent = None

        # 🔁 Rollback history (stack of commands)
        self.history = []

        # 🧠 Pronoun resolution history (ordered)
        self.recent_objects = []   # newest at end

        self._load()

    # ---------------------------
    # Persistence
    # ---------------------------
    def _load(self):
        if not os.path.exists(MEMORY_FILE):
            return

        try:
            with open(MEMORY_FILE, "r") as f:
                data = json.load(f)

            self.last_path = data.get("last_path")
            self.last_src = data.get("last_src")
            self.last_dst = data.get("last_dst")
            self.last_git_intent = data.get("last_git_intent")

            self.history = data.get("history", [])
            if not isinstance(self.history, list):
                self.history = []

            self.recent_objects = data.get("recent_objects", [])
            if not isinstance(self.recent_objects, list):
                self.recent_objects = []

        except Exception:
            # Corrupt memory must never crash hcmd
            self.history = []
            self.recent_objects = []

    def save(self):
        with open(MEMORY_FILE, "w") as f:
            json.dump(
                {
                    "last_path": self.last_path,
                    "last_src": self.last_src,
                    "last_dst": self.last_dst,
                    "last_git_intent": self.last_git_intent,
                    "history": self.history,

                    # 🧠 Pronoun memory
                    "recent_objects": self.recent_objects,
                },
                f,
                indent=2,
            )

    # ---------------------------
    # Pronoun helpers
    # ---------------------------
    def push_object(self, obj: str | None):
        if not obj:
            return

        self.recent_objects.append(obj)

        # Keep only last 5 references
        self.recent_objects = self.recent_objects[-5:]

        # Backward compatibility
        self.last_path = obj


memory = Memory()
