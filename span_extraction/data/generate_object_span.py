import csv
import random
import string
import nlpaug.augmenter.word as naw

# -----------------------------
# Random name generators
# -----------------------------

FILE_EXTENSIONS = [
    "py", "txt", "csv", "json", "md", "log",
    "yaml", "yml", "pdf", "png", "jpg"
]

def random_word(min_len=3, max_len=8):
    return "".join(
        random.choices(string.ascii_lowercase, k=random.randint(min_len, max_len))
    )

def random_file_name():
    base = random_word()
    if random.random() < 0.5:
        base += f"_{random.randint(1, 99)}"
    return f"{base}.{random.choice(FILE_EXTENSIONS)}"

def random_dir_name():
    base = random_word()
    if random.random() < 0.4:
        base += "_" + random.choice(["backup", "data", "src", "build"])
    if random.random() < 0.3:
        base += str(random.randint(1, 5))
    return base

# -----------------------------
# Templates
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

# -----------------------------
# NLP augmenters (SAFE)
# -----------------------------

syn_aug = naw.SynonymAug(aug_src="wordnet", aug_p=0.25)
del_aug = naw.RandomWordAug(action="delete", aug_p=0.08)

# -----------------------------
# Span-safe augmentation
# -----------------------------

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

# -----------------------------
# Sentence generation
# -----------------------------

def generate_sentence(obj):
    template = random.choice(TEMPLATES)
    sentence = template.format(obj=obj)

    start = sentence.index(obj)
    end = start + len(obj)

    sentence = augment_outside_span(sentence, (start, end))

    # Recompute span after augmentation
    start = sentence.index(obj)
    end = start + len(obj)

    return sentence, start, end

# -----------------------------
# Main
# -----------------------------

def main():
    rows = []

    for _ in range(7000):
        obj = (
            random_file_name()
            if random.random() < 0.6
            else random_dir_name()
        )

        text, start, end = generate_sentence(obj)
        rows.append([text, start, end])

    with open("object_spans.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "start_char", "end_char"])
        writer.writerows(rows)

    print(f"Generated {len(rows)} SAFE + NLP-AUGMENTED object span samples")

if __name__ == "__main__":
    main()
