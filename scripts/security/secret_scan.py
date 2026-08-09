from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SKIP_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    ".next",
    "dist",
    "__pycache__",
    ".pytest_cache",
}

TEXT_SUFFIXES = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".yml",
    ".yaml",
    ".env",
    ".md",
    ".ps1",
    ".toml",
    ".xml",
    ".ini",
    ".cfg",
}

SENSITIVE_NAMES = (
    r"password"
    r"|passwd"
    r"|api[_-]?key"
    r"|secret[_-]?key"
    r"|client[_-]?secret"
    r"|access[_-]?token"
    r"|private[_-]?key"
)

ASSIGNMENT_PATTERN = re.compile(
    rf"""
    \b(?:{SENSITIVE_NAMES})\b
    \s*[:=]\s*
    ["']
    (?P<value>[^"']+)
    ["']
    """,
    re.IGNORECASE | re.VERBOSE,
)

YAML_ASSIGNMENT_PATTERN = re.compile(
    rf"""
    ^\s*
    (?:{SENSITIVE_NAMES})
    \s*:\s*
    ["']?
    (?P<value>[^"'#\r\n]+)
    ["']?
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

ENV_ASSIGNMENT_PATTERN = re.compile(
    rf"""
    ^\s*
    (?:{SENSITIVE_NAMES})
    \s*=\s*
    (?P<value>[^\r\n]+)
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)

PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
)

KNOWN_SECRET_PATTERNS = (
    re.compile(r"\bghp_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)

SAFE_VALUE_MARKERS = (
    "example",
    "dummy",
    "fake",
    "mock",
    "test",
    "testing",
    "changeme",
    "change-me",
    "replace",
    "placeholder",
    "github-actions",
    "localhost",
    "<managed-secret>",
    "<secret>",
    "<password>",
    "<token>",
    "${{ secrets.",
    "${",
    "...",
    "{{",
    ".values.secretenv.",
)

SAFE_LINE_MARKERS = (
    "assert ",
    "not in content",
    "pulumi config set --secret",
    "read-host",
    "getnetworkcredential",
    "os.getenv",
    "os.environ",
    "getenv(",
    "require_secret(",
    "get_secret(",
    "secrets.",
    "--set secretenv.",
    ".values.secretenv.",
)

SAFE_EXAMPLE_NAMES = {
    ".env.example",
    ".env.production.example",
    "Pulumi.dev.yaml.example",
}


def git_tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )

    names = result.stdout.decode(
        "utf-8",
        errors="ignore",
    ).split("\0")

    paths: list[Path] = []

    for name in names:
        if not name:
            continue

        path = ROOT / name

        if not path.is_file():
            continue

        if any(part in SKIP_PARTS for part in path.parts):
            continue

        if (
            path.suffix.lower() not in TEXT_SUFFIXES
            and path.name not in {
                ".env",
                ".env.example",
            }
        ):
            continue

        paths.append(path)

    return paths


def is_safe_value(value: str) -> bool:
    normalized = value.strip().lower()

    return any(
        marker.lower() in normalized
        for marker in SAFE_VALUE_MARKERS
    )


def is_safe_line(line: str) -> bool:
    normalized = line.strip().lower()

    return any(
        marker.lower() in normalized
        for marker in SAFE_LINE_MARKERS
    )


def find_literal_assignment(
    path: Path,
    line: str,
) -> str | None:
    suffix = path.suffix.lower()

    if suffix in {".yml", ".yaml"}:
        match = YAML_ASSIGNMENT_PATTERN.search(line)

    elif suffix == ".env" or path.name == ".env":
        match = ENV_ASSIGNMENT_PATTERN.search(line)

    else:
        match = ASSIGNMENT_PATTERN.search(line)

    if not match:
        return None

    return match.group("value").strip()


def scan_file(path: Path) -> list[str]:
    relative = path.relative_to(ROOT)

    try:
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except OSError:
        return []

    findings: list[str] = []

    if PRIVATE_KEY_PATTERN.search(text):
        findings.append(
            f"{relative}: private key material"
        )

    for pattern in KNOWN_SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(
                f"{relative}: token/credential pattern"
            )

    for line_number, line in enumerate(
        text.splitlines(),
        start=1,
    ):
        if is_safe_line(line):
            continue

        value = find_literal_assignment(
            path,
            line,
        )

        if value is None:
            continue

        if is_safe_value(value):
            continue

        if path.name in SAFE_EXAMPLE_NAMES:
            continue

        findings.append(
            f"{relative}:{line_number}"
        )

    return findings


def scan() -> list[str]:
    findings: list[str] = []

    try:
        tracked = git_tracked_files()
    except subprocess.CalledProcessError as exc:
        print(
            f"Unable to read Git tracked files: {exc}",
            file=sys.stderr,
        )
        return ["git ls-files failed"]

    for path in tracked:
        findings.extend(scan_file(path))

    return sorted(set(findings))


def main() -> int:
    matches = scan()

    if matches:
        print("Potential committed secrets detected:")
        print()

        for match in matches:
            print(f" - {match}")

        return 1

    print("[PASS] No obvious committed secrets detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())