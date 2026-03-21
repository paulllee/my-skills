import shutil
from pathlib import Path

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"

script_dir = Path(__file__).parent.resolve()
home = Path.home()

destinations = [
    home / ".claude" / "skills"
]

for dest in destinations:
    dest.mkdir(parents=True, exist_ok=True)
    print(f"\n{BOLD}{dest}{RESET}")
    for skill in sorted((script_dir / "skills").iterdir()):
        if not skill.is_dir():
            continue
        target = dest / skill.name
        if target.exists():
            shutil.rmtree(target)
            print(f"  {YELLOW}Updating{RESET} {skill.name}")
        else:
            print(f"  {GREEN}Installing{RESET} {skill.name}")
        shutil.copytree(skill, target)

print("\nSkills installed")
