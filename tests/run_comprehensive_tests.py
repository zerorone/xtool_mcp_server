#!/usr/bin/env python3
"""
Comprehensive Test Runner for xtool MCP Server

This script runs all test suites and generates a comprehensive test report.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest


class TestReporter:
    """Generate comprehensive test reports"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "suites": {},
            "summary": {"total_tests": 0, "passed": 0, "failed": 0, "skipped": 0, "duration": 0},
        }

    def run_test_suite(self, suite_name: str, test_file: str, markers: list[str] = None) -> dict:
        """Run a test suite and collect results"""
        print(f"\n{'=' * 60}")
        print(f"Running {suite_name}")
        print(f"{'=' * 60}")

        start_time = time.time()

        # Prepare pytest arguments
        args = [test_file, "-v", "--tb=short"]
        if markers:
            for marker in markers:
                args.extend(["-m", marker])

        # Run tests and capture results
        result = pytest.main(args)

        duration = time.time() - start_time

        # Store results
        suite_result = {
            "name": suite_name,
            "file": test_file,
            "duration": duration,
            "exit_code": result,
            "status": "passed" if result == 0 else "failed",
        }

        self.results["suites"][suite_name] = suite_result

        return suite_result

    def generate_report(self) -> str:
        """Generate final test report"""
        report = []
        report.append("\n" + "=" * 80)
        report.append("xtool MCP SERVER - COMPREHENSIVE TEST REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {self.results['timestamp']}")
        report.append("")

        # Suite results
        report.append("TEST SUITE RESULTS:")
        report.append("-" * 40)

        total_duration = 0
        for suite_name, suite_result in self.results["suites"].items():
            status_emoji = "✅" if suite_result["status"] == "passed" else "❌"
            report.append(f"{status_emoji} {suite_name:30} {suite_result['duration']:.2f}s")
            total_duration += suite_result["duration"]

        # Summary
        report.append("")
        report.append("SUMMARY:")
        report.append("-" * 40)

        passed_suites = sum(1 for s in self.results["suites"].values() if s["status"] == "passed")
        total_suites = len(self.results["suites"])

        report.append(f"Total Test Suites: {total_suites}")
        report.append(f"Passed: {passed_suites}")
        report.append(f"Failed: {total_suites - passed_suites}")
        report.append(f"Total Duration: {total_duration:.2f}s")
        report.append(f"Success Rate: {(passed_suites / total_suites * 100):.1f}%")

        # Recommendations
        report.append("")
        report.append("RECOMMENDATIONS:")
        report.append("-" * 40)

        if passed_suites == total_suites:
            report.append("✅ All tests passed! Ready for deployment.")
        else:
            report.append("⚠️ Some tests failed. Please review and fix before deployment.")
            failed_suites = [name for name, result in self.results["suites"].items() if result["status"] == "failed"]
            report.append(f"   Failed suites: {', '.join(failed_suites)}")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

    def save_report(self, filepath: str = "test_report.json"):
        """Save detailed report to file"""
        with open(filepath, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\nDetailed report saved to: {filepath}")


def run_unit_tests(reporter: TestReporter):
    """Run unit test suites"""
    print("\n🧪 RUNNING UNIT TESTS")

    # Find all unit test files
    test_dir = Path(__file__).parent
    unit_test_files = [
        f
        for f in test_dir.glob("test_*.py")
        if f.name
        not in [
            "test_integration_comprehensive.py",
            "test_e2e_mcp_protocol.py",
            "test_performance_stress.py",
            "test_cross_tool_collaboration.py",
            "run_comprehensive_tests.py",
        ]
    ]

    for test_file in unit_test_files:
        suite_name = f"Unit: {test_file.stem}"
        reporter.run_test_suite(suite_name, str(test_file), markers=["not integration"])


def run_integration_tests(reporter: TestReporter):
    """Run integration test suites"""
    print("\n🔗 RUNNING INTEGRATION TESTS")

    test_file = Path(__file__).parent / "test_integration_comprehensive.py"
    if test_file.exists():
        reporter.run_test_suite("Integration: Comprehensive", str(test_file))


def run_e2e_tests(reporter: TestReporter):
    """Run end-to-end test suites"""
    print("\n🚀 RUNNING END-TO-END TESTS")

    test_file = Path(__file__).parent / "test_e2e_mcp_protocol.py"
    if test_file.exists():
        reporter.run_test_suite("E2E: MCP Protocol", str(test_file))


def run_performance_tests(reporter: TestReporter):
    """Run performance test suites"""
    print("\n⚡ RUNNING PERFORMANCE TESTS")

    test_file = Path(__file__).parent / "test_performance_stress.py"
    if test_file.exists():
        reporter.run_test_suite("Performance: Stress Tests", str(test_file))


def run_collaboration_tests(reporter: TestReporter):
    """Run cross-tool collaboration tests"""
    print("\n🤝 RUNNING COLLABORATION TESTS")

    test_file = Path(__file__).parent / "test_cross_tool_collaboration.py"
    if test_file.exists():
        reporter.run_test_suite("Collaboration: Cross-Tool", str(test_file))


def check_environment():
    """Check test environment setup"""
    print("🔍 Checking Test Environment...")

    issues = []

    # Check Python version

    # Check for API keys (at least one should be set)
    api_keys = ["OPENAI_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY", "CUSTOM_API_URL"]

    if not any(os.getenv(key) for key in api_keys):
        issues.append("No API keys configured. At least one API key required for AI-based tests.")

    # Check test directory
    test_dir = Path(__file__).parent
    if not test_dir.exists():
        issues.append(f"Test directory not found: {test_dir}")

    if issues:
        print("⚠️ Environment Issues Found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nSome tests may fail due to environment issues.")
    else:
        print("✅ Environment check passed!")

    return len(issues) == 0


def main():
    """Main test runner"""
    print("🚀 xtool MCP Server - Comprehensive Test Suite")
    print("=" * 60)

    # Check environment
    env_ok = check_environment()
    if not env_ok:
        response = input("\nContinue with tests anyway? (y/n): ")
        if response.lower() != "y":
            print("Tests cancelled.")
            return

    # Create reporter
    reporter = TestReporter()

    # Run test suites in order
    start_time = time.time()

    try:
        # 1. Unit tests first (fastest, no external dependencies)
        run_unit_tests(reporter)

        # 2. Integration tests (may require API keys)
        run_integration_tests(reporter)

        # 3. E2E tests (full protocol testing)
        run_e2e_tests(reporter)

        # 4. Performance tests (may take longer)
        response = input("\nRun performance tests? These may take longer (y/n): ")
        if response.lower() == "y":
            run_performance_tests(reporter)

        # 5. Collaboration tests
        run_collaboration_tests(reporter)

    except KeyboardInterrupt:
        print("\n\n⚠️ Test run interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test run failed with error: {e}")

    # Generate and display report
    total_duration = time.time() - start_time
    print(f"\n\nTotal test duration: {total_duration:.2f}s")

    report = reporter.generate_report()
    print(report)

    # Save detailed report
    reporter.save_report("test_report.json")

    # Exit with appropriate code
    failed_suites = sum(1 for s in reporter.results["suites"].values() if s["status"] == "failed")
    sys.exit(failed_suites)


if __name__ == "__main__":
    # For async tests
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    main()
