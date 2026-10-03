#!/usr/bin/env python3
"""Scan the Git index for credentials and prohibited generated/private files."""
import re
import subprocess
import sys

# Prefixes must begin a token, including after quotes, assignment or URL separators.
# Otherwise a path word such as task-draft-v21-compatible contains a false sk- match.
TOKEN_START = rb"(?<![A-Za-z0-9_-])"
PATTERNS = [
    re.compile(TOKEN_START + rb"sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}"),
    re.compile(TOKEN_START + rb"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(TOKEN_START + rb"github_pat_[A-Za-z0-9_]{30,}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
BLOCKED_EXTENSIONS = (".gguf", ".safetensors", ".onnx", ".apk", ".aab", ".mp4", ".jks", ".keystore")
BLOCKED_PREFIXES = ("research/", "models/", "datasets/private/", "artifacts/")


def main():
    names = subprocess.check_output(["git", "ls-files", "-z"]).split(b"\0")
    failures = []
    for raw_name in names:
        if not raw_name:
            continue
        name = raw_name.decode()
        parts = name.split("/")
        env = any(p == ".env" or (p.startswith(".env.") and p != ".env.example") for p in parts)
        blocked = name.endswith(BLOCKED_EXTENSIONS) or name.startswith(BLOCKED_PREFIXES)
        if env or (blocked and name != "artifacts/.gitkeep"):
            failures.append((name, "prohibited file"))
            continue
        # Scan exactly what will be committed, including binary blobs.
        payload = subprocess.check_output(["git", "show", f":{name}"])
        if any(pattern.search(payload) for pattern in PATTERNS):
            failures.append((name, "possible secret"))
    for name, reason in failures:
        print(f"FAIL: {name}: {reason}", file=sys.stderr)
    if failures:
        print("No secret values printed. Remove these files/values from the index.", file=sys.stderr)
        return 1
    print("Git index passed credential and prohibited-file checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
