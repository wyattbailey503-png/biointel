"""Lightweight standalone test runner for BioIntel.

Executes all test functions in tests/ without requiring third-party test runners.
"""

from __future__ import annotations

import importlib
import inspect
import sys
import time
import traceback
import unittest
from pathlib import Path



def main() -> int:
    tests_dir = Path(__file__).parent
    sys.path.insert(0, str(tests_dir.parent / "src"))
    sys.path.insert(0, str(tests_dir.parent))

    test_files = sorted(tests_dir.glob("test_*.py"))
    passed = 0
    failed = 0
    total = 0

    print("=================================================================")
    print("                 BIOINTEL TEST SUITE EXECUTION                   ")
    print("=================================================================")

    start_suite = time.time()
    for tf in test_files:
        mod_name = f"tests.{tf.stem}"
        try:
            mod = importlib.import_module(mod_name)
        except Exception as e:
            print(f"[FAIL] Could not import {mod_name}: {e}")
            traceback.print_exc()
            failed += 1
            continue

        test_funcs = [
            (name, fn)
            for name, fn in inspect.getmembers(mod, inspect.isfunction)
            if name.startswith("test_")
        ]

        # Also find unittest.TestCase classes
        test_classes = [
            (cname, cls)
            for cname, cls in inspect.getmembers(mod, inspect.isclass)
            if issubclass(cls, unittest.TestCase) and cls != unittest.TestCase
        ]

        for cname, cls in test_classes:
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(cls)
            for test in suite:
                total += 1
                t0 = time.time()
                result = unittest.TestResult()
                test.run(result)
                dt = (time.time() - t0) * 1000
                test_name = test._testMethodName
                if result.wasSuccessful():
                    print(f" [PASS] {mod_name}::{cname}::{test_name} ({dt:.1f}ms)")
                    passed += 1
                else:
                    print(f" [FAIL] {mod_name}::{cname}::{test_name} ({dt:.1f}ms)")
                    for err in result.errors + result.failures:
                        print(f"        {err[1]}")
                    failed += 1

        for name, fn in test_funcs:
            total += 1
            t0 = time.time()
            try:
                # Handle simple fixtures if needed
                sig = inspect.signature(fn)
                if "temp_db" in sig.parameters:
                    import tempfile
                    from biointel.storage.database import Database
                    with tempfile.NamedTemporaryFile(suffix=".db") as f:
                        db = Database(f.name)
                        fn(db)
                elif "tmp_path" in sig.parameters:
                    import tempfile
                    with tempfile.TemporaryDirectory() as td:
                        fn(Path(td))
                else:
                    fn()
                dt = (time.time() - t0) * 1000
                print(f" [PASS] {mod_name}::{name} ({dt:.1f}ms)")
                passed += 1
            except Exception as e:
                dt = (time.time() - t0) * 1000
                print(f" [FAIL] {mod_name}::{name} ({dt:.1f}ms)")
                print(f"        {type(e).__name__}: {e}")
                traceback.print_exc()
                failed += 1

    total_time = time.time() - start_suite
    print("=================================================================")
    print(f" Results: {passed} passed, {failed} failed in {total_time:.2f}s")
    print("=================================================================")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
