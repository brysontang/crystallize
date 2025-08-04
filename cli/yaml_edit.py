from __future__ import annotations

from pathlib import Path


def find_treatment_line(path: Path, name: str) -> int:
    try:
        lines = path.read_text().splitlines()
    except Exception:
        return 1
    in_block = False
    indent = ""
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("treatments:"):
            in_block = True
            indent = line[: len(line) - len(stripped)] + "  "
            continue
        if in_block:
            if stripped and not line.startswith(indent):
                break
            if stripped.startswith(f"{name}:"):
                return i
    return 1


def ensure_new_treatment_placeholder(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    treat_idx = None
    indent = ""
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("treatments:"):
            treat_idx = i
            indent = line[: len(line) - len(stripped)] + "  "
            break
    if treat_idx is None:
        lines.append("treatments:")
        treat_idx = len(lines) - 1
    insert = treat_idx + 1
    for i in range(treat_idx + 1, len(lines)):
        line = lines[i]
        if line.strip() and not line.startswith(indent):
            insert = i
            break
        insert = i + 1
    placeholder = f"{indent}# new treatment"
    if insert >= len(lines) or lines[insert].strip() != "# new treatment":
        lines.insert(insert, placeholder)
    newline = "\n" if text.endswith("\n") else ""
    path.write_text("\n".join(lines) + newline, encoding="utf-8")
    return insert + 1


def find_treatment_apply_line(path: Path, name: str, key: str) -> int:
    try:
        lines = path.read_text().splitlines()
    except Exception:
        return 1
    in_block = False
    block_indent = ""
    t_indent = ""
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("treatments:"):
            in_block = True
            block_indent = line[: len(line) - len(stripped)] + "  "
            continue
        if in_block and t_indent:
            if stripped and not line.startswith(t_indent):
                break
            if stripped.startswith(f"{key}:"):
                return i
            continue
        if in_block:
            if stripped and not line.startswith(block_indent):
                break
            if stripped.startswith(f"{name}:"):
                t_indent = line[: len(line) - len(stripped)] + "  "
    return 1
