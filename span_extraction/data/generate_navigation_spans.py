import csv
import random
import string

# -----------------------------
# Directory generators
# -----------------------------

SYSTEM_DIRS = [
    "downloads", "documents", "desktop",
    "home", "pictures", "videos"
]

BASE_DIR_WORDS = [
    "src", "data", "logs", "backup",
    "project", "build", "tmp", "cache"
]

def rand_word(min_len=2, max_len=8):
    return "".join(
        random.choices(string.ascii_lowercase, k=random.randint(min_len, max_len))
    )

def rand_dir():
    base = random.choice(BASE_DIR_WORDS + [rand_word()])
    if random.random() < 0.4:
        base += "_" + random.choice(["v1", "v2", "old", "new", "backup"])
    if random.random() < 0.3:
        base += str(random.randint(1, 5))
    return base

def rand_path():
    if random.random() < 0.4:
        return rand_dir() + "/" + rand_dir()
    return rand_dir()

# -----------------------------
# Templates
# -----------------------------

TEMPLATES = [
    "go to {dir}",
    "lets go to {dir}",
    "lets go from current to {dir}",
    "take me to {dir}",
    "take me into {dir}",
    "open {dir}",
    "open {dir} folder",
    "navigate to {dir}",
    "switch to {dir}",
    "cd {dir}",
    "could you please open {dir}",
    "go ahead and open {dir} for me",
    "i want to move to {dir}",
    "please take me to {dir}",
]

NOISE_PREFIX = ["", "hey ", "okay ", "so ", "well ", "pls "]
NOISE_SUFFIX = ["", " please", " now", " quickly", " for me", " asap"]

# -----------------------------
# Safe noise
# -----------------------------

def add_noise_safe(text, start, end):
    chars = list(text)

    for i in range(len(chars)):
        if start <= i < end:
            continue
        if random.random() < 0.02 and chars[i] == "o":
            chars[i] = "0"

    noisy = "".join(chars)

    if random.random() < 0.3:
        noisy = noisy.capitalize()

    if random.random() < 0.25:
        noisy = noisy.replace(" ", "  ")

    return noisy

# -----------------------------
# Sentence generation
# -----------------------------

def generate_sentence(dir_name):
    template = random.choice(TEMPLATES)
    prefix = random.choice(NOISE_PREFIX)
    suffix = random.choice(NOISE_SUFFIX)

    base_sentence = prefix + template.format(dir=dir_name) + suffix

    start = base_sentence.index(dir_name)
    end = start + len(dir_name)

    sentence = add_noise_safe(base_sentence, start, end).strip()

    # Safety check
    assert dir_name in sentence

    return sentence, start, end

# -----------------------------
# Main
# -----------------------------

def main():
    rows = []

    for _ in range(1500):
        d = random.choice(SYSTEM_DIRS) if random.random() < 0.3 else rand_path()
        text, start, end = generate_sentence(d)
        rows.append([text, start, end])

    with open("navigation_spans.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "start_char", "end_char"])
        writer.writerows(rows)

    print(f"Generated {len(rows)} safe, diverse navigation span samples")

if __name__ == "__main__":
    main()
