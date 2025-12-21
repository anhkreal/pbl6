"""
Quick Test Runner Script
========================

Chạy nhanh comprehensive tests với options khác nhau.

Usage:
    python run_tests_v21.py                    # Run all tests
    python run_tests_v21.py --session          # Only session tracking tests
    python run_tests_v21.py --emotion          # Only emotion scoring tests
    python run_tests_v21.py --grace            # Only grace period tests
    python run_tests_v21.py --thread           # Only thread-safety tests
    python run_tests_v21.py --quick            # Quick tests (skip time-dependent)
"""

import sys
import argparse
import unittest
from test_iot_v21_comprehensive import (
    TestSessionTracking,
    TestEmotionScoringFirstBad,
    TestGracePeriod,
    TestAutoCheckout,
    TestKPICalculation,
    TestThreadSafeConcurrentAPIs,
    TestRealWorldScenarios
)


def main():
    parser = argparse.ArgumentParser(description="Run IoT v2.1 tests")
    parser.add_argument("--session", action="store_true", help="Run session tracking tests")
    parser.add_argument("--emotion", action="store_true", help="Run emotion scoring tests")
    parser.add_argument("--grace", action="store_true", help="Run grace period tests")
    parser.add_argument("--checkout", action="store_true", help="Run auto checkout tests")
    parser.add_argument("--kpi", action="store_true", help="Run KPI calculation tests")
    parser.add_argument("--thread", action="store_true", help="Run thread-safety tests")
    parser.add_argument("--scenario", action="store_true", help="Run real-world scenarios")
    parser.add_argument("--quick", action="store_true", help="Quick tests (skip time-dependent)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Create test suite
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Determine which tests to run
    if args.quick:
        # Quick tests: skip grace period and auto checkout (time-dependent)
        suite.addTests(loader.loadTestsFromTestCase(TestSessionTracking))
        suite.addTests(loader.loadTestsFromTestCase(TestEmotionScoringFirstBad))
        suite.addTests(loader.loadTestsFromTestCase(TestKPICalculation))
        suite.addTests(loader.loadTestsFromTestCase(TestThreadSafeConcurrentAPIs))
        print("🚀 Running QUICK tests (time-independent only)...\n")
    elif args.session:
        suite.addTests(loader.loadTestsFromTestCase(TestSessionTracking))
        print("🧪 Running SESSION TRACKING tests...\n")
    elif args.emotion:
        suite.addTests(loader.loadTestsFromTestCase(TestEmotionScoringFirstBad))
        print("🧪 Running EMOTION SCORING tests...\n")
    elif args.grace:
        suite.addTests(loader.loadTestsFromTestCase(TestGracePeriod))
        print("🧪 Running GRACE PERIOD tests...\n")
    elif args.checkout:
        suite.addTests(loader.loadTestsFromTestCase(TestAutoCheckout))
        print("🧪 Running AUTO CHECKOUT tests...\n")
    elif args.kpi:
        suite.addTests(loader.loadTestsFromTestCase(TestKPICalculation))
        print("🧪 Running KPI CALCULATION tests...\n")
    elif args.thread:
        suite.addTests(loader.loadTestsFromTestCase(TestThreadSafeConcurrentAPIs))
        print("🧪 Running THREAD-SAFETY tests...\n")
    elif args.scenario:
        suite.addTests(loader.loadTestsFromTestCase(TestRealWorldScenarios))
        print("🧪 Running REAL-WORLD SCENARIOS...\n")
    else:
        # Run all tests
        suite.addTests(loader.loadTestsFromTestCase(TestSessionTracking))
        suite.addTests(loader.loadTestsFromTestCase(TestEmotionScoringFirstBad))
        suite.addTests(loader.loadTestsFromTestCase(TestGracePeriod))
        suite.addTests(loader.loadTestsFromTestCase(TestAutoCheckout))
        suite.addTests(loader.loadTestsFromTestCase(TestKPICalculation))
        suite.addTests(loader.loadTestsFromTestCase(TestThreadSafeConcurrentAPIs))
        suite.addTests(loader.loadTestsFromTestCase(TestRealWorldScenarios))
        print("🧪 Running ALL tests...\n")
    
    # Run tests
    verbosity = 2 if args.verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    print(f"⏭️  Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
