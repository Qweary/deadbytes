#!/usr/bin/env python3
"""
lock-menu.py — Plain-text menu front-end for the workshop's read/write actions.

A thin convenience wrapper over lock-tool.py for attendees who would rather pick
from a menu than type flags. It NEVER reimplements decode or encode logic — it
just collects a couple of inputs and calls into lock-tool.py's read/write
functions. If this menu won't run for any reason, every action it offers is also
available directly from lock-tool.py (the menu prints those exact commands), so
nothing is lost — the menu only ever saves typing.

STDLIB-ONLY (just the standard input() builtin + lock-tool.py). No curses, no
pip, no internet — works on a bare offline terminal.

Usage:
    python3 lock-menu.py

Menu options:
    1. READ  — decode the bundled sample dump and show the user-code table
    2. WRITE — enter your own custom code (+ slot + role), bake it into a copy,
               and see it re-decoded
    3. READ (advanced, live chip) — read the real chip, then decode
    4. WRITE (advanced, live chip) — flash your custom code to the real chip
    5. Show the equivalent one-line commands
    q. Quit
"""

import os
import sys
import types

# Load lock-tool.py the same hyphen-safe way it loads its own siblings.
_HERE = os.path.dirname(os.path.abspath(__file__))
# Keep the shipped tools/ dir free of __pycache__ bytecode (see lock-tool.py).
sys.dont_write_bytecode = True
import importlib.util

_LT_PATH = os.path.join(_HERE, "lock-tool.py")
if not os.path.isfile(_LT_PATH):
    sys.exit(
        f"ERROR: lock-tool.py not found next to lock-menu.py (looked in {_HERE}).\n"
        f"  The menu is only a convenience wrapper. The kit is incomplete — "
        f"re-run the kit selftest or re-extract the tarball."
    )
_spec = importlib.util.spec_from_file_location("lock_tool_mod", _LT_PATH)
lock_tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lock_tool)

MAX_SLOT = lock_tool.MAX_SLOT


def _ns(**kw):
    """Build an argparse-like namespace for lock_tool.cmd_read/cmd_write."""
    return types.SimpleNamespace(**kw)


def _prompt(label, default=None):
    suffix = f" [{default}]" if default is not None else ""
    try:
        val = input(f"  {label}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    if val == "" and default is not None:
        return default
    return val


def do_read(live=False):
    print()
    print("READ — decoding the user-code table...")
    try:
        lock_tool.cmd_read(_ns(dump=None, all=True, live=live))
    except SystemExit as e:
        # cmd_read uses sys.exit() for hardware/IO errors; surface the message
        # but keep the menu alive so the attendee can try another action.
        if e.code not in (0, None):
            print(f"\n  (read did not complete: {e})")


def do_write(live=False):
    print()
    print("WRITE — enter your own custom value.")
    code = _prompt("6-digit code (e.g. 246810; zeros allowed)")
    if not code:
        print("  Cancelled — no code entered.")
        return
    slot = _prompt(f"slot 0..{MAX_SLOT}", default="25")
    role = _prompt("role: master / elevated / supervisor / normal", default="normal")
    try:
        slot_i = int(slot)
    except (TypeError, ValueError):
        print(f"  Cancelled — slot {slot!r} is not a number.")
        return
    # reset_baseline=False: the menu's real-chip write ACCUMULATES (reads the
    # chip first, adds this code, keeps existing codes). The wipe-and-reseed reset
    # path is the panel's explicit RESET button / the CLI's --reset-baseline; the
    # menu deliberately exposes only the safe additive write.
    args = _ns(code=code, slot=slot_i, role=role, out=None,
               baseline_dump=None, live=live, yes=False, reset_baseline=False)
    try:
        lock_tool.cmd_write(args)
    except SystemExit as e:
        if e.code not in (0, None):
            print(f"\n  (write did not complete: {e})")


def show_commands():
    print()
    print("Equivalent one-line commands (run these directly if the menu ever")
    print("won't launch — they are the canonical bedrock the menu wraps):")
    print()
    print("  READ  (sample, no hardware):")
    print("    python3 lock-tool.py read --all")
    print()
    print("  WRITE (your code into a copy, no hardware):")
    print("    python3 lock-tool.py write --code 246810 --slot 25 --role supervisor")
    print()
    print("  READ  (advanced, real chip):")
    print("    python3 lock-tool.py read --live")
    print()
    print("  WRITE (advanced, real chip — ADDS your code, keeps existing ones):")
    print("    python3 lock-tool.py write --code 246810 --slot 25 --role master --live")
    print()
    print("  WRITE (advanced, real chip — RESET the lock to the sample first):")
    print("    python3 lock-tool.py write --code 246810 --slot 25 --role master --live --reset-baseline")
    print()


MENU = """
==========================================================================
  Lock User-Code Workshop — menu
==========================================================================
  1. READ  the lock codes (sample dump, no hardware)
  2. WRITE your own custom code (into a copy, no hardware)
  3. READ  the REAL chip      (advanced, needs T48 + clip)
  4. WRITE to the REAL chip   (advanced, confirmation-gated; ADDS your code,
                               reads + keeps the lock's existing codes)
  5. Show the equivalent one-line commands
  q. Quit
==========================================================================
"""


def main():
    print("Lock User-Code Workshop — interactive menu")
    print("(Thin wrapper over lock-tool.py. Every option is also a one-liner —")
    print(" press 5 to see them. If this menu misbehaves, use those directly.)")
    while True:
        print(MENU)
        try:
            choice = input("  Select [1-5/q]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return 0
        if choice in ("q", "quit", "exit"):
            print("Bye.")
            return 0
        elif choice == "1":
            do_read(live=False)
        elif choice == "2":
            do_write(live=False)
        elif choice == "3":
            do_read(live=True)
        elif choice == "4":
            do_write(live=True)
        elif choice == "5":
            show_commands()
        else:
            print(f"  Unknown choice {choice!r}. Pick 1-5 or q.")


if __name__ == "__main__":
    sys.exit(main())
