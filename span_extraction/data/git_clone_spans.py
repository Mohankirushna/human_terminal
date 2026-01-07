import csv
import random
import string

def rand_repo():
    if random.random() < 0.6:
        return f"https://github.com/{rand_word()}/{rand_word()}.git"
    return rand_word()

def rand_word():
    return "".join(random.choices(string.ascii_lowercase, k=6))

TEMPLATES = [
    "git clone {repo}",
    "clone repository {repo}",
    "clone {repo}",
]

def main():
    rows = []
    for _ in range(2000):
        r = rand_repo()
        text = random.choice(TEMPLATES).format(repo=r)
        start = text.index(r)
        end = start + len(r)
        rows.append([text, start, end])

    with open("git_clone_spans.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "start_char", "end_char"])
        writer.writerows(rows)

if __name__ == "__main__":
    main()
