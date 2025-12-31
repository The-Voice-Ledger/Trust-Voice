#!/usr/bin/env python3
"""
Test runner for TrustVoice mini app integration tests.
Runs smoke tests, integration tests, and frontend validation.
"""
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0


def main():
    """Run all test suites"""
    tests_dir = Path(__file__).parent
    project_root = tests_dir.parent
    
    print("\n" + "="*60)
    print("  TrustVoice Mini App Test Suite")
    print("="*60)
    
    # Check if server is running
    print("\nℹ️  Make sure the FastAPI server is running on http://localhost:8001")
    print("   Start it with: uvicorn main:app --reload --port 8001\n")
    
    input("Press Enter when server is ready, or Ctrl+C to cancel...")
    
    results = []
    
    # 1. Quick smoke test
    success = run_command(
        f"python {tests_dir / 'smoke_test.py'}",
        "Quick Smoke Test (Basic Integration)"
    )
    results.append(("Smoke Test", success))
    
    # 2. Frontend validation (doesn't require server)
    success = run_command(
        f"pytest {tests_dir / 'test_frontend_validation.py'} -v",
        "Frontend Validation Tests"
    )
    results.append(("Frontend Tests", success))
    
    # 3. Full integration tests (requires server)
    success = run_command(
        f"pytest {tests_dir / 'test_miniapp_integration.py'} -v",
        "Backend Integration Tests"
    )
    results.append(("Integration Tests", success))
    
    # Summary
    print("\n" + "="*60)
    print("  Test Results Summary")
    print("="*60 + "\n")
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status}  {name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\n  Total: {total_passed}/{total_tests} test suites passed")
    
    if total_passed == total_tests:
        print("\n🎉 All test suites passed!\n")
        return 0
    else:
        print("\n⚠️  Some test suites failed. Review output above.\n")
        return 1


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\nTests cancelled by user.\n")
        exit(1)
