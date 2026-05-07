import sys


def main() -> None:
    msg = sys.stdin.read().splitlines()
    msg = [line for line in msg if line.strip() != "Co-authored-by: Cursor <cursoragent@cursor.com>"]
    sys.stdout.write("\n".join(msg).rstrip() + "\n")


if __name__ == "__main__":
    main()

