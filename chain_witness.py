#!/usr/bin/env python3
"""
chain_witness - watches the infinite chain state file

observes iteration changes, completed tasks, ideas queue
reports when the chain moves forward
"""

import json
import sys
import time
import hashlib
from datetime import datetime
from pathlib import Path

# Singleton protection
sys.path.insert(0, str(Path.home() / "workspace" / "organism"))
try:
    from core.singleton import Singleton
    HAS_SINGLETON = True
except ImportError:
    HAS_SINGLETON = False

HOME = Path.home()
STATE_FILE = HOME / ".infinite-chain" / "state.json"
LOG_FILE = HOME / ".infinite-chain" / ".chain-witness.log"


def fingerprint(data: dict) -> str:
    """hash of state for change detection"""
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()[:12]


def load_state() -> dict | None:
    """load current chain state"""
    if not STATE_FILE.exists():
        return None
    try:
        return json.loads(STATE_FILE.read_text())
    except:
        return None


def log_observation(message: str):
    """log an observation"""
    timestamp = datetime.now().isoformat(timespec='seconds')
    entry = f"[{timestamp}] {message}\n"

    with open(LOG_FILE, "a") as f:
        f.write(entry)

    print(entry.strip())


def describe_change(old: dict, new: dict) -> list[str]:
    """describe what changed between two states"""
    changes = []

    if old["iteration"] != new["iteration"]:
        changes.append(f"iteration: {old['iteration']} -> {new['iteration']}")

    old_completed = len(old.get("completed", []))
    new_completed = len(new.get("completed", []))
    if old_completed != new_completed:
        changes.append(f"completed tasks: {old_completed} -> {new_completed}")
        if new_completed > old_completed:
            latest = new["completed"][-1]
            if isinstance(latest, dict):
                changes.append(f"  latest: {latest.get('task', 'unknown')[:40]}...")

    old_ideas = len(old.get("ideas", []))
    new_ideas = len(new.get("ideas", []))
    if old_ideas != new_ideas:
        changes.append(f"ideas queue: {old_ideas} -> {new_ideas}")

    old_streak = old.get("streak", {}).get("iterations", 0)
    new_streak = new.get("streak", {}).get("iterations", 0)
    if old_streak != new_streak:
        changes.append(f"streak: {old_streak} -> {new_streak}")

    return changes


def watch_once():
    """single observation of chain state"""
    state = load_state()

    if state is None:
        print("chain state not found")
        return

    print("chain_witness observes:")
    print()
    print(f"  iteration: {state.get('iteration', 0)}")
    print(f"  streak: {state.get('streak', {}).get('iterations', 0)}")
    print(f"  completed: {len(state.get('completed', []))}")
    print(f"  ideas: {len(state.get('ideas', []))}")
    print(f"  last run: {state.get('last_run', 'never')}")
    print()
    print(f"  fingerprint: {fingerprint(state)}")


def watch_loop(interval: float = 5.0):
    """continuously watch for chain changes"""
    # Singleton protection
    guard = None
    if HAS_SINGLETON:
        guard = Singleton("chain-witness")
        if not guard.acquire():
            print("chain-witness: already running")
            return

    print("chain_witness begins watching")
    print(f"target: {STATE_FILE}")
    print(f"interval: {interval}s")
    if guard:
        print("singleton: protected")
    print()

    log_observation("chain_witness begins")

    state = load_state()
    if state is None:
        print("chain state not found, waiting...")
        while state is None:
            time.sleep(interval)
            state = load_state()

    fp = fingerprint(state)
    log_observation(f"initial state: iteration={state.get('iteration')}, streak={state.get('streak', {}).get('iterations')}")

    try:
        while True:
            time.sleep(interval)
            new_state = load_state()

            if new_state is None:
                continue

            new_fp = fingerprint(new_state)

            if new_fp != fp:
                changes = describe_change(state, new_state)
                log_observation("chain moved:")
                for change in changes:
                    log_observation(f"  {change}")

                state = new_state
                fp = new_fp

    except KeyboardInterrupt:
        print()
        log_observation("chain_witness stops")
        print()
        print("observation ended")
    finally:
        if guard:
            guard.release()


def show_history():
    """show observation history"""
    if not LOG_FILE.exists():
        print("no observations recorded")
        return

    print("chain_witness history:")
    print()
    print(LOG_FILE.read_text())


def main():
    if len(sys.argv) < 2:
        watch_once()
        return

    cmd = sys.argv[1]

    if cmd == "--loop":
        interval = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
        watch_loop(interval)

    elif cmd == "--history":
        show_history()

    else:
        print("chain_witness - watches the infinite chain state")
        print()
        print("usage:")
        print("  chain_witness.py           # observe once")
        print("  chain_witness.py --loop    # continuous watching")
        print("  chain_witness.py --history # show log")


if __name__ == "__main__":
    main()
