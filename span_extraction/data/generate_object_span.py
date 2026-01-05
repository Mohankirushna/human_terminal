import csv
import random
import string

# -----------------------------
# Random name generators
# -----------------------------

FILE_EXTENSIONS = [
    "py", "txt", "csv", "json", "md", "log",
    "yaml", "yml", "pdf", "png", "jpg"
]

def random_word(min_len=3, max_len=8):
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def random_file_name():
    base = random_word()
    if random.random() < 0.5:
        base += f"_{random.randint(1, 99)}"
    ext = random.choice(FILE_EXTENSIONS)
    return f"{base}.{ext}"

def random_dir_name():
    base = random_word()
    if random.random() < 0.4:
        base += f"_{random.choice(['backup', 'data', 'src', 'build'])}"
    if random.random() < 0.3:
        base += f"{random.randint(1, 5)}"
    return base

# -----------------------------
# Templates and noise
# -----------------------------

TEMPLATES = [
    "delete {obj}",
    "remove {obj}",
    "erase {obj}",
    "create {obj}",
    "make {obj}",
    "create file {obj}",
    "create directory {obj}",
    "make directory {obj}",
    "remove file {obj}",
    "delete directory {obj}",
    "please delete {obj}",
    "can you remove {obj}",
    "i want to delete {obj}",
]

NOISE_PREFIX = ["", "hey ", "okay ", "so "]
NOISE_SUFFIX = ["", " please", " now", " quickly"]

# -----------------------------
# Sentence generation
# -----------------------------

def generate_sentence(obj):
    template = random.choice(TEMPLATES)
    prefix = random.choice(NOISE_PREFIX)
    suffix = random.choice(NOISE_SUFFIX)

    sentence = prefix + template.format(obj=obj) + suffix
    start = sentence.index(obj)
    end = start + len(obj)

    return sentence.strip(), start, end

# -----------------------------
# Main
# -----------------------------

def main():
    rows = []

    for _ in range(6000):
        obj = random_file_name() if random.random() < 0.6 else random_dir_name()
        text, start, end = generate_sentence(obj)
        rows.append([text, start, end])

    with open("object_spans.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "start_char", "end_char"])
        writer.writerows(rows)

    print(f"Generated {len(rows)} object span samples")

if __name__ == "__main__":
    main()
