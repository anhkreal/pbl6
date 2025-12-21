"""
Test Dashboard - Quick Overview of Test Status
==============================================

Chạy script này để xem tổng quan về test coverage và status.
"""

import subprocess
import sys
from datetime import datetime
import os

def print_header():
    print("="*80)
    print("🧪 TEST DASHBOARD - v2.1")
    print("="*80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()

def check_backend_running():
    """Check if backend is running"""
    import requests
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def run_mock_tests():
    """Run mock tests (fast, no backend required)"""
    print("🔹 Running Mock Tests (No Backend Required)...")
    print("-"*80)
    try:
        result = subprocess.run(
            [sys.executable, "test_mock_v21.py"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Parse output
        output = result.stdout
        if "ALL MOCK TESTS PASSED" in output:
            print("✅ Mock Tests: PASSED")
            # Extract counts
            for line in output.split('\n'):
                if "Tests run:" in line or "Passed:" in line or "Failed:" in line:
                    print(f"   {line.strip()}")
        else:
            print("❌ Mock Tests: FAILED")
            print(output[-500:])  # Last 500 chars
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⏱️  Mock Tests: TIMEOUT")
        return False
    except Exception as e:
        print(f"⚠️  Mock Tests: ERROR - {e}")
        return False

def run_integration_tests_quick():
    """Run quick integration tests"""
    print("\n🔹 Running Quick Integration Tests (Backend Required)...")
    print("-"*80)
    
    if not check_backend_running():
        print("⚠️  Backend not running - skipping integration tests")
        print("   Start backend with: python app.py")
        return None
    
    try:
        result = subprocess.run(
            [sys.executable, "run_tests_v21.py", "--quick"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        output = result.stdout
        if "ALL TESTS PASSED" in output:
            print("✅ Integration Tests: PASSED")
            for line in output.split('\n'):
                if "Tests run:" in line or "Passed:" in line or "Failed:" in line:
                    print(f"   {line.strip()}")
        else:
            print("❌ Integration Tests: FAILED")
            print(output[-500:])
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⏱️  Integration Tests: TIMEOUT")
        return False
    except Exception as e:
        print(f"⚠️  Integration Tests: ERROR - {e}")
        return False

def check_test_files():
    """Check test file existence"""
    print("\n🔹 Test Files Status")
    print("-"*80)
    
    files = [
        ("test_iot_v21_comprehensive.py", "Integration tests"),
        ("test_mock_v21.py", "Mock unit tests"),
        ("run_tests_v21.py", "Test runner"),
        ("test_config.ini", "Test configuration"),
        ("TESTS_V21_README.md", "Test documentation"),
    ]
    
    all_exist = True
    for filename, description in files:
        exists = os.path.exists(filename)
        status = "✅" if exists else "❌"
        print(f"   {status} {filename:40s} - {description}")
        if not exists:
            all_exist = False
    
    return all_exist

def show_test_coverage():
    """Show which features are tested"""
    print("\n🔹 Test Coverage by Feature")
    print("-"*80)
    
    features = [
        ("Session tracking (no_serving_count >= 2)", "✅ Covered"),
        ("Emotion scoring (first bad emotion)", "✅ Covered"),
        ("Grace period (30 min after shift)", "✅ Covered"),
        ("Auto checkout (no early penalty)", "✅ Covered"),
        ("KPI calculation (70-30 ratio)", "✅ Covered"),
        ("Thread-safety (concurrent APIs)", "✅ Covered"),
        ("Real-world scenarios", "✅ Covered"),
    ]
    
    for feature, status in features:
        print(f"   {status:12s} {feature}")

def show_recommendations():
    """Show recommendations"""
    print("\n🔹 Recommendations")
    print("-"*80)
    
    backend_running = check_backend_running()
    
    if not backend_running:
        print("   ⚠️  Backend not running")
        print("      → Start with: python app.py")
        print("      → Then run: python run_tests_v21.py --quick")
    else:
        print("   ✅ Backend is running")
        
    current_time = datetime.now().time()
    grace_times = [
        (datetime.strptime("14:00", "%H:%M").time(), 
         datetime.strptime("14:30", "%H:%M").time()),
        (datetime.strptime("20:00", "%H:%M").time(), 
         datetime.strptime("20:30", "%H:%M").time()),
    ]
    
    in_grace = False
    for start, end in grace_times:
        if start <= current_time < end:
            in_grace = True
            print(f"   ⏰ Currently in grace period ({start.strftime('%H:%M')}-{end.strftime('%H:%M')})")
            print("      → Good time to run: python run_tests_v21.py --grace")
            break
    
    if not in_grace:
        print("   ⏰ Not in grace period")
        print("      → Grace period tests will be skipped")
        print("      → Run full tests at 14:00-14:30 or 20:00-20:30")
    
    print("\n   💡 Quick Commands:")
    print("      python test_mock_v21.py                    # Fast, no backend")
    print("      python run_tests_v21.py --quick            # Quick integration")
    print("      python test_iot_v21_comprehensive.py       # Full suite")

def main():
    print_header()
    
    # Check files
    files_ok = check_test_files()
    
    # Show coverage
    show_test_coverage()
    
    # Run tests
    if files_ok:
        mock_passed = run_mock_tests()
        integration_passed = run_integration_tests_quick()
        
        # Summary
        print("\n" + "="*80)
        print("📊 OVERALL STATUS")
        print("="*80)
        
        if mock_passed:
            print("✅ Mock Tests: PASSED")
        else:
            print("❌ Mock Tests: FAILED")
        
        if integration_passed is None:
            print("⏭️  Integration Tests: SKIPPED (backend not running)")
        elif integration_passed:
            print("✅ Integration Tests: PASSED")
        else:
            print("❌ Integration Tests: FAILED")
        
        print("="*80)
    else:
        print("\n❌ Some test files missing!")
    
    # Show recommendations
    show_recommendations()
    
    print("\n" + "="*80)
    print("🎯 For detailed test results, run individual test files")
    print("="*80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)

