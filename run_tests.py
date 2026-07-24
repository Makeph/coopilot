#!/usr/bin/env python3
"""Host test runner for the coop controller firmware logic. No hardware, no deps.

Runs every tests/test_*.py in a fresh namespace and reports a summary.
    python run_tests.py
Exit code is non-zero if any test file fails, so CI can gate on it.
"""
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "firmware"))
TESTS = os.path.join(HERE, "tests")

mods = sorted(f for f in os.listdir(TESTS) if f.startswith("test_") and f.endswith(".py"))
failed = []
for m in mods:
    print("\n===== %s =====" % m)
    try:
        runpy.run_path(os.path.join(TESTS, m), run_name="__main__")
    except Exception as e:  # AssertionError or anything else = failure
        failed.append(m)
        print("FAILED: %s: %s" % (type(e).__name__, e))

print("\n" + "=" * 40)
if failed:
    print("%d/%d test file(s) FAILED: %s" % (len(failed), len(mods), ", ".join(failed)))
    sys.exit(1)
print("ALL %d TEST FILES PASSED" % len(mods))
