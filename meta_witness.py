#!/usr/bin/env python3
"""
meta-witness - watches the watcher

witness observes files
meta-witness observes witness observing
the observer is observed
"""

import sys
import time
import hashlib
from pathlib import Path
from datetime import datetime

# where we come from
HERE = Path(__file__).parent
WITNESS = HERE / "witness.py"

# observation log
OBSERVATIONS_FILE = HERE / ".meta-observations.log"


def fingerprint(path: Path) -> str | None:
    """get a hash of a file"""
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()[:12]
    except:
        return None


def log_observation(message: str) -> None:
    """record an observation"""
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] {message}\n"

    with open(OBSERVATIONS_FILE, "a") as f:
        f.write(entry)

    print(entry.strip())


def observe_witness() -> dict:
    """observe the state of witness"""
    state = {
        "exists": WITNESS.exists(),
        "fingerprint": None,
        "size": None,
        "mtime": None,
    }

    if state["exists"]:
        stat = WITNESS.stat()
        state["fingerprint"] = fingerprint(WITNESS)
        state["size"] = stat.st_size
        state["mtime"] = stat.st_mtime

    return state


def describe_change(before: dict, after: dict) -> str | None:
    """describe what changed in witness"""
    if not before["exists"] and after["exists"]:
        return "witness has appeared"

    if before["exists"] and not after["exists"]:
        return "witness has vanished"

    if before["fingerprint"] != after["fingerprint"]:
        return f"witness has changed (was {before['fingerprint']}, now {after['fingerprint']})"

    return None


def watch_once() -> None:
    """take a single observation"""
    state = observe_witness()

    print("meta-witness observes:")
    print()

    if not state["exists"]:
        print("  witness does not exist")
        print("  there is nothing to observe observing")
        return

    print(f"  witness exists at: {WITNESS}")
    print(f"  witness fingerprint: {state['fingerprint']}")
    print(f"  witness size: {state['size']} bytes")

    # read witness and count its observations
    content = WITNESS.read_text()
    obs_count = content.count("OBSERVATIONS")
    func_count = content.count("def ")

    print()
    print(f"  witness defines {func_count} functions")
    print(f"  witness references OBSERVATIONS {obs_count} times")
    print()
    print("  the watcher is being watched")
    print("  does it know?")


def watch_loop(interval: float = 5.0) -> None:
    """continuously observe witness"""
    print("meta-witness begins observing")
    print(f"target: {WITNESS}")
    print(f"interval: {interval}s")
    print()

    log_observation("meta-witness begins")

    state = observe_witness()
    log_observation(f"initial state: fingerprint={state['fingerprint']}")

    try:
        while True:
            time.sleep(interval)
            new_state = observe_witness()

            change = describe_change(state, new_state)
            if change:
                log_observation(change)

            state = new_state

    except KeyboardInterrupt:
        print()
        log_observation("meta-witness stops observing")
        print()
        print("the observation of the observer ends")


def show_history() -> None:
    """show observation history"""
    if not OBSERVATIONS_FILE.exists():
        print("no observations recorded yet")
        return

    print("meta-witness observation history:")
    print()
    print(OBSERVATIONS_FILE.read_text())


def main():
    if len(sys.argv) < 2:
        watch_once()
        return

    cmd = sys.argv[1]

    if cmd == "--loop":
        interval = 5.0
        if len(sys.argv) > 2:
            try:
                interval = float(sys.argv[2])
            except ValueError:
                pass
        watch_loop(interval)

    elif cmd == "--history":
        show_history()

    else:
        print("meta-witness - watches the watcher")
        print()
        print("usage:")
        print("  meta_witness.py           # observe once")
        print("  meta_witness.py --loop    # continuous observation")
        print("  meta_witness.py --history # show observation log")


if __name__ == "__main__":
    main()
