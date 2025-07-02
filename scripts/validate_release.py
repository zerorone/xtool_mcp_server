#!/usr/bin/env python3
"""
Zen MCP Server Release Validation Script
Performs comprehensive validation before release
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any


# Colors for terminal output
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{Colors.BLUE}{'=' * 50}{Colors.NC}")
    print(f"{Colors.BLUE}{title:^50}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 50}{Colors.NC}\n")


def print_status(success: bool, message: str):
    """Print a status message with color"""
    symbol = f"{Colors.GREEN}✓{Colors.NC}" if success else f"{Colors.RED}✗{Colors.NC}"
    print(f"{symbol} {message}")


def run_command(cmd: list[str], description: str) -> tuple[bool, str]:
    """Run a command and return success status and output"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"{e.stderr}\n{e.stdout}"
    except Exception as e:
        return False, str(e)


def check_version_consistency() -> bool:
    """Check version consistency across files"""
    print(f"{Colors.YELLOW}Checking version consistency...{Colors.NC}")

    # Get version from config.py
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import __version__ as config_version

    # Check CHANGELOG.md
    changelog_path = Path("CHANGELOG.md")
    if changelog_path.exists():
        with open(changelog_path, encoding="utf-8") as f:
            content = f.read()
            # Look for version in changelog
            import re

            match = re.search(r"## \[([0-9.]+)\]", content)
            if match:
                changelog_version = match.group(1)
                if config_version == changelog_version:
                    print_status(True, f"Version consistent: {config_version}")
                    return True
                else:
                    print_status(
                        False, f"Version mismatch: config.py={config_version}, CHANGELOG.md={changelog_version}"
                    )
                    return False

    print_status(False, "CHANGELOG.md not found or version not detected")
    return False


def check_dependencies() -> bool:
    """Validate all dependencies are properly specified"""
    print(f"{Colors.YELLOW}Checking dependencies...{Colors.NC}")

    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        print_status(False, "requirements.txt not found")
        return False

    # Check if pip check passes
    success, output = run_command([sys.executable, "-m", "pip", "check"], "Checking pip dependencies")

    if success:
        print_status(True, "All dependencies properly installed")
    else:
        print_status(False, f"Dependency issues found:\n{output}")

    return success


def check_tests() -> bool:
    """Run a quick test suite validation"""
    print(f"{Colors.YELLOW}Running test validation...{Colors.NC}")

    # Check if pytest is available
    success, _ = run_command([sys.executable, "-m", "pytest", "--version"], "Checking pytest")

    if not success:
        print_status(False, "pytest not installed")
        return False

    # Run a subset of critical tests
    test_files = ["tests/test_server.py", "tests/test_memory_manager.py", "tests/test_version.py"]

    existing_tests = [f for f in test_files if Path(f).exists()]

    if existing_tests:
        success, output = run_command(
            [sys.executable, "-m", "pytest", "-v", "--tb=short"] + existing_tests, "Running critical tests"
        )

        if success:
            print_status(True, "Critical tests passed")
        else:
            print_status(False, "Some tests failed")
            print(output)

        return success
    else:
        print_status(True, "No critical test files found (skipping)")
        return True


def check_documentation() -> bool:
    """Validate documentation completeness"""
    print(f"{Colors.YELLOW}Checking documentation...{Colors.NC}")

    required_docs = [
        ("README.md", "Main documentation"),
        ("CHANGELOG.md", "Change log"),
        ("docs/USER_GUIDE.md", "User guide"),
        ("docs/API_KEY_SETUP.md", "API setup guide"),
        ("docs/README_CN.md", "Chinese documentation"),
        ("docs/MIGRATION_GUIDE.md", "Migration guide"),
    ]

    all_present = True
    for doc_path, description in required_docs:
        path = Path(doc_path)
        if path.exists():
            # Check if file has content
            size = path.stat().st_size
            if size > 100:  # Reasonable minimum size
                print_status(True, f"{description}: {doc_path} ({size:,} bytes)")
            else:
                print_status(False, f"{description}: {doc_path} (too small: {size} bytes)")
                all_present = False
        else:
            print_status(False, f"{description}: {doc_path} (missing)")
            all_present = False

    return all_present


def check_code_quality() -> bool:
    """Run code quality checks"""
    print(f"{Colors.YELLOW}Checking code quality...{Colors.NC}")

    # Check if ruff is available
    success, _ = run_command(["ruff", "--version"], "Checking ruff")

    if success:
        # Run ruff check
        success, output = run_command(["ruff", "check", ".", "--statistics"], "Running ruff linter")

        if success:
            print_status(True, "Code quality checks passed")
        else:
            print_status(False, "Code quality issues found")
            print(output)
    else:
        print_status(True, "ruff not installed (skipping)")
        return True

    return success


def check_git_status() -> bool:
    """Check git repository status"""
    print(f"{Colors.YELLOW}Checking git status...{Colors.NC}")

    # Check if we're in a git repo
    success, _ = run_command(["git", "rev-parse", "--git-dir"], "Checking git repository")

    if not success:
        print_status(False, "Not in a git repository")
        return False

    # Check for uncommitted changes
    success, output = run_command(["git", "status", "--porcelain"], "Checking for uncommitted changes")

    if success and output.strip():
        print_status(False, "Uncommitted changes found:")
        print(output)
        return False
    else:
        print_status(True, "Git working directory clean")

    # Check current branch
    success, branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], "Getting current branch")

    if success:
        branch = branch.strip()
        print_status(True, f"Current branch: {branch}")
        if branch != "main" and branch != "master":
            print(f"{Colors.YELLOW}Warning: Not on main/master branch{Colors.NC}")

    return True


def generate_release_summary() -> dict[str, Any]:
    """Generate a summary of the release"""
    from config import __author__, __updated__, __version__

    summary = {
        "version": __version__,
        "updated": __updated__,
        "author": __author__,
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
    }

    # Count tools
    tools_dir = Path("tools")
    if tools_dir.exists():
        tool_files = list(tools_dir.glob("**/*.py"))
        tool_files = [f for f in tool_files if not f.name.startswith("__")]
        summary["tool_count"] = len(tool_files)

    # Count tests
    tests_dir = Path("tests")
    if tests_dir.exists():
        test_files = list(tests_dir.glob("test_*.py"))
        summary["test_count"] = len(test_files)

    return summary


def main():
    """Main validation function"""
    print_header("Zen MCP Server Release Validation")

    # Track validation results
    validations = []

    # Run all validations
    validations.append(("Version Consistency", check_version_consistency()))
    validations.append(("Dependencies", check_dependencies()))
    validations.append(("Documentation", check_documentation()))
    validations.append(("Code Quality", check_code_quality()))
    validations.append(("Tests", check_tests()))
    validations.append(("Git Status", check_git_status()))

    # Generate summary
    print_header("Release Summary")
    summary = generate_release_summary()

    print(f"Version: {summary['version']}")
    print(f"Updated: {summary['updated']}")
    print(f"Author: {summary['author']}")
    print(f"Python: {summary['python_version']}")
    print(f"Platform: {summary['platform']}")

    if "tool_count" in summary:
        print(f"Tools: {summary['tool_count']}")
    if "test_count" in summary:
        print(f"Tests: {summary['test_count']}")

    # Final result
    print_header("Validation Results")

    all_passed = True
    for name, passed in validations:
        print_status(passed, name)
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print(f"{Colors.GREEN}✓ All validations passed! Ready for release.{Colors.NC}")
        return 0
    else:
        print(f"{Colors.RED}✗ Some validations failed. Please fix issues before releasing.{Colors.NC}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
