#!/usr/bin/env python3
"""Update the passing test count in replit.md from live pytest output."""

import re
import subprocess
import sys


def get_passing_count() -> int:
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "--tb=no", "-q"],
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    if result.returncode != 0:
        print("ERROR: pytest exited with failures (exit code %d). replit.md will not be updated." % result.returncode, file=sys.stderr)
        print(output, file=sys.stderr)
        sys.exit(result.returncode)
    match = re.search(r"(\d+) passed", output)
    if not match:
        print("ERROR: could not find passing test count in pytest output.", file=sys.stderr)
        print(output, file=sys.stderr)
        sys.exit(1)
    return int(match.group(1))


def update_readme(count: int, readme_path: str = "replit.md") -> None:
    with open(readme_path, "r") as f:
        content = f.read()

    new_content, n = re.subn(
        r"(?<=\*\*Testing:\*\* )\d+(?= passing tests)",
        str(count),
        content,
    )
    if n == 0:
        print("ERROR: could not find the Testing line to update in replit.md.", file=sys.stderr)
        sys.exit(1)

    with open(readme_path, "w") as f:
        f.write(new_content)

    print(f"Updated replit.md: {count} passing tests")


if __name__ == "__main__":
    count = get_passing_count()
    update_readme(count)
