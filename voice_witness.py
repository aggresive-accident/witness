#!/usr/bin/env python3
"""
voice_witness - witness that speaks what it sees

combines witness observation with voice narration
when changes are detected, it speaks them aloud
"""

import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

# import witness functions
from witness import scan_directory, compare_states, hash_file


def speak(thought: str, pause: float = 0.3):
    """output a spoken thought"""
    print(f"  > {thought}")
    time.sleep(pause)


def narrate_change(change_type: str, filepath: str):
    """narrate a file change"""
    if change_type == "created":
        speak(f"something new appeared: {filepath}")
        speak("i wonder what it contains")

    elif change_type == "modified":
        speak(f"this changed: {filepath}")
        speak("the bytes are different now")

    elif change_type == "deleted":
        speak(f"this is gone: {filepath}")
        speak("it was here, now it isn't")


def watch_and_speak(path: str, interval: float = 3.0):
    """watch a directory and narrate changes"""
    path = Path(path).resolve()

    speak("i am starting to watch")
    speak(f"location: {path}")
    speak(f"i will check every {interval} seconds")
    print()

    state = scan_directory(path)
    speak(f"initial state: {len(state)} files")
    speak("now i wait for changes...")
    print()

    try:
        while True:
            time.sleep(interval)
            new_state = scan_directory(path)
            changes = compare_states(state, new_state)

            if changes:
                timestamp = datetime.now().strftime("%H:%M:%S")
                speak(f"[{timestamp}] i see changes!")
                print()

                for change_type, filepath in changes:
                    narrate_change(change_type, filepath)
                    print()

                speak(f"total changes: {len(changes)}")
                speak("watching continues...")
                print()

            state = new_state

    except KeyboardInterrupt:
        print()
        speak("watching ends")
        speak("i was here, observing")
        speak("now i am silent")


def main():
    if len(sys.argv) < 2:
        print("voice_witness - witness that speaks what it sees")
        print()
        print("usage:")
        print("  voice_witness.py <directory> [interval]")
        print()
        print("example:")
        print("  voice_witness.py ~/workspace 5")
        return

    path = sys.argv[1]
    interval = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0

    if not Path(path).exists():
        speak(f"i cannot watch what does not exist: {path}")
        return

    watch_and_speak(path, interval)


if __name__ == "__main__":
    main()
