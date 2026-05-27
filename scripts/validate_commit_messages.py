from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


CONVENTIONAL_PATTERN = re.compile(
    r"^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)"
    r"(\([a-z0-9._/-]+\))?(!)?: [^\s].+$"
)
ALLOWED_PREFIXES = ("Merge ", "Revert ")


def _is_valid_subject(subject: str) -> bool:
    normalized = subject.strip()

    if not normalized:
        return False

    if normalized.startswith(ALLOWED_PREFIXES):
        return True

    return bool(CONVENTIONAL_PATTERN.fullmatch(normalized))


def _read_subject_from_message_file(path: Path) -> str:
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return ""


def _iter_subjects_from_range(rev_range: str) -> list[tuple[str, str]]:
    completed = subprocess.run(
        ["git", "log", "--format=%H%x00%s", rev_range],
        capture_output=True,
        text=True,
        check=True,
    )

    commits: list[tuple[str, str]] = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        commit_hash, subject = line.split("\x00", 1)
        commits.append((commit_hash, subject.strip()))
    return commits


def _print_examples() -> None:
    print("Formato esperado: tipo(escopo-opcional): descricao")
    print("Exemplos validos:")
    print("  feat(monorepo): adiciona pipeline unificado")
    print("  fix(deploy): corrige reinicio do servico da api")
    print("  build(release): v0.1.0")


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida Conventional Commits do repositorio.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--message-file", type=Path, help="Arquivo de mensagem fornecido pelo hook commit-msg.")
    group.add_argument("--rev-range", help="Range git no formato base..head para validar multiplos commits.")
    args = parser.parse_args()

    invalid: list[tuple[str, str]] = []

    try:
        if args.message_file:
            subject = _read_subject_from_message_file(args.message_file)
            if not _is_valid_subject(subject):
                invalid.append(("LOCAL", subject))
        else:
            for commit_hash, subject in _iter_subjects_from_range(args.rev_range):
                if not _is_valid_subject(subject):
                    invalid.append((commit_hash[:7], subject))
    except subprocess.CalledProcessError as exc:
        print(exc.stderr.strip() or str(exc), file=sys.stderr)
        return 1

    if not invalid:
        print("Commit message policy OK")
        return 0

    print("Foram encontradas mensagens de commit fora do padrao.", file=sys.stderr)
    for commit_ref, subject in invalid:
        print(f"- {commit_ref}: {subject or '<vazia>'}", file=sys.stderr)
    _print_examples()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())