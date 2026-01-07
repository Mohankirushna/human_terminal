import csv
import random
import string

BRANCH_WORDS = ["main", "master", "dev", "develop", "feature", "bugfix", "release"]

def rand_branch():
    base = random.choice(BRANCH_WORDS)
    if random.random() < 0.5:
        base += "-" + "".join(random.choices(string.ascii_lowercase, k=4))
    return base

TEMPLATES = [
    "git checkout {branch}",
    "switch to {branch}",
    "change branch to {branch}",
    "checkout {branch}",
]

def main():
    rows = []
    for _ in range(2000):
        b = rand_branch()
        text = random.choice(TEMPLATES).format(branch=b)
        start = text.index(b)
        end = start + len(b)
        rows.append([text, start, end])

    with open("git_checkout_spans.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "start_char", "end_char"])
        writer.writerows(rows)

if __name__ == "__main__":
    main()
