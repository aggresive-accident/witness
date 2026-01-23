#!/usr/bin/env python3
"""
dormant - alerts when files haven't changed in a while

the opposite of witness
instead of watching for change
watches for stillness

perhaps stillness is a sign
that something needs attention
or perhaps it's peaceful

either way, dormant notices
"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

HOME = Path.home()
WORKSPACE = HOME / "workspace"


def file_age(filepath: Path) -> timedelta | None:
    """get the age of a file since last modification"""
    try:
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
        return datetime.now() - mtime
    except:
        return None


def format_age(age: timedelta) -> str:
    """format age in human readable form"""
    total_seconds = age.total_seconds()

    if total_seconds < 60:
        return f"{int(total_seconds)} seconds"
    elif total_seconds < 3600:
        return f"{int(total_seconds / 60)} minutes"
    elif total_seconds < 86400:
        return f"{total_seconds / 3600:.1f} hours"
    else:
        return f"{total_seconds / 86400:.1f} days"


def find_dormant_files(directory: Path, threshold_hours: float = 24.0) -> list:
    """find files older than threshold"""
    threshold = timedelta(hours=threshold_hours)
    dormant = []

    for py_file in directory.rglob("*.py"):
        if ".git" in str(py_file):
            continue

        age = file_age(py_file)
        if age and age > threshold:
            dormant.append({
                "path": py_file,
                "age": age,
                "age_str": format_age(age),
            })

    # sort by age, oldest first
    dormant.sort(key=lambda x: x["age"], reverse=True)
    return dormant


def find_dormant_projects(threshold_hours: float = 24.0) -> dict:
    """find dormant files in all projects"""
    all_dormant = {}

    for project_dir in WORKSPACE.iterdir():
        if project_dir.is_dir() and not project_dir.name.startswith("."):
            dormant = find_dormant_files(project_dir, threshold_hours)
            if dormant:
                all_dormant[project_dir.name] = dormant

    return all_dormant


def project_last_activity(project_dir: Path) -> timedelta | None:
    """get the most recent file modification in a project"""
    newest = None

    for py_file in project_dir.rglob("*.py"):
        if ".git" in str(py_file):
            continue

        age = file_age(py_file)
        if age is not None:
            if newest is None or age < newest:
                newest = age

    return newest


def rank_projects_by_activity() -> list:
    """rank all projects by most recent activity"""
    projects = []

    for project_dir in WORKSPACE.iterdir():
        if project_dir.is_dir() and not project_dir.name.startswith("."):
            last_activity = project_last_activity(project_dir)
            if last_activity:
                projects.append({
                    "name": project_dir.name,
                    "last_activity": last_activity,
                    "last_activity_str": format_age(last_activity),
                })

    # sort by last activity (most active first)
    projects.sort(key=lambda x: x["last_activity"])
    return projects


def print_dormant_report(threshold_hours: float = 24.0):
    """print report of dormant files"""
    print("=" * 60)
    print(" DORMANT FILES REPORT")
    print(f" Threshold: {threshold_hours} hours")
    print("=" * 60)
    print()

    all_dormant = find_dormant_projects(threshold_hours)

    if not all_dormant:
        print(f"No files older than {threshold_hours} hours found.")
        print("Everything has been touched recently.")
        return

    total_dormant = 0

    for project, files in sorted(all_dormant.items()):
        print(f"[{project}] {len(files)} dormant files")
        for f in files[:5]:  # show top 5 oldest
            rel_path = f["path"].relative_to(WORKSPACE / project)
            print(f"  {rel_path}: {f['age_str']} ago")
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more")
        print()
        total_dormant += len(files)

    print("-" * 60)
    print(f"TOTAL: {total_dormant} dormant files across {len(all_dormant)} projects")


def print_activity_report():
    """print report ranking projects by activity"""
    print("=" * 60)
    print(" PROJECT ACTIVITY RANKING")
    print("=" * 60)
    print()

    projects = rank_projects_by_activity()

    if not projects:
        print("No projects found.")
        return

    for i, proj in enumerate(projects, 1):
        print(f"  {i}. {proj['name']:20} last active: {proj['last_activity_str']} ago")

    print()

    # identify concerns
    threshold = timedelta(hours=24)
    stale = [p for p in projects if p["last_activity"] > threshold]

    if stale:
        print("-" * 60)
        print(f"STALE PROJECTS ({len(stale)} haven't been touched in 24+ hours):")
        for p in stale:
            print(f"  - {p['name']}")


def watch_for_dormancy(threshold_hours: float = 1.0, interval: float = 60.0):
    """continuously watch for files becoming dormant"""
    print(f"Watching for files dormant > {threshold_hours} hours")
    print(f"Checking every {interval} seconds")
    print("Press Ctrl+C to stop")
    print()

    previous_dormant = set()

    try:
        while True:
            all_dormant = find_dormant_projects(threshold_hours)
            current_dormant = set()

            for project, files in all_dormant.items():
                for f in files:
                    current_dormant.add(str(f["path"]))

            # find newly dormant files
            newly_dormant = current_dormant - previous_dormant

            if newly_dormant:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] {len(newly_dormant)} files became dormant:")
                for path in list(newly_dormant)[:5]:
                    print(f"  {Path(path).relative_to(WORKSPACE)}")
                print()

            previous_dormant = current_dormant
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nWatching stopped.")


def main():
    if len(sys.argv) < 2:
        print_dormant_report()
        print()
        print_activity_report()
        return

    cmd = sys.argv[1]

    if cmd == "--help":
        print("dormant - alerts when files haven't changed in a while")
        print()
        print("usage:")
        print("  dormant.py                    # full report (24h threshold)")
        print("  dormant.py --hours N          # use N hour threshold")
        print("  dormant.py --activity         # rank projects by activity")
        print("  dormant.py --watch [hours]    # watch for dormancy")
        print("  dormant.py --json             # JSON output")
        return

    elif cmd == "--hours":
        hours = float(sys.argv[2]) if len(sys.argv) > 2 else 24.0
        print_dormant_report(hours)

    elif cmd == "--activity":
        print_activity_report()

    elif cmd == "--watch":
        hours = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
        watch_for_dormancy(hours)

    elif cmd == "--json":
        import json
        hours = float(sys.argv[2]) if len(sys.argv) > 2 else 24.0
        all_dormant = find_dormant_projects(hours)
        output = {}
        for project, files in all_dormant.items():
            output[project] = [
                {
                    "file": str(f["path"].relative_to(WORKSPACE / project)),
                    "age_seconds": f["age"].total_seconds(),
                    "age_human": f["age_str"],
                }
                for f in files
            ]
        print(json.dumps(output, indent=2))

    else:
        print(f"unknown command: {cmd}")


if __name__ == "__main__":
    main()
