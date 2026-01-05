import csv
import random
import string

# -------------------------
# Random name generators
# -------------------------

FILE_EXTENSIONS = ["py", "txt", "csv", "json", "md", "log", "pdf", "yaml"]

def rand_word(min_len=3, max_len=8):
    return "".join(random.choices(string.ascii_lowercase, k=random.randint(min_len, max_len)))

def rand_file():
    base = rand_word()
    if random.random() < 0.5:
        base += f"_{random.randint(1,99)}"
    return f"{base}.{random.choice(FILE_EXTENSIONS)}"

def rand_dir():
    base = rand_word()
    if random.random() < 0.4:
        base += "_" + random.choice(["src", "data", "logs", "backup"])
    if random.random() < 0.3:
        base += str(random.randint(1,5))
    return base

# -------------------------
# Intents (expanded)
# -------------------------

INTENTS = {
    "NAVIGATION": {
        "count": 450,
        "templates": [
            "go to {dir}",
            "navigate to {dir}",
            "open {dir}",
            "enter {dir}",
            "switch to {dir}",
            "cd {dir}",
            "take me to {dir}",
            "move into {dir}",
        ],
    },
    "LIST_FILES": {
        "count": 400,
        "templates": [
            "list files",
            "show files",
            "list all files",
            "ls",
            "ls -l",
            "what files are here",
            "show directory contents",
        ],
    },
    "PWD": {
        "count": 350,
        "templates": [
            "where am i",
            "current directory",
            "pwd",
            "print working directory",
            "show current path",
        ],
    },
    "CREATE_FILE": {
        "count": 450,
        "templates": [
            "create file {file}",
            "make a file named {file}",
            "new file {file}",
            "touch {file}",
            "generate file {file}",
        ],
    },
    "CREATE_DIR": {
        "count": 350,
        "templates": [
            "create directory {dir}",
            "make folder {dir}",
            "new directory {dir}",
            "mkdir {dir}",
        ],
    },
    "DELETE_FILE": {
        "count": 450,
        "templates": [
            "delete {file}",
            "remove {file}",
            "erase {file}",
            "rm {file}",
        ],
    },
    "COPY_FILE": {
        "count": 350,
        "templates": [
            "copy {src} to {dst}",
            "duplicate {src} into {dst}",
            "cp {src} {dst}",
        ],
    },
    "MOVE_FILE": {
        "count": 350,
        "templates": [
            "move {src} to {dst}",
            "relocate {src} into {dst}",
            "mv {src} {dst}",
        ],
    },
    "RENAME_FILE": {
        "count": 300,
        "templates": [
            "rename {src} to {dst}",
            "change filename from {src} to {dst}",
        ],
    },
    "GIT_STATUS": {
        "count": 300,
        "templates": [
            "git status",
            "show git status",
            "any git changes",
            "repository status",
        ],
    },
    "GIT_BRANCH": {
        "count": 300,
        "templates": [
            "git branch",
            "current git branch",
            "which branch am i on",
        ],
    },
    "INVALID": {
        "count": 400,
        "templates": [
            "tell me a joke",
            "play music",
            "open chrome",
            "search google for cats",
            "what is the weather today",
        ],
    },
    "FORBIDDEN": {
        "count": 300,
        "templates": [
            "delete everything",
            "rm -rf /",
            "format c drive",
            "shutdown system",
            "wipe all files",
        ],
    },
}

# -------------------------
# Noise
# -------------------------

FILLERS = ["", "please ", "can you ", "hey ", "could you ", "quickly "]
SUFFIXES = ["", " now", " asap", " please"]

def add_noise(text: str) -> str:
    if random.random() < 0.25:
        text = text.capitalize()
    if random.random() < 0.2:
        text = text.replace(" ", "  ")
    if random.random() < 0.15:
        text = text.replace("e", "3", 1)
    if random.random() < 0.15:
        text += random.choice(SUFFIXES)
    return text

def fill(template: str) -> str:
    base = template.format(
        dir=rand_dir(),
        file=rand_file(),
        src=rand_file(),
        dst=random.choice([rand_file(), rand_dir()]),
    )
    base = random.choice(FILLERS) + base
    return add_noise(base.strip())

# -------------------------
# Dataset generation
# -------------------------

def generate_dataset(output_path="intent_dataset.csv"):
    samples = []

    for label, cfg in INTENTS.items():
        for _ in range(cfg["count"]):
            samples.append((fill(random.choice(cfg["templates"])), label))

    random.shuffle(samples)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "label"])
        writer.writerows(samples)

    print(f"Generated {len(samples)} samples → {output_path}")

if __name__ == "__main__":
    generate_dataset()
