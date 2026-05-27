from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "_version.py"
CHANGELOG_FILE = ROOT / "CHANGELOG.md"
VERSION_PATTERN = re.compile(r'__version__\s*=\s*"(?P<version>\d+\.\d+\.\d+)"')
CONVENTIONAL_PATTERN = re.compile(
    r"^(?P<type>build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)"
    r"(\((?P<scope>[a-z0-9._/-]+)\))?(?P<breaking>!)?: (?P<description>[^\s].+)$"
)
RELEASE_PREFIX = "build(release):"
SECTION_BY_TYPE = {
    "feat": "Added",
    "fix": "Fixed",
    "build": "Changed",
    "chore": "Changed",
    "ci": "Changed",
    "docs": "Changed",
    "perf": "Changed",
    "refactor": "Changed",
    "revert": "Changed",
    "style": "Changed",
    "test": "Changed",
}
SECTION_ORDER = ("Added", "Fixed", "Changed")


def _run_git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def _read_version() -> str:
    match = VERSION_PATTERN.search(VERSION_FILE.read_text(encoding="utf-8"))
    if not match:
        raise RuntimeError("Nao foi possivel localizar __version__ em _version.py")
    return match.group("version")


def _parse_version(version: str) -> tuple[int, int, int]:
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def _format_version(version: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version)


def _latest_tag() -> str | None:
    output = _run_git("tag", "--list", "v*.*.*", "--sort=-v:refname")
    if not output:
        return None
    return output.splitlines()[0].strip()


def _commit_entries(latest_tag: str | None) -> list[dict[str, str]]:
    args = ["log", "--format=%H%x00%s%x00%b"]
    if latest_tag:
        args.append(f"{latest_tag}..HEAD")

    output = _run_git(*args)
    entries: list[dict[str, str]] = []

    for line in output.splitlines():
        if not line.strip():
            continue
        commit_hash, subject, body = line.split("\x00", 2)
        entries.append(
            {
                "hash": commit_hash,
                "subject": subject.strip(),
                "body": body.strip(),
            }
        )

    return entries


def _releasable_entries(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    filtered = [entry for entry in entries if not entry["subject"].startswith(RELEASE_PREFIX)]
    non_merge = [entry for entry in filtered if not entry["subject"].startswith("Merge ")]
    return non_merge or filtered


def _detect_bump(entries: list[dict[str, str]]) -> str:
    bump = "patch"

    for entry in entries:
        match = CONVENTIONAL_PATTERN.match(entry["subject"])
        body_upper = entry["body"].upper()

        if (match and match.group("breaking")) or "BREAKING CHANGE" in body_upper:
            return "major"

        if match and match.group("type") == "feat":
            bump = "minor"

    return bump


def _next_version(base_version: str, bump: str) -> str:
    major, minor, patch = _parse_version(base_version)

    if bump == "major":
        return _format_version((major + 1, 0, 0))
    if bump == "minor":
        return _format_version((major, minor + 1, 0))
    return _format_version((major, minor, patch + 1))


def _display_subject(entry: dict[str, str]) -> tuple[str, str]:
    match = CONVENTIONAL_PATTERN.match(entry["subject"])
    if not match:
        return "Changed", entry["subject"]

    section = SECTION_BY_TYPE.get(match.group("type"), "Changed")
    scope = match.group("scope")
    description = match.group("description")

    if scope:
        return section, f"{scope}: {description}"
    return section, description


def _render_changelog_section(version: str, entries: list[dict[str, str]]) -> str:
    today = dt.date.today().isoformat()
    grouped: dict[str, list[str]] = {section: [] for section in SECTION_ORDER}

    for entry in entries:
        section, message = _display_subject(entry)
        grouped.setdefault(section, []).append(message)

    lines = [f"## [{version}] - {today}", ""]
    populated_sections = [section for section in SECTION_ORDER if grouped.get(section)]

    if not populated_sections:
        populated_sections = ["Changed"]
        grouped["Changed"] = ["Atualizacao automatica de release para o estado atual da main."]

    for section in populated_sections:
        lines.append(f"### {section}")
        lines.append("")
        for message in grouped[section]:
            lines.append(f"- {message}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _ensure_changelog_file() -> None:
    if CHANGELOG_FILE.exists():
        return

    CHANGELOG_FILE.write_text(
        "# Changelog\n\n"
        "Todas as mudancas relevantes deste projeto devem ser registradas aqui.\n\n"
        "## [Unreleased]\n\n"
        "### Pending\n\n"
        "- Nenhuma alteracao registrada apos a release mais recente.\n",
        encoding="utf-8",
    )


def _update_changelog(version: str, entries: list[dict[str, str]]) -> None:
    _ensure_changelog_file()
    current = CHANGELOG_FILE.read_text(encoding="utf-8")
    new_section = _render_changelog_section(version, entries)

    marker = "## [Unreleased]"
    if marker not in current:
        raise RuntimeError("CHANGELOG.md nao contem a secao [Unreleased].")

    marker_index = current.index(marker)
    next_header_index = current.find("\n## [", marker_index + len(marker))

    if next_header_index == -1:
        updated = current.rstrip() + "\n\n" + new_section
    else:
        prefix = current[:next_header_index].rstrip()
        suffix = current[next_header_index:].lstrip("\n")
        updated = prefix + "\n\n" + new_section + "\n" + suffix

    CHANGELOG_FILE.write_text(updated.rstrip() + "\n", encoding="utf-8")


def _write_version(version: str) -> None:
    current = VERSION_FILE.read_text(encoding="utf-8")
    updated = VERSION_PATTERN.sub(f'__version__ = "{version}"', current, count=1)
    VERSION_FILE.write_text(updated, encoding="utf-8")


def _write_output(path: Path | None, created: bool, version: str, bump: str, tag: str) -> None:
    if path is None:
        return

    lines = [
        f"created={'true' if created else 'false'}",
        f"version={version}",
        f"bump={bump}",
        f"tag={tag}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepara os arquivos de release do monorepo.")
    parser.add_argument("--github-output", type=Path, help="Arquivo GITHUB_OUTPUT para expor resultados ao workflow.")
    args = parser.parse_args()

    current_version = _read_version()
    latest_tag = _latest_tag()
    latest_tag_version = latest_tag[1:] if latest_tag else current_version
    base_version = max(current_version, latest_tag_version, key=_parse_version)

    entries = _releasable_entries(_commit_entries(latest_tag))
    if not entries:
        tag = f"v{base_version}"
        _write_output(args.github_output, False, base_version, "none", tag)
        print("Nenhuma alteracao nova para release.")
        return 0

    bump = _detect_bump(entries)
    next_version = _next_version(base_version, bump)
    _write_version(next_version)
    _update_changelog(next_version, entries)

    tag = f"v{next_version}"
    _write_output(args.github_output, True, next_version, bump, tag)
    print(f"Release preparada: {tag} ({bump})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())