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
    "NAVIGATION": {
        "count": 450,
        "templates": [
            "go to {dir}",
            "navigate to {dir}",
            "open {dir}",
            "enter {dir}",
            "switch to {dir}",
            "cd {dir}",
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
        ],
    },
    "CREATE_FILE": {
        "count": 450,
        "templates": [
            "create file {file}",
            "make a file named {file}",
            "new file {file}",
            "touch {file}",
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
            "copy file {src} to {dst}",
            "duplicate {src} into {dst}",
            "duplicate file {src} into {dst}",
            "cp {src} {dst}",
        ],
    },
    "MOVE_FILE": {
        "count": 350,
        "templates": [
            "move {src} to {dst}",
            "move file {src} to {dst}",
            "relocate {src} into {dst}",
            "relocate file {src} into {dst}",
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
    "UNKNOWN": {
        "count": 400,
        "templates": [
            "open chrome",
            "play music",
            "tell me a joke",
            "search google",
        ],
    },
    "FORBIDDEN": {
        "count": 300,
        "templates": [
            "delete everything",
            "rm -rf /",
            "format c drive",
            "shutdown system",
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
