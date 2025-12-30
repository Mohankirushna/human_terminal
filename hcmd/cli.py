import sys
from .core import RuleParser, CommandGenerator, CommandExecutor, validate
from .constants import CommandType

def main():
    if len(sys.argv) < 2:
        print("Usage: hcmd <natural language command>")
        return 1

    text = " ".join(sys.argv[1:])

    parser = RuleParser()
    generator = CommandGenerator()
    executor = CommandExecutor()

    intent, args = parser.parse(text)

    if intent == CommandType.UNKNOWN:
        print("ERROR: Unknown command")
        return 1

    ok, err = validate(intent, args)
    if not ok:
        print(f"ERROR: {err}")
        return 1

    cmd = generator.generate(intent, args)
    if not cmd:
        print("ERROR: Could not generate command")
        return 1

    success, output = executor.execute(cmd)
    if not success:
        print(f"ERROR: {output}")
        return 1

    if output:
        print(output)

    return 0

if __name__ == "__main__":
    sys.exit(main())
