import csv
import random
import string

EXTENSIONS = [
    "txt", "csv", "py", "js", "md", "json",
    "log", "pdf", "docx", "png", "jpg"
]

DIR_NAMES = [
    "src", "data", "logs", "backup", "tmp",
    "project", "old", "new", "v1", "v2"
]

PREFIX_NOISE = [
    "",
    "hey ",
    "okay ",
    "so ",
    "well ",
    "can you ",
    "please ",
]

SUFFIX_NOISE = [
    "",
    " please",
    " now",
    " for me",
    " quickly",
]

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

def random_filename():
    name = "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 8)))
    ext = random.choice(EXTENSIONS)
    return f"{name}.{ext}"

def maybe_path(name):
    if random.random() < 0.4:
        return f"{random.choice(DIR_NAMES)}/{name}"
    return name

def maybe_quotes(name):
    if random.random() < 0.3:
        return f'"{name}"'
    return name

def add_noise(text: str) -> str:
    if random.random() < 0.2:
        text = text.replace(" ", "  ")
    if random.random() < 0.1:
        text = text.capitalize()
    return text

def generate_sentence():
    src_name = maybe_path(random_filename())
    dst_name = maybe_path(random_filename())

    src = maybe_quotes(src_name)
    dst = maybe_quotes(dst_name)

    template = random.choice(TEMPLATES)
    prefix = random.choice(PREFIX_NOISE)
    suffix = random.choice(SUFFIX_NOISE)

    sentence = (prefix + template.format(src=src, dst=dst) + suffix).strip()
    sentence = add_noise(sentence)

    src_start = sentence.index(src)
    src_end = src_start + len(src)

    dst_start = sentence.index(dst)
    dst_end = dst_start + len(dst)

    return sentence, src_start, src_end, dst_start, dst_end

def main(n_samples=2000, out_path="rename_spans.csv"):
    rows = []

    for _ in range(n_samples):
        text, s1, e1, s2, e2 = generate_sentence()
        rows.append([text, s1, e1, s2, e2])

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "src_start", "src_end", "dst_start", "dst_end"])
        writer.writerows(rows)

    print(f"Generated {len(rows)} diversified rename span samples → {out_path}")

if __name__ == "__main__":
    main()
