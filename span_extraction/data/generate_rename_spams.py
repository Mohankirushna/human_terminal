import csv
import random
import string
import nlpaug.augmenter.word as naw

# -----------------------------
# Random generators
# -----------------------------

EXTENSIONS = [
    "txt", "csv", "py", "js", "md", "json",
    "log", "pdf", "docx", "png", "jpg"
]

DIR_NAMES = [
    "src", "data", "logs", "backup", "tmp",
    "project", "old", "new", "v1", "v2"
]

def rand_word(min_len=3, max_len=8):
    return "".join(
        random.choices(string.ascii_lowercase, k=random.randint(min_len, max_len))
    )

def random_filename():
    return f"{rand_word()}.{random.choice(EXTENSIONS)}"

def maybe_path(name):
    if random.random() < 0.4:
        return f"{random.choice(DIR_NAMES)}/{name}"
    return name

def maybe_quotes(name):
    if random.random() < 0.3:
        return f'"{name}"'
    return name

# -----------------------------
# Templates
# -----------------------------

TEMPLATES = [
    "rename {src} to {dst}",
    "rename {src} as {dst}",
    "change {src} to {dst}",
    "change filename from {src} to {dst}",
    "rename file {src} into {dst}",
    "update the name of {src} to {dst}",
    "i want to rename {src} to {dst}",
    "could you rename {src} as {dst}",
]

PREFIX_NOISE = ["", "hey ", "please ", "can you ", "okay "]
SUFFIX_NOISE = ["", " please", " now", " for me"]

# -----------------------------
# NLP augmenters (SAFE)
# -----------------------------

syn_aug = naw.SynonymAug(aug_src="wordnet", aug_p=0.25)
del_aug = naw.RandomWordAug(action="delete", aug_p=0.08)

# -----------------------------
# Span-safe augmentation
# -----------------------------

def augment_outside_spans(text, spans):
    tokens = text.split()
    new_tokens = []
    char_idx = 0

    def protected(start, end):
        for s, e in spans:
            if start < e and end > s:
                return True
        return False

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

def generate_sentence():
    src = maybe_quotes(maybe_path(random_filename()))
    dst = maybe_quotes(maybe_path(random_filename()))

    template = random.choice(TEMPLATES)
    prefix = random.choice(PREFIX_NOISE)
    suffix = random.choice(SUFFIX_NOISE)

    base_sentence = (prefix + template.format(src=src, dst=dst) + suffix).strip()

    # Compute spans BEFORE augmentation
    src_start = base_sentence.index(src)
    src_end = src_start + len(src)

    dst_start = base_sentence.index(dst)
    dst_end = dst_start + len(dst)

    sentence = augment_outside_spans(
        base_sentence,
        [(src_start, src_end), (dst_start, dst_end)]
    )

    # Recompute spans AFTER augmentation
    src_start = sentence.index(src)
    src_end = src_start + len(src)

    dst_start = sentence.index(dst)
    dst_end = dst_start + len(dst)

    return sentence, src_start, src_end, dst_start, dst_end

# -----------------------------
# Main
# -----------------------------

def main(n_samples=2500, out_path="rename_spans.csv"):
    rows = []

    for _ in range(n_samples):
        text, s1, e1, s2, e2 = generate_sentence()
        rows.append([text, s1, e1, s2, e2])

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["text", "src_start", "src_end", "dst_start", "dst_end"]
        )
        writer.writerows(rows)

    print(f"Generated {len(rows)} SAFE + NLP-AUGMENTED rename span samples → {out_path}")

if __name__ == "__main__":
    main()
