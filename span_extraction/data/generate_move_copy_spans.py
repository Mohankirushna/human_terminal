import csv
import random

FILES = [
    "a.txt", "notes.txt", "report.pdf",
    "image.png", "main.py", "chanau.py",
    "data.csv", "test123.log"
]

DIRS = [
    "downloads", "documents", "desktop",
    "backup", "data", "logs",
    "aa", "bb", "project", "tmp",
    "something", "where"
]

TEMPLATES = [
    "move {src} to {dst}",
    "copy {src} to {dst}",
    "move file {src} into {dst}",
    "copy file {src} into {dst}",
    "can you move {src} to {dst}",
    "please copy {src} into {dst}",
    "shift {src} to {dst}",
    "relocate {src} into {dst}",
]

NOISE_PREFIX = ["", "hey ", "okay ", "so ", "well "]
NOISE_SUFFIX = ["", " please", " now", " for me", " quickly"]

def generate_sentence(src, dst):
    template = random.choice(TEMPLATES)
    prefix = random.choice(NOISE_PREFIX)
    suffix = random.choice(NOISE_SUFFIX)

    sentence = prefix + template.format(src=src, dst=dst) + suffix

    src_start = sentence.index(src)
    src_end = src_start + len(src)

    dst_start = sentence.index(dst)
    dst_end = dst_start + len(dst)

    return sentence.strip(), src_start, src_end, dst_start, dst_end

def main():
    src_rows = []
    dst_rows = []

    for _ in range(800):
        src = random.choice(FILES)
        dst = random.choice(DIRS)

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

    print("Generated MOVE/COPY span datasets")

if __name__ == "__main__":
    main()
