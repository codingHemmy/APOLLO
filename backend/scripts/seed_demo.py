from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

KEYWORDS = ["Durchmesser 1", "Durchmesser 2", "Tiefe", "Breite"]


def generate_dat_content(keyword: str, value: float) -> str:
    lines = [
        "HEADER: RoboDrill",
        "Machine running",
        f"{keyword}: {value:.4f} mm",
        "END",
    ]
    return "\n".join(lines)


def seed_demo(root: Path, days: int = 10, files_per_day: int = 5) -> None:
    if root.exists():
        print(f"Cleaning existing demo data at {root}")
        for item in root.rglob("*"):
            if item.is_file():
                item.unlink()
        for folder in sorted(root.glob("**/*"), reverse=True):
            if folder.is_dir():
                folder.rmdir()
    root.mkdir(parents=True, exist_ok=True)
    start_date = datetime.now() - timedelta(days=days)
    for machine in range(1, 4):
        machine_root = root / "rd" / f"{machine:03d}" / "ftp"
        machine_root.mkdir(parents=True, exist_ok=True)
        for day in range(days):
            day_date = start_date + timedelta(days=day)
            folder = machine_root / day_date.strftime("%d-%m-%y")
            folder.mkdir(parents=True, exist_ok=True)
            for index in range(files_per_day):
                keyword = random.choice(KEYWORDS)
                value = random.uniform(0.1, 10.0)
                filename = f"LOG_{index:03d}.DAT"
                content = generate_dat_content(keyword, value)
                (folder / filename).write_text(content, encoding="utf-8")
    print(f"Seeded demo FTP structure at {root}")


if __name__ == "__main__":
    seed_demo(Path("demo_ftp"))
