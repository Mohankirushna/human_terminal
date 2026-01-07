import csv
import random
import string
import nlpaug.augmenter.word as naw

# =============================
# Directory generators (ONLY)
# =============================

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
    if random.random() < 0.35:
        return rand_dir() + "/" + rand_dir()
    return rand_dir()

# =============================
# Templates
# Navigation + Create + Delete
# =============================

TEMPLATES = [

    # ---- Navigation ----
    "go to {dir}",
    "navigate to {dir}",
    "open {dir}",
    "take me to {dir}",
    "switch to {dir}",
    "cd {dir}",
    "please go to {dir}",
    "could you open {dir}",
    "i want to move to {dir}",

    # ---- Create directory ----
    "create directory {dir}",
    "create {dir} directory",
    "create {dir}",
    "make directory {dir}",
    "make {dir} directory",
    "make {dir}",
    "create folder {dir}",
    "make folder {dir}",
    "mkdir {dir}",
    "please create directory {dir}",
    "create a new folder named {dir}",

    # ---- Delete directory ----
    "delete directory {dir}"
    "delete {dir} directory",
    "delete {dir}",
    "remove directory {dir}",
    "delete folder {dir}",
    "remove folder {dir}",
    "rm {dir}",
    "please delete directory {dir}",
]

# =============================
# NLP augmenters (SAFE)
# =============================

syn_aug = naw.SynonymAug(aug_src="wordnet", aug_p=0.25)
del_aug = naw.RandomWordAug(action="delete", aug_p=0.08)

# =============================
# Span-safe augmentation
# =============================

def augment_outside_span(text, span):
    tokens = text.split()
    new_tokens = []

    s_start, s_end = span
    char_idx = 0

    def protected(start, end):
        return start < s_end and end > s_start

    for tok in tokens:
        start = text.find(tok, char_idx)
        end = start + len(tok)
        char_idx = end

        if protected(start, end):
            new_tokens.append(tok)
            continue

        if random.random() < 0.3:
            tok = syn_aug.augment(tok)[0]

        if random.random() < 0.2:
            tok = del_aug.augment(tok)[0]

        new_tokens.append(tok)

    return " ".join(new_tokens)

# =============================
# Sentence generation
# =============================

def generate_sentence(dir_name):
    template = random.choice(TEMPLATES)
    base = template.format(dir=dir_name)

    start = base.index(dir_name)
    end = start + len(dir_name)

    sentence = augment_outside_span(base, (start, end))

    # recompute span after augmentation
    start = sentence.index(dir_name)
    end = start + len(dir_name)

    return sentence, start, end

# =============================
# Main
# =============================

def main():
    rows = []

    for _ in range(2000):
        d = random.choice(SYSTEM_DIRS) if random.random() < 0.35 else rand_path()
        text, start, end = generate_sentence(d)
        rows.append([text, start, end])

    with open("directory_spans.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "start_char", "end_char"])
        writer.writerows(rows)

    print(f"Generated {len(rows)} directory-only span samples")

if __name__ == "__main__":
    main()
