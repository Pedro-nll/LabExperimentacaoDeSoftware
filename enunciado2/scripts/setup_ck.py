#!/usr/bin/env python3
"""Bootstrap CK tool by cloning and building its standalone JAR."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

CK_REPO_URL = "https://github.com/mauricioaniche/ck.git"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Setup CK tool")
    parser.add_argument("--ck-dir", required=True, help="Directory where CK repo should live")
    parser.add_argument("--build", action="store_true", help="Build CK JAR after clone/update")
    return parser.parse_args()


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def ensure_ck_repo(ck_dir: Path) -> None:
    if ck_dir.exists() and (ck_dir / ".git").exists():
        run(["git", "pull", "--ff-only"], cwd=ck_dir)
        return

    ck_dir.parent.mkdir(parents=True, exist_ok=True)
    run(["git", "clone", CK_REPO_URL, str(ck_dir)])


def build_ck(ck_dir: Path) -> None:
    mvnw = ck_dir / "mvnw"
    if mvnw.exists():
        run(["chmod", "+x", str(mvnw)], cwd=ck_dir)
        run([str(mvnw), "clean", "compile", "package", "-DskipTests"], cwd=ck_dir)
        return

    if shutil.which("mvn") is None:
        raise RuntimeError("Maven not found and mvnw is unavailable in CK directory")

    run(["mvn", "clean", "compile", "package", "-DskipTests"], cwd=ck_dir)


def find_jar(ck_dir: Path) -> Path:
    jars = sorted((ck_dir / "target").glob("*-jar-with-dependencies.jar"))
    if not jars:
        raise RuntimeError("Could not find CK standalone JAR in target/")
    return jars[-1]


def main() -> int:
    args = parse_args()
    ck_dir = Path(args.ck_dir).resolve()

    ensure_ck_repo(ck_dir)
    if args.build:
        build_ck(ck_dir)

    try:
        jar = find_jar(ck_dir)
        print(f"CK JAR: {jar}")
    except RuntimeError as exc:
        print(f"Info: {exc}")
        if args.build:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
