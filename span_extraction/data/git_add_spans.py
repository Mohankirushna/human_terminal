import csv
import random
import string

EXTS = ["py", "txt", "md", "csv"]

def rand_word():
    return "".join(random.choices(string.ascii_lowercase, k=6))

def rand_path():
    if random.random() < 0.5:
        return rand_word() + "." + random.choice(EXTS)
    return rand_word() + "/" + rand_word()

TEMPLATES = [
    "git add {path}",
    "stage {path}",
    "add {path}",
    "add file {path}",
]

def main():
    rows = []
    for _ in range(2000):
        p = rand_path()
        text = random.choice(TEMPLATES).format(path=p)
        start = text.index(p)
        end = start + len(p)
        rows.append([text, start, end])

    with open("git_add_spans.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "start_char", "end_char"])
        writer.writerows(rows)

if __name__ == "__main__":
    main()
