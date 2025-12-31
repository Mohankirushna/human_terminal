import csv
import random

INTENTS = {
    "NAVIGATION": {
        "count": 300,
        "templates": [
            "go to {dir}",
            "cd to {dir}",
            "open {dir}",
            "navigate to {dir}",
            "take me to {dir}",
            "switch to {dir}",
            "enter {dir}",
        ],
    },
    "LIST_FILES": {
        "count": 250,
        "templates": [
            "list files",
            "show files",
            "list all files",
            "show directory contents",
            "what files are here",
        ],
    },
    "SHOW_PATH": {
        "count": 200,
        "templates": [
            "where am i",
            "current directory",
            "print working directory",
            "show path",
            "pwd",
        ],
    },
    "CREATE_FILE": {
        "count": 250,
        "templates": [
            "create file {file}",
            "make a file named {file}",
            "new file {file}",
            "touch {file}",
        ],
    },
    "READ_FILE": {
        "count": 250,
        "templates": [
            "show contents of {file}",
            "open {file}",
            "read {file}",
            "display {file}",
            "cat {file}",
        ],
    },
    "DELETE_FILE": {
        "count": 250,
        "templates": [
            "delete {file}",
            "remove {file}",
            "erase {file}",
        ],
    },
    "COPY_FILE": {
        "count": 200,
        "templates": [
            "copy {src} to {dst}",
            "duplicate {src} into {dst}",
        ],
    },
    "MOVE_FILE": {
        "count": 200,
        "templates": [
            "move {src} to {dst}",
            "relocate {src} into {dst}",
        ],
    },
    "RENAME_FILE": {
        "count": 200,
        "templates": [
            "rename {src} to {dst}",
            "change filename from {src} to {dst}",
        ],
    },
    "INVALID": {
        "count": 200,
        "templates": [
            "tell me a joke",
            "open chrome",
            "play music",
            "search google for cats",
            "what is the weather today",
        ],
    },
    "FORBIDDEN": {
        "count": 150,
        "templates": [
            "format c drive",
            "delete everything",
            "shutdown system",
            "restart computer",
            "rm -rf /",
            "wipe all files",
        ],
    },
}

DIRS = [
    "downloads", "documents", "desktop", "home",
    "projects", "src", "data", "logs"
]

FILES = [
    "test.txt", "notes.txt", "a.py", "main.cpp",
    "data.csv", "report.pdf"
]

FILLERS = ["", "please ", "can you ", "hey "]

def add_noise(text: str) -> str:
    if random.random() < 0.3:
        text = text.capitalize()
    if random.random() < 0.2:
        text = text.replace(" ", "  ")
    if random.random() < 0.1:
        text = text.replace("o", "0", 1)
    return text

def fill(template):
    base = template.format(
        dir=random.choice(DIRS),
        file=random.choice(FILES),
        src=random.choice(FILES),
        dst=random.choice(FILES + DIRS),
    )
    base = random.choice(FILLERS) + base
    return add_noise(base.strip())

def generate_dataset(output_path="intent_dataset.csv"):
    samples = []

    for label, cfg in INTENTS.items():
        for _ in range(cfg["count"]):
            template = random.choice(cfg["templates"])
            samples.append((fill(template), label))

    random.shuffle(samples)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "label"])
        writer.writerows(samples)

    print(f"Generated {len(samples)} samples → {output_path}")

if __name__ == "__main__":
    generate_dataset()
