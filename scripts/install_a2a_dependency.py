from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"
DEPENDENCY = "a2a-sdk[http-server]>=1.0,<2.0"


def main() -> None:
    lines = REQUIREMENTS.read_text(
        encoding="utf-8",
    ).splitlines()

    if any(
        line.strip().startswith("a2a-sdk")
        for line in lines
    ):
        print("An a2a-sdk dependency already exists.")
        return

    with REQUIREMENTS.open(
        "a",
        encoding="utf-8",
    ) as file:
        if lines and lines[-1].strip():
            file.write("\n")

        file.write(DEPENDENCY + "\n")

    print(f"Added {DEPENDENCY}")


if __name__ == "__main__":
    main()
