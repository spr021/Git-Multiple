#!/usr/bin/env python3
"""Build a dependency-free, cross-platform Python zip application."""

import shutil
import tempfile
import zipapp
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def main() -> None:
    DIST.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        source = Path(temporary)
        shutil.copytree(ROOT / "git_multiple", source / "git_multiple")
        (source / "__main__.py").write_text(
            "from git_multiple.cli import main\nraise SystemExit(main())\n",
            encoding="utf-8",
        )
        zipapp.create_archive(
            source,
            DIST / "git-multiple.pyz",
            interpreter="/usr/bin/env python3",
            compressed=True,
        )
    print(DIST / "git-multiple.pyz")


if __name__ == "__main__":
    main()
