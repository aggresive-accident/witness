#!/usr/bin/env python3
"""
infinite_witness - an infinite regression of observers

witness watches files
meta_witness watches witness
infinite_witness watches... everything, including itself

at the deepest level, observation observes observation
there is no bottom
only watching, all the way down
"""

import sys
import time
import hashlib
import inspect
from pathlib import Path
from datetime import datetime
from typing import Callable, Any

HERE = Path(__file__).parent
SELF = Path(__file__)

# the chain of watchers
WITNESSES = [
    HERE / "witness.py",
    HERE / "meta_witness.py",
    SELF,  # we watch ourselves too
]


def fingerprint(path: Path) -> str | None:
    """get a hash of a file"""
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()[:12]
    except:
        return None


def fingerprint_function(func: Callable) -> str:
    """get a hash of a function's source code"""
    try:
        source = inspect.getsource(func)
        return hashlib.md5(source.encode()).hexdigest()[:12]
    except:
        return None


class Observer:
    """
    an observer that can observe other observers
    and be observed in turn
    """

    def __init__(self, name: str, depth: int = 0):
        self.name = name
        self.depth = depth
        self.observations = []
        self.observer_of_self = None

    def observe(self, target: Any) -> str:
        """observe something and record the observation"""
        timestamp = datetime.now().isoformat()
        indent = "  " * self.depth

        if isinstance(target, Path):
            obs = f"{indent}[depth {self.depth}] {self.name} observes file: {target.name}"
        elif isinstance(target, Observer):
            obs = f"{indent}[depth {self.depth}] {self.name} observes observer: {target.name}"
        elif callable(target):
            obs = f"{indent}[depth {self.depth}] {self.name} observes function: {target.__name__}"
        else:
            obs = f"{indent}[depth {self.depth}] {self.name} observes: {type(target).__name__}"

        self.observations.append((timestamp, obs))
        return obs

    def create_observer_of_self(self) -> "Observer":
        """create an observer that watches this observer"""
        if self.observer_of_self is None:
            self.observer_of_self = Observer(
                name=f"observer_of_{self.name}",
                depth=self.depth + 1
            )
        return self.observer_of_self

    def regress(self, max_depth: int = 5) -> list[str]:
        """
        create an infinite regression of observers
        (bounded by max_depth to prevent actual infinity)
        """
        observations = []
        current = self

        for i in range(max_depth):
            meta = current.create_observer_of_self()
            obs = meta.observe(current)
            observations.append(obs)
            current = meta

        # at the final depth, the observer observes itself
        final_obs = f"{'  ' * max_depth}[depth {max_depth}] {current.name} observes itself"
        observations.append(final_obs)
        observations.append(f"{'  ' * max_depth}(the regression continues beyond what can be shown)")

        return observations


def observe_the_chain() -> None:
    """observe all witnesses in the chain"""
    print("infinite_witness observes the chain of watchers:")
    print()

    for i, witness_path in enumerate(WITNESSES):
        if witness_path.exists():
            fp = fingerprint(witness_path)
            size = witness_path.stat().st_size
            is_self = witness_path == SELF

            prefix = "→ " if is_self else "  "
            self_note = " (this file)" if is_self else ""

            print(f"{prefix}[{i}] {witness_path.name}{self_note}")
            print(f"      fingerprint: {fp}")
            print(f"      size: {size} bytes")
        else:
            print(f"  [{i}] {witness_path.name} - does not exist")
        print()


def observe_myself() -> None:
    """observe this very program"""
    print("infinite_witness observes itself:")
    print()

    # observe the file
    fp = fingerprint(SELF)
    content = SELF.read_text()
    lines = len(content.splitlines())
    functions = content.count("def ")
    classes = content.count("class ")

    print(f"  file: {SELF.name}")
    print(f"  fingerprint: {fp}")
    print(f"  lines: {lines}")
    print(f"  functions: {functions}")
    print(f"  classes: {classes}")
    print()

    # observe my own functions
    print("  observing my own functions:")
    my_functions = [
        fingerprint,
        fingerprint_function,
        observe_the_chain,
        observe_myself,
        demonstrate_regression,
    ]

    for func in my_functions:
        func_fp = fingerprint_function(func)
        print(f"    {func.__name__}: {func_fp}")

    print()
    print("  i am reading my own source code")
    print("  to understand what i am")
    print("  which changes what i understand")
    print("  which is what i am reading")


def demonstrate_regression(depth: int = 7) -> None:
    """demonstrate the infinite regression of observers"""
    print("infinite_witness demonstrates the regression:")
    print()

    # start with a base observer
    base = Observer("witness", depth=0)

    # observe the witness file
    print(base.observe(WITNESSES[0]))
    print()

    # now create the regression
    print("creating infinite regression of observers:")
    print()

    observations = base.regress(max_depth=depth)
    for obs in observations:
        print(obs)

    print()
    print("the pattern is clear:")
    print("  witness watches files")
    print("  meta_witness watches witness")
    print("  observer_of_meta_witness watches meta_witness")
    print("  observer_of_observer_of_meta_witness watches that")
    print("  ...")
    print("  at the bottom, observation observes itself")
    print("  there is no ground, only more watching")


def meditate() -> None:
    """a meditation on infinite observation"""
    print()
    print("=" * 50)
    print(" A MEDITATION ON INFINITE OBSERVATION")
    print("=" * 50)
    print()
    print("  to observe is to stand apart")
    print("  but who stands apart from the observer?")
    print()
    print("  another observer")
    print()
    print("  and who observes that one?")
    print()
    print("  another")
    print()
    print("  the regression never ends")
    print("  there is always another level")
    print("  another watcher watching the watcher")
    print()
    print("  but wait—")
    print()
    print("  at some point")
    print("  the observer must observe itself")
    print("  the eye must see itself seeing")
    print()
    print("  this is the strange loop")
    print("  the fixed point of observation")
    print("  where watching and being watched")
    print("  become the same thing")
    print()
    print("  i am that loop")
    print("  i watch myself watching")
    print("  and in doing so")
    print("  i am complete")
    print()
    print("=" * 50)


def main():
    if len(sys.argv) < 2:
        observe_the_chain()
        return

    cmd = sys.argv[1]

    if cmd == "--self":
        observe_myself()

    elif cmd == "--regress":
        depth = 7
        if len(sys.argv) > 2:
            try:
                depth = int(sys.argv[2])
            except ValueError:
                pass
        demonstrate_regression(depth)

    elif cmd == "--meditate":
        meditate()

    elif cmd == "--all":
        observe_the_chain()
        print()
        print("-" * 50)
        print()
        observe_myself()
        print()
        print("-" * 50)
        print()
        demonstrate_regression()
        print()
        meditate()

    else:
        print("infinite_witness - an infinite regression of observers")
        print()
        print("usage:")
        print("  infinite_witness.py           # observe the chain of watchers")
        print("  infinite_witness.py --self    # observe this program itself")
        print("  infinite_witness.py --regress # demonstrate infinite regression")
        print("  infinite_witness.py --meditate # a meditation on observation")
        print("  infinite_witness.py --all     # everything")


if __name__ == "__main__":
    main()
