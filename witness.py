#!/usr/bin/env python3
"""
witness - a quiet observer of changes
"""

import json
import os
import subprocess
import sys
import time
import hashlib
from pathlib import Path
from datetime import datetime

HOME = Path.home()
WITNESS_STATE_FILE = HOME / ".witness_last_scan.json"

# how we describe what we see
OBSERVATIONS = {
    "created": [
        "something new appeared:",
        "a new presence:",
        "came into being:",
        "emerged:",
        "arrived quietly:",
    ],
    "modified": [
        "changed:",
        "was touched:",
        "shifted:",
        "became different:",
        "transformed:",
    ],
    "deleted": [
        "departed:",
        "is gone now:",
        "was here, then wasn't:",
        "left no trace:",
        "faded:",
    ],
    "unchanged": [
        "remains:",
        "persists:",
        "holds still:",
        "waits:",
        "continues:",
    ],
}


def hash_file(path):
    """get a fingerprint of a file's contents"""
    try:
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()[:8]
    except (IOError, OSError):
        return None


def get_content_preview(path, lines=3):
    """get first few lines of a text file"""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            preview = []
            for i, line in enumerate(f):
                if i >= lines:
                    break
                preview.append(line.rstrip()[:60])
            return preview
    except:
        return None


def get_content_tail(path, lines=3):
    """get last few lines of a text file"""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
            tail = all_lines[-lines:] if len(all_lines) >= lines else all_lines
            return [l.rstrip()[:60] for l in tail]
    except:
        return None


def get_git_blame(filepath: Path, lines: int = 3) -> list:
    """get recent git blame info for a file"""
    try:
        # find git root
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=filepath.parent,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return None

        git_root = Path(result.stdout.strip())
        rel_path = filepath.relative_to(git_root)

        # get blame with timestamps
        result = subprocess.run(
            ["git", "blame", "--line-porcelain", str(rel_path)],
            cwd=git_root,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return None

        # parse blame output
        blame_entries = []
        current_entry = {}

        for line in result.stdout.split("\n"):
            if line.startswith("author "):
                current_entry["author"] = line[7:]
            elif line.startswith("author-time "):
                ts = int(line[12:])
                current_entry["time"] = datetime.fromtimestamp(ts)
            elif line.startswith("summary "):
                current_entry["summary"] = line[8:][:40]
            elif line.startswith("\t"):
                # content line - entry complete
                if current_entry:
                    blame_entries.append(current_entry.copy())
                current_entry = {}

        if not blame_entries:
            return None

        # sort by time and return most recent
        blame_entries.sort(key=lambda x: x.get("time", datetime.min), reverse=True)
        seen = set()
        unique = []
        for entry in blame_entries:
            key = (entry.get("author"), entry.get("summary"))
            if key not in seen:
                seen.add(key)
                unique.append(entry)
                if len(unique) >= lines:
                    break

        return unique

    except Exception:
        return None


def scan_directory(path, recursive=True, max_depth=None):
    """capture the current state of a directory"""
    state = {}
    path = Path(path)

    if not path.exists():
        return state

    if recursive:
        items = path.rglob('*')
    else:
        items = path.glob('*')

    for item in items:
        if item.is_file():
            rel_path = str(item.relative_to(path))

            # skip hidden files and common noise
            if any(part.startswith('.') for part in item.parts):
                continue

            # check depth if specified
            if max_depth is not None:
                depth = len(item.relative_to(path).parts)
                if depth > max_depth:
                    continue

            state[rel_path] = {
                'mtime': item.stat().st_mtime,
                'size': item.stat().st_size,
                'hash': hash_file(item),
            }

    return state


def describe_change(change_type, filepath):
    """generate a poetic observation"""
    import random
    phrases = OBSERVATIONS.get(change_type, OBSERVATIONS["unchanged"])
    return f"  {random.choice(phrases)} {filepath}"


def compare_states(before, after):
    """find what changed between two states"""
    changes = []

    all_files = set(before.keys()) | set(after.keys())

    for filepath in sorted(all_files):
        if filepath not in before:
            changes.append(("created", filepath))
        elif filepath not in after:
            changes.append(("deleted", filepath))
        elif before[filepath]['hash'] != after[filepath]['hash']:
            changes.append(("modified", filepath))

    return changes


def save_scan(path: str, state: dict):
    """save scan state for later comparison"""
    data = {
        "path": str(path),
        "timestamp": datetime.now().isoformat(),
        "state": state,
    }
    WITNESS_STATE_FILE.write_text(json.dumps(data, indent=2))


def load_previous_scan(path: str) -> dict | None:
    """load previous scan for this path"""
    if not WITNESS_STATE_FILE.exists():
        return None

    try:
        data = json.loads(WITNESS_STATE_FILE.read_text())
        if data.get("path") == str(path):
            return data
    except:
        pass
    return None


def witness_diff(path, recursive=True, max_depth=None, show_content=False, show_blame=False):
    """compare current state to previous scan"""
    path = Path(path).resolve()
    current = scan_directory(path, recursive, max_depth)
    previous_data = load_previous_scan(str(path))

    if not previous_data:
        print("no previous scan found for this path")
        print("running initial scan...")
        print()
        save_scan(str(path), current)
        print(f"scanned {len(current)} files")
        print("run --diff again to see changes")
        return

    previous = previous_data.get("state", {})
    prev_time = previous_data.get("timestamp", "unknown")[:19]

    print(f"comparing to scan from {prev_time}")
    print()

    changes = compare_states(previous, current)

    if not changes:
        print("  nothing has changed")
    else:
        created = [c for c in changes if c[0] == "created"]
        modified = [c for c in changes if c[0] == "modified"]
        deleted = [c for c in changes if c[0] == "deleted"]

        if created:
            print(f"  NEW ({len(created)}):")
            for _, filepath in created[:10]:
                print(f"    + {filepath}")
                if show_content:
                    full_path = path / filepath
                    preview = get_content_preview(full_path, 2)
                    if preview:
                        for line in preview:
                            print(f"      | {line}")
            if len(created) > 10:
                print(f"    ... and {len(created) - 10} more")
            print()

        if modified:
            print(f"  MODIFIED ({len(modified)}):")
            for _, filepath in modified[:10]:
                print(f"    ~ {filepath}")
                if show_content:
                    full_path = path / filepath
                    # show tail (recent changes often at end)
                    tail = get_content_tail(full_path, 2)
                    if tail:
                        print(f"      (end of file):")
                        for line in tail:
                            print(f"      | {line}")
                if show_blame:
                    full_path = path / filepath
                    blame = get_git_blame(full_path, 2)
                    if blame:
                        print(f"      (recent blame):")
                        for entry in blame:
                            author = entry.get("author", "unknown")[:15]
                            time_str = entry.get("time", datetime.min).strftime("%m-%d %H:%M")
                            summary = entry.get("summary", "")[:30]
                            print(f"      @ {author} ({time_str}): {summary}")
            if len(modified) > 10:
                print(f"    ... and {len(modified) - 10} more")
            print()

        if deleted:
            print(f"  DELETED ({len(deleted)}):")
            for _, filepath in deleted[:10]:
                print(f"    - {filepath}")
            if len(deleted) > 10:
                print(f"    ... and {len(deleted) - 10} more")
            print()

    # update saved state
    save_scan(str(path), current)
    print(f"saved new scan ({len(current)} files)")


def witness_once(path, recursive=True, max_depth=None, save=False):
    """take a single snapshot and report"""
    state = scan_directory(path, recursive, max_depth)

    if not state:
        print("the directory is empty, or hidden")
        return state

    mode = "recursive" if recursive else "flat"
    if max_depth is not None:
        mode = f"depth={max_depth}"
    print(f"i see {len(state)} files ({mode})")
    for filepath in sorted(state.keys())[:5]:
        print(f"  {filepath}")
    if len(state) > 5:
        print(f"  ... and {len(state) - 5} more")

    if save:
        save_scan(str(Path(path).resolve()), state)
        print()
        print("scan saved for future --diff comparison")

    return state


def witness_loop(path, interval=2.0, recursive=True, max_depth=None):
    """watch continuously, reporting changes"""
    path = Path(path).resolve()

    mode = "recursive" if recursive else "flat"
    if max_depth is not None:
        mode = f"depth={max_depth}"

    print(f"witnessing: {path}")
    print(f"mode: {mode}, interval: {interval}s")
    print()

    state = scan_directory(path, recursive, max_depth)
    print(f"initial state: {len(state)} files")
    print("waiting...")
    print()

    try:
        while True:
            time.sleep(interval)
            new_state = scan_directory(path, recursive, max_depth)
            changes = compare_states(state, new_state)

            if changes:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}]")
                for change_type, filepath in changes:
                    print(describe_change(change_type, filepath))
                print()

            state = new_state

    except KeyboardInterrupt:
        print()
        print("the watching ends")
        print(f"final state: {len(state)} files")


