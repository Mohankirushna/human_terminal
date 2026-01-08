import csv
import random
import string

PROCESS_NAMES = [
    "notepad",
    "chrome",
    "python",
    "code",
    "explorer",
    "cmd",
    "powershell",
    "java",
    "node",
]

TEMPLATES = [
    "kill process {target}",
    "terminate {target}",
    "end process {target}",
    "taskkill {target}",
    "stop {target}",
]

def rand_pid():
    return str(random.randint(100, 9999))

def rand_target():
    return random.choice(PROCESS_NAMES + [rand_pid()])

def generate(output_path="process_target_spans.csv", count=800):
    rows = []

    for _ in range(count):
        target = rand_target()
        template = random.choice(TEMPLATES)
        text = template.format(target=target)

        start = text.index(target)
        end = start + len(target)

        rows.append([text, start, end])

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "start_char", "end_char"])
        writer.writerows(rows)

    print(f"Generated {len(rows)} samples → {output_path}")

if __name__ == "__main__":
    generate()
