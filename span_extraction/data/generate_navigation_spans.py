import csv
import random

SYSTEM_DIRS = [
    "downloads", "documents", "desktop",
    "home", "pictures", "videos"
]

RANDOM_DIRS = [
    "aa", "bb", "cc", "xyz", "tmp",
    "project", "backup", "logs", "data",
    "my_folder", "test123", "foo-bar", "abc_def",
    "something", "where", "here", "there"
]

ALL_DIRS = SYSTEM_DIRS + RANDOM_DIRS

TEMPLATES = [
    "go to {dir}",
    "lets go to {dir}",
    "lets go from current to {dir}",
    "take me to {dir}",
    "take me into {dir}",
    "open {dir}",
    "open {dir} folder",
    "navigate to {dir}",
    "switch to {dir}",
    "could you please open {dir}",
    "go ahead and open {dir} for me",
    "i want to move to {dir}",
    "please take me to {dir}",
]

NOISE_PREFIX = [
    "",
    "hey ",
    "okay ",
    "so ",
    "well ",
]

NOISE_SUFFIX = [
    "",
    " please",
    " now",
    " quickly",
    " for me",
]

def generate_sentence(dir_name):
    template = random.choice(TEMPLATES)
    prefix = random.choice(NOISE_PREFIX)
    suffix = random.choice(NOISE_SUFFIX)

    sentence = prefix + template.format(dir=dir_name) + suffix
    start = sentence.index(dir_name)
    end = start + len(dir_name)

    return sentence.strip(), start, end

def main():
    rows = []

    for _ in range(500):
        d = random.choice(ALL_DIRS)
        text, start, end = generate_sentence(d)
        rows.append([text, start, end])

    with open("navigation_spans.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "start_char", "end_char"])
        writer.writerows(rows)

    print(f"Generated {len(rows)} navigation span samples")

if __name__ == "__main__":
    main()