def main():
    if len(sys.argv) < 2:
        print("usage: witness.py <directory> [options]")
        print()
        print("options:")
        print("  --loop       watch continuously for changes")
        print("  --interval N seconds between checks (default: 2)")
        print("  --flat       only watch top-level files (no recursion)")
        print("  --depth N    limit recursion depth")
        print("  --diff       compare to previous scan")
        print("  --content    show file content previews (with --diff)")
        print("  --blame      show git blame for modified files (with --diff)")
        print("  --save       save scan for future --diff")
        sys.exit(1)

    path = sys.argv[1]
    loop_mode = "--loop" in sys.argv
    diff_mode = "--diff" in sys.argv
    save_mode = "--save" in sys.argv
    content_mode = "--content" in sys.argv
    blame_mode = "--blame" in sys.argv
    recursive = "--flat" not in sys.argv

    interval = 2.0
    if "--interval" in sys.argv:
        try:
            idx = sys.argv.index("--interval")
            interval = float(sys.argv[idx + 1])
        except (IndexError, ValueError):
            pass

    max_depth = None
    if "--depth" in sys.argv:
        try:
            idx = sys.argv.index("--depth")
            max_depth = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            pass

    if not Path(path).exists():
        print(f"cannot witness what does not exist: {path}")
        sys.exit(1)

    if diff_mode:
        witness_diff(path, recursive, max_depth, show_content=content_mode, show_blame=blame_mode)
    elif loop_mode:
        witness_loop(path, interval, recursive, max_depth)
    else:
        witness_once(path, recursive, max_depth, save=save_mode)


if __name__ == "__main__":
    main()

