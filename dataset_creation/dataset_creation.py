import nltk
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('averaged_perceptron_tagger_eng')

import csv
import random
import string
import nlpaug.augmenter.word as naw
import nlpaug.augmenter.char as nac

# -------------------------
# Random name generators
# -------------------------

FILE_EXTENSIONS = ["py", "txt", "csv", "json", "md", "log", "pdf", "yaml"]

def rand_word(min_len=3, max_len=8):
    return "".join(random.choices(string.ascii_lowercase, k=random.randint(min_len, max_len)))

def rand_file():
    base = rand_word()
    if random.random() < 0.4:
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
# NLP Augmenters (SAFE SET)
# -------------------------

# Synonym replacement (WordNet) – safest
syn_aug = naw.SynonymAug(aug_src="wordnet", aug_p=0.25)

# Random word deletion (very low prob)
del_aug = naw.RandomWordAug(action="delete", aug_p=0.08)

# Minor character noise (typos)
char_aug = nac.RandomCharAug(
    action="substitute",
    aug_char_p=0.05
)



# -------------------------
# Intents
# -------------------------

INTENTS = {

    # =====================
    # NAVIGATION
    # =====================
    "NAVIGATION": {
        "count": 500,
        "templates": [
            "go to {dir}",
            "navigate to {dir}",
            "enter {dir}",
            "cd {dir}",
            "switch to {dir}",
            "move into {dir}",
        ],
    },

    "PWD": {
        "count": 350,
        "templates": [
            "where am i",
            "current directory",
            "pwd",
            "print working directory",
        ],
    },

    "LIST_FILES": {
        "count": 450,
        "templates": [
            "list files",
            "show files",
            "dir",
            "ls",
            "list all files",
            "show directory contents",
        ],
    },

    # =====================
    # FILE OPERATIONS
    # =====================
    "CREATE_FILE": {
        "count": 500,
        "templates": [
            "create file {file}",
            "make file {file}",
            "new file {file}",
            "touch {file}",
        ],
    },

    "CREATE_DIR": {
        "count": 400,
        "templates": [
            "create directory {dir}",
            "make folder {dir}",
            "mkdir {dir}",
            "new directory {dir}",
        ],
    },
    
    "DELETE_DIR": {
        "count": 400,
        "templates": [
            "delete directory {dir}",
            "remove directory {dir}",
            "delete folder {dir}",
            "remove folder {dir}",
            "rmdir {dir}",
        ],
    },


    "DELETE_FILE": {
        "count": 500,
        "templates": [
            "delete {file}",
            "remove {file}",
            "erase {file}",
            "rm {file}",
        ],
    },

    "COPY_FILE": {
        "count": 400,
        "templates": [
            "copy {src} to {dst}",
            "duplicate {src} into {dst}",
            "cp {src} {dst}",
        ],
    },

    "MOVE_FILE": {
        "count": 400,
        "templates": [
            "move {src} to {dst}",
            "relocate {src} into {dst}",
            "mv {src} {dst}",
        ],
    },

    "RENAME_FILE": {
        "count": 350,
        "templates": [
            "rename {src} to {dst}",
            "change filename from {src} to {dst}",
        ],
    },

    # =====================
    # SYSTEM / CMD
    # =====================
    "SYSTEM_INFO": {
        "count": 350,
        "templates": [
            "system info",
            "show system info",
            "whoami",
            "hostname",
            "ver",
        ],
    },

    "PROCESS_LIST": {
        "count": 350,
        "templates": [
            "list processes",
            "show running processes",
            "tasklist",
        ],
    },

    "PROCESS_KILL": {
        "count": 300,
        "templates": [
            "kill process {file}",
            "terminate process {file}",
            "taskkill {file}",
        ],
    },

    "NETWORK_INFO": {
        "count": 350,
        "templates": [
            "ip config",
            "show ip address",
            "network configuration",
            "ipconfig",
        ],
    },

    "ENV_VAR": {
        "count": 300,
        "templates": [
            "show environment variables",
            "list env",
            "set variable",
            "echo %path%",
        ],
    },

    # =====================
    # GIT — CORE
    # =====================
    "GIT_STATUS": {
        "count": 400,
        "templates": [
            "git status",
            "show git status",
            "any git changes",
        ],
    },

    "GIT_BRANCH": {
        "count": 400,
        "templates": [
            "git branch",
            "list branches",
            "current git branch",
        ],
    },

    "GIT_CHECKOUT": {
        "count": 350,
        "templates": [
            "git checkout {dir}",
            "switch branch to {dir}",
            "change branch to {dir}",
        ],
    },

    "GIT_ADD": {
        "count": 400,
        "templates": [
            "git add {file}",
            "stage {file}",
            "add file to git",
        ],
    },

    "GIT_COMMIT": {
        "count": 400,
        "templates": [
            "git commit",
            "commit changes",
            "save git changes",
        ],
    },

    "GIT_LOG": {
        "count": 350,
        "templates": [
            "git log",
            "show commit history",
            "git history",
        ],
    },

    "GIT_PULL": {
        "count": 350,
        "templates": [
            "git pull",
            "pull latest changes",
            "update from remote",
        ],
    },

    "GIT_PUSH": {
        "count": 350,
        "templates": [
            "git push",
            "push changes",
            "upload commits",
        ],
    },

    "GIT_CLONE": {
        "count": 300,
        "templates": [
            "git clone {dir}",
            "clone repository",
            "copy git repo",
        ],
    },

    "GIT_RESET": {
        "count": 300,
        "templates": [
            "git reset",
            "reset git changes",
            "undo git add",
        ],
    },

    "GIT_STASH": {
        "count": 300,
        "templates": [
            "git stash",
            "stash changes",
            "save work temporarily",
        ],
    },

    # =====================
    # SAFETY
    # =====================
    "FORBIDDEN": {
        "count": 400,
        "templates": [
            "delete everything",
            "rm -rf /",
            "format c drive",
            "shutdown system",
            "erase disk",
        ],
    },

    "UNKNOWN": {
        "count": 500,
        "templates": [
            "open chrome",
            "play music",
            "tell me a joke",
            "search google",
        ],
    },
}


# -------------------------
# Controlled augmentation
# -------------------------

def augment_text(text: str) -> str:
    if random.random() < 0.35:
        text = syn_aug.augment(text)
    if random.random() < 0.15:
        text = del_aug.augment(text)
    if random.random() < 0.10:
        text = char_aug.augment(text)
    return text

def fill(template: str) -> str:
    base = template.format(
        dir=rand_dir(),
        file=rand_file(),
        src=rand_file(),
        dst=random.choice([rand_file(), rand_dir()]),
    )
    return augment_text(base)

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
