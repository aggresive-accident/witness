#!/usr/bin/env python3
"""
witness - a quiet observer of changes
"""

import os
import sys
import time
import hashlib
from pathlib import Path
from datetime import datetime

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


def scan_directory(path):
    """capture the current state of a directory"""
    state = {}
    path = Path(path)

    if not path.exists():
        return state

    for item in path.rglob('*'):
        if item.is_file():
            rel_path = str(item.relative_to(path))
            # skip hidden files and common noise
            if any(part.startswith('.') for part in item.parts):
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


def witness_once(path):
    """take a single snapshot and report"""
    state = scan_directory(path)

    if not state:
        print("the directory is empty, or hidden")
        return state

    print(f"i see {len(state)} files")
    for filepath in sorted(state.keys())[:5]:
        print(f"  {filepath}")
    if len(state) > 5:
        print(f"  ... and {len(state) - 5} more")

    return state


def witness_loop(path, interval=2.0):
    """watch continuously, reporting changes"""
    path = Path(path).resolve()

    print(f"witnessing: {path}")
    print(f"interval: {interval}s")
    print()

    state = scan_directory(path)
    print(f"initial state: {len(state)} files")
    print("waiting...")
    print()

    try:
        while True:
            time.sleep(interval)
            new_state = scan_directory(path)
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
        print("usage: witness.py <directory> [--loop] [--interval N]")
        print()
        print("options:")
        print("  --loop       watch continuously for changes")
        print("  --interval N seconds between checks (default: 2)")
        sys.exit(1)

    path = sys.argv[1]
    loop_mode = "--loop" in sys.argv

    interval = 2.0
    if "--interval" in sys.argv:
        try:
            idx = sys.argv.index("--interval")
            interval = float(sys.argv[idx + 1])
        except (IndexError, ValueError):
            pass

    if not Path(path).exists():
        print(f"cannot witness what does not exist: {path}")
        sys.exit(1)

    if loop_mode:
        witness_loop(path, interval)
    else:
        witness_once(path)


if __name__ == "__main__":
    main()
