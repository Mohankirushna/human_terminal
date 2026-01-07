import csv
import random
import string
import nlpaug.augmenter.word as naw

# -----------------------------
# File / directory generators
# -----------------------------

FILE_EXTS = ["py", "txt", "csv", "json", "md", "log", "pdf"]

def rand_word(min_len=3, max_len=8):
    return "".join(
        random.choices(string.ascii_lowercase, k=random.randint(min_len, max_len))
    )

def rand_file():
    base = rand_word()
    if random.random() < 0.5:
        base += f"_{random.randint(1,99)}"
    return f"{base}.{random.choice(FILE_EXTS)}"

def rand_dir():
    base = rand_word()
    if random.random() < 0.4:
        base += "_" + random.choice(["src", "data", "logs", "backup"])
    if random.random() < 0.3:
        base += str(random.randint(1,5))
    return base

# -----------------------------
# Templates
# -----------------------------

TEMPLATES = [
    "move {src} to {dst}",
    "copy {src} to {dst}",
    "move file {src} into {dst}",
    "copy file {src} into {dst}",
    "relocate {src} under {dst}",
    "transfer {src} to {dst}",
    "mv {src} {dst}",
    "cp {src} {dst}",
]

# -----------------------------
# NLP augmenters (SAFE)
# -----------------------------

syn_aug = naw.SynonymAug(aug_src="wordnet", aug_p=0.25)
del_aug = naw.RandomWordAug(action="delete", aug_p=0.08)

# -----------------------------
# Span-safe augmentation
# -----------------------------

def augment_outside_spans(text, src_span, dst_span):
    tokens = text.split()
    new_tokens = []

    s_s, s_e = src_span
    d_s, d_e = dst_span
    char_idx = 0

    def protected(start, end):
        return (start < s_e and end > s_s) or (start < d_e and end > d_s)

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

def generate_sentence(src, dst):
    template = random.choice(TEMPLATES)
    base = template.format(src=src, dst=dst)

    src_start = base.index(src)
    src_end = src_start + len(src)

    dst_start = base.index(dst)
    dst_end = dst_start + len(dst)

    sentence = augment_outside_spans(
        base,
        (src_start, src_end),
        (dst_start, dst_end)
    )

    # recompute spans
    src_start = sentence.index(src)
    src_end = src_start + len(src)

    dst_start = sentence.index(dst)
    dst_end = dst_start + len(dst)

    return sentence, src_start, src_end, dst_start, dst_end

# -----------------------------
# Main
# -----------------------------

def main():
    src_rows = []
    dst_rows = []

    for _ in range(2500):
        src = rand_file()
        dst = rand_dir()

        text, s_s, s_e, d_s, d_e = generate_sentence(src, dst)

        src_rows.append([text, s_s, s_e])
        dst_rows.append([text, d_s, d_e])

    with open("move_src_spans.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "start_char", "end_char"])
        writer.writerows(src_rows)

    with open("move_dst_spans.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "start_char", "end_char"])
        writer.writerows(dst_rows)

    print("Generated MOVE/COPY src & dst span datasets")

if __name__ == "__main__":
    main()
