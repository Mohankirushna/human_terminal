import csv
import random
import string

# -----------------------------
# Random name generators
# -----------------------------

FILE_EXTS = ["py", "txt", "csv", "json", "log", "pdf", "png"]

def rand_word(min_len=3, max_len=8):
    return "".join(
        random.choices(string.ascii_lowercase, k=random.randint(min_len, max_len))
    )

def rand_file():
    base = rand_word()
    if random.random() < 0.4:
        base += f"_{random.randint(1, 99)}"
    if random.random() < 0.2:
        base = f"img{random.randint(1, 999)}"
    return f"{base}.{random.choice(FILE_EXTS)}"

def rand_dir():
    base = rand_word()
    if random.random() < 0.4:
        base += "_" + random.choice(["data", "logs", "backup", "src"])
    if random.random() < 0.3:
        base += str(random.randint(1, 5))
    return base

# -----------------------------
# Templates & noise
# -----------------------------

TEMPLATES = [
    "move {src} to {dst}",
    "copy {src} to {dst}",
    "move file {src} into {dst}",
    "copy file {src} into {dst}",
    "relocate {src} under {dst}",
    "shift {src} into {dst}",
    "transfer {src} to {dst}",
    "can you move {src} to {dst}",
    "please copy {src} into {dst}",
    "mv {src} {dst}",
    "cp {src} {dst}",
]

NOISE_PREFIX = ["", "hey ", "okay ", "so ", "well ", "pls "]
NOISE_SUFFIX = ["", " please", " now", " quickly", " asap", " for me"]

# -----------------------------
# Safe noise (never touches spans)
# -----------------------------

def add_noise_safe(text, src_span, dst_span):
    chars = list(text)

    s_s, s_e = src_span
    d_s, d_e = dst_span

    for i in range(len(chars)):
        if s_s <= i < s_e or d_s <= i < d_e:
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

def generate_sentence(src, dst):
    template = random.choice(TEMPLATES)
    prefix = random.choice(NOISE_PREFIX)
    suffix = random.choice(NOISE_SUFFIX)

    base_sentence = prefix + template.format(src=src, dst=dst) + suffix

    # Calculate spans BEFORE noise
    src_start = base_sentence.index(src)
    src_end = src_start + len(src)

    dst_start = base_sentence.index(dst)
    dst_end = dst_start + len(dst)

    # Apply safe noise
    sentence = add_noise_safe(
        base_sentence,
        (src_start, src_end),
        (dst_start, dst_end),
    )

    # Safety check (optional but recommended)
    assert src in sentence
    assert dst in sentence

    return sentence.strip(), src_start, src_end, dst_start, dst_end

# -----------------------------
# Main
# -----------------------------

def main():
    src_rows = []
    dst_rows = []

    for _ in range(1500):
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

    print("Generated SAFE & DIVERSE MOVE/COPY span datasets")

if __name__ == "__main__":
    main()
