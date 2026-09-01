from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STYLE_SOURCE = ROOT / "styles" / "simple-english.md"
SKILLS_SOURCE = ROOT / "skills"
SKILL_IGNORES = (".DS_Store", ".pixi", ".pytest_cache", ".ruff_cache", "__pycache__", "*.pyc", "*.pyo")
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RESET = "\033[0m"


def style_body(source: str) -> str:
    if not source.startswith("---\n"):
        return source.strip()
    _, separator, body = source[4:].partition("\n---\n")
    if not separator:
        raise ValueError("style frontmatter is not closed")
    return body.strip()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def install(home: Path) -> None:
    source = STYLE_SOURCE.read_text(encoding="utf-8")
    write_text(home / ".codex" / "AGENTS.md", f"{style_body(source)}\n")
    write_text(home / ".claude" / "output-styles" / "simple-english.md", source)

    settings_path = home / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    settings["outputStyle"] = "simple english"
    write_text(settings_path, json.dumps(settings, indent=2, ensure_ascii=False) + "\n")
    print(f'{GREEN}installed{RESET} "simple english" style')

    for skill_source in sorted(SKILLS_SOURCE.iterdir()):
        if skill_source.is_dir():
            targets = (
                home / ".codex" / "skills" / skill_source.name,
                home / ".claude" / "skills" / skill_source.name,
            )
            deleted_old_skill = False
            for target in targets:
                if target.exists():
                    shutil.rmtree(target)
                    deleted_old_skill = True
            if deleted_old_skill:
                print(f'{YELLOW}deleted{RESET} old "{skill_source.name}" skill')
            for target in targets:
                shutil.copytree(
                    skill_source,
                    target,
                    ignore=shutil.ignore_patterns(*SKILL_IGNORES),
                )
            print(f'{GREEN}installed{RESET} "{skill_source.name}" skill')


if __name__ == "__main__":
    install(Path.home())
