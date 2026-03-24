#!/usr/bin/env python3
"""Clone repositories and run CK metrics collection."""

from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
from pathlib import Path


EXPECTED_JAR_GLOB = "*-jar-with-dependencies.jar"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run clone + CK pipeline")
    parser.add_argument("--repos-csv", required=True, help="CSV with collected repositories")
    parser.add_argument("--sample-size", type=int, default=1, help="How many repos to process")
    parser.add_argument("--workspace", required=True, help="Working directory for clones")
    parser.add_argument("--output", required=True, help="Output directory for CK files")
    parser.add_argument("--ck-jar", default="", help="Path to CK standalone jar")
    parser.add_argument("--ck-dir", default="enunciado2/tools/ck", help="Path to CK repository")
    parser.add_argument("--use-jars", default="true", choices=["true", "false"])
    parser.add_argument("--max-files-per-partition", default="0")
    parser.add_argument("--variables-and-fields", default="false", choices=["true", "false"])
    parser.add_argument("--timeout-minutes", type=int, default=30)
    return parser.parse_args()


def run(cmd: list[str], cwd: Path | None = None, timeout_seconds: int | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=True,
        timeout=timeout_seconds,
    )


def resolve_ck_jar(ck_jar_arg: str, ck_dir_arg: str) -> Path:
    if ck_jar_arg:
        jar = Path(ck_jar_arg).resolve()
        if not jar.exists():
            raise FileNotFoundError(f"CK JAR not found: {jar}")
        return jar

    ck_dir = Path(ck_dir_arg).resolve()
    jars = sorted((ck_dir / "target").glob(EXPECTED_JAR_GLOB))
    if not jars:
        raise FileNotFoundError(
            "No CK JAR found. Build CK first with setup_ck.py --build or pass --ck-jar."
        )
    return jars[-1]


def read_repos(path: Path) -> list[dict[str, str]]:
    repos: list[dict[str, str]] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            owner = row.get("owner", "").strip()
            repo = row.get("repo", "").strip()
            if owner and repo:
                repos.append(row)
    return repos


def clone_repo(repo_url: str, target_dir: Path) -> None:
    if target_dir.exists() and (target_dir / ".git").exists():
        run(["git", "fetch", "--all", "--tags", "--prune"], cwd=target_dir)
        run(["git", "pull", "--ff-only"], cwd=target_dir)
        return

    if target_dir.exists():
        shutil.rmtree(target_dir)

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    run(["git", "clone", "--depth", "1", repo_url, str(target_dir)])


def run_ck(
    ck_jar: Path,
    project_dir: Path,
    output_dir: Path,
    use_jars: str,
    max_files: str,
    variables_and_fields: str,
    timeout_minutes: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "java",
        "-jar",
        str(ck_jar),
        str(project_dir),
        use_jars,
        max_files,
        variables_and_fields,
        str(output_dir),
    ]
    run(cmd, timeout_seconds=timeout_minutes * 60)


def write_run_log(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["owner", "repo", "status", "message"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    args = parse_args()
    repos_csv = Path(args.repos_csv).resolve()
    workspace = Path(args.workspace).resolve()
    output_root = Path(args.output).resolve()

    if not repos_csv.exists():
        raise FileNotFoundError(f"Repos CSV not found: {repos_csv}")

    ck_jar = resolve_ck_jar(args.ck_jar, args.ck_dir)
    repos = read_repos(repos_csv)
    if not repos:
        raise RuntimeError("No repositories found in CSV.")

    run_log: list[dict[str, str]] = []
    selected = repos[: max(1, args.sample_size)]

    for row in selected:
        owner = row["owner"]
        repo = row["repo"]
        full_name = f"{owner}/{repo}"
        clone_url = f"https://github.com/{full_name}.git"

        repo_dir = workspace / full_name.replace("/", "__")
        repo_output = output_root / full_name.replace("/", "__")

        try:
            print(f"Processing {full_name}")
            clone_repo(clone_url, repo_dir)
            run_ck(
                ck_jar=ck_jar,
                project_dir=repo_dir,
                output_dir=repo_output,
                use_jars=args.use_jars,
                max_files=args.max_files_per_partition,
                variables_and_fields=args.variables_and_fields,
                timeout_minutes=args.timeout_minutes,
            )
            run_log.append({"owner": owner, "repo": repo, "status": "ok", "message": ""})
        except Exception as exc:  # noqa: BLE001
            run_log.append({
                "owner": owner,
                "repo": repo,
                "status": "error",
                "message": str(exc),
            })

    write_run_log(output_root / "pipeline_run_log.csv", run_log)
    failures = [r for r in run_log if r["status"] != "ok"]
    print(f"Processed: {len(run_log)} | Failed: {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
