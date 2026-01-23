#!/usr/bin/env python3
"""
diff_witness - shows what changed between two witness runs

when witness scans twice
this shows what shifted
what came and went
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# import witness functions
try:
    from witness import scan_directory, compare_states, hash_file
except ImportError:
    # fallback - define locally
    import hashlib

    def hash_file(filepath: Path) -> str:
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return "error"

    def scan_directory(path: Path) -> dict:
        state = {}
        for item in path.rglob('*'):
            if item.is_file() and '.git' not in str(item):
                try:
                    state[str(item.relative_to(path))] = hash_file(item)
                except:
                    pass
        return state


WITNESS_CACHE = Path.home() / ".witness-cache"


def save_state(name: str, state: dict, path: str):
    """save a witness state"""
    WITNESS_CACHE.mkdir(exist_ok=True)

    data = {
        "name": name,
        "timestamp": datetime.now().isoformat(),
        "path": str(path),
        "state": state,
    }

    filepath = WITNESS_CACHE / f"{name}.json"
    filepath.write_text(json.dumps(data, indent=2))
    return filepath


def load_state(name: str) -> dict | None:
    """load a saved witness state"""
    filepath = WITNESS_CACHE / f"{name}.json"
    if filepath.exists():
        try:
            return json.loads(filepath.read_text())
        except:
            return None
    return None


def list_saved_states() -> list:
    """list all saved states"""
    if not WITNESS_CACHE.exists():
        return []

    states = []
    for f in WITNESS_CACHE.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            states.append({
                "name": f.stem,
                "timestamp": data.get("timestamp"),
                "path": data.get("path"),
                "files": len(data.get("state", {})),
            })
        except:
            pass

    return sorted(states, key=lambda x: x.get("timestamp", ""))


def diff_states(state1: dict, state2: dict) -> dict:
    """compute the difference between two states"""
    s1 = state1.get("state", {})
    s2 = state2.get("state", {})

    files1 = set(s1.keys())
    files2 = set(s2.keys())

    created = files2 - files1
    deleted = files1 - files2
    common = files1 & files2

    modified = []
    for f in common:
        if s1[f] != s2[f]:
            modified.append(f)

    return {
        "state1": {
            "name": state1.get("name"),
            "timestamp": state1.get("timestamp"),
            "files": len(s1),
        },
        "state2": {
            "name": state2.get("name"),
            "timestamp": state2.get("timestamp"),
            "files": len(s2),
        },
        "created": list(created),
        "deleted": list(deleted),
        "modified": modified,
        "unchanged": len(common) - len(modified),
    }


def print_diff(diff: dict):
    """print a diff report"""
    print("=" * 60)
    print(" WITNESS DIFF")
    print("=" * 60)
    print()

    s1 = diff["state1"]
    s2 = diff["state2"]

    print(f"FROM: {s1['name']} ({s1['timestamp']})")
    print(f"  {s1['files']} files")
    print()
    print(f"TO: {s2['name']} ({s2['timestamp']})")
    print(f"  {s2['files']} files")
    print()

    print("-" * 40)
    print()

    created = diff["created"]
    if created:
        print(f"CREATED ({len(created)}):")
        for f in sorted(created)[:10]:
            print(f"  + {f}")
        if len(created) > 10:
            print(f"  ... and {len(created) - 10} more")
        print()

    deleted = diff["deleted"]
    if deleted:
        print(f"DELETED ({len(deleted)}):")
        for f in sorted(deleted)[:10]:
            print(f"  - {f}")
        if len(deleted) > 10:
            print(f"  ... and {len(deleted) - 10} more")
        print()

    modified = diff["modified"]
    if modified:
        print(f"MODIFIED ({len(modified)}):")
        for f in sorted(modified)[:10]:
            print(f"  ~ {f}")
        if len(modified) > 10:
            print(f"  ... and {len(modified) - 10} more")
        print()

    print("-" * 40)
    print(f"SUMMARY: {len(created)} created, {len(deleted)} deleted, {len(modified)} modified, {diff['unchanged']} unchanged")


def witness_and_save(path: str, name: str):
    """scan a directory and save the state"""
    print(f"scanning {path}...")
    state = scan_directory(Path(path))
    filepath = save_state(name, state, path)
    print(f"saved as: {name} ({len(state)} files)")
    print(f"stored at: {filepath}")


def main():
    if len(sys.argv) < 2:
        print("diff_witness - shows what changed between two witness runs")
        print()
        print("usage:")
        print("  diff_witness.py scan <path> <name>  # scan and save state")
        print("  diff_witness.py list                # list saved states")
        print("  diff_witness.py diff <name1> <name2> # diff two states")
        print("  diff_witness.py quick <path>        # scan, save as 'now', diff with 'prev'")
        print()
        print("example workflow:")
        print("  diff_witness.py scan ~/workspace before")
        print("  # ... make changes ...")
        print("  diff_witness.py scan ~/workspace after")
        print("  diff_witness.py diff before after")
        return

    cmd = sys.argv[1]

    if cmd == "scan":
        if len(sys.argv) < 4:
            print("need: scan <path> <name>")
            return
        path = sys.argv[2]
        name = sys.argv[3]
        witness_and_save(path, name)

    elif cmd == "list":
        states = list_saved_states()
        if not states:
            print("no saved states")
            return

        print(f"saved states ({len(states)}):")
        for s in states:
            print(f"  {s['name']:15} {s['timestamp'][:19]}  {s['files']:4} files  {s['path']}")

    elif cmd == "diff":
        if len(sys.argv) < 4:
            print("need: diff <name1> <name2>")
            return

        name1 = sys.argv[2]
        name2 = sys.argv[3]

        state1 = load_state(name1)
        state2 = load_state(name2)

        if not state1:
            print(f"state not found: {name1}")
            return
        if not state2:
            print(f"state not found: {name2}")
            return

        diff = diff_states(state1, state2)
        print_diff(diff)

    elif cmd == "quick":
        # quick diff: save current as 'now', rename previous 'now' to 'prev', diff
        path = sys.argv[2] if len(sys.argv) > 2 else str(Path.home() / "workspace")

        # load current 'now' if exists
        prev_now = load_state("now")

        # scan and save as 'now'
        print(f"scanning {path}...")
        state = scan_directory(Path(path))
        save_state("now", state, path)
        print(f"saved as 'now' ({len(state)} files)")

        if prev_now:
            # save previous as 'prev'
            save_state("prev", prev_now.get("state", {}), prev_now.get("path", ""))
            print("previous 'now' saved as 'prev'")
            print()

            # diff
            new_now = load_state("now")
            diff = diff_states(prev_now, new_now)
            print_diff(diff)
        else:
            print("(no previous 'now' to diff against)")

    else:
        print(f"unknown command: {cmd}")


if __name__ == "__main__":
    main()
