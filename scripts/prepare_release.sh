#!/bin/bash

# Zen MCP Server Release Preparation Script
# This script prepares the codebase for a new release

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}    Zen MCP Server Release Preparation          ${NC}"
echo -e "${BLUE}================================================${NC}"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
        exit 1
    fi
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command_exists git; then
    echo -e "${RED}Error: git is not installed${NC}"
    exit 1
fi

if ! command_exists python3; then
    echo -e "${RED}Error: python3 is not installed${NC}"
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Prerequisites checked"
echo

# Step 1: Check git status
echo -e "${YELLOW}Step 1: Checking git status...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${RED}Warning: You have uncommitted changes${NC}"
    echo "Uncommitted files:"
    git status --short
    echo
    read -p "Do you want to continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
print_status 0 "Git status checked"
echo

# Step 2: Run code quality checks
echo -e "${YELLOW}Step 2: Running code quality checks...${NC}"
if [ -f "./code_quality_checks.sh" ]; then
    ./code_quality_checks.sh
    print_status $? "Code quality checks passed"
else
    echo -e "${YELLOW}Warning: code_quality_checks.sh not found, skipping${NC}"
fi
echo

# Step 3: Run tests
echo -e "${YELLOW}Step 3: Running tests...${NC}"
if [ -f "./run_comprehensive_tests.py" ]; then
    python3 ./run_comprehensive_tests.py --quiet
    print_status $? "All tests passed"
else
    echo -e "${YELLOW}Warning: test runner not found, skipping${NC}"
fi
echo

# Step 4: Check version number
echo -e "${YELLOW}Step 4: Checking version number...${NC}"
CURRENT_VERSION=$(python3 -c "from config import __version__; print(__version__)")
echo "Current version: $CURRENT_VERSION"

# Extract version from CHANGELOG.md
if [ -f "CHANGELOG.md" ]; then
    CHANGELOG_VERSION=$(grep -m1 "^## \[" CHANGELOG.md | sed 's/## \[\(.*\)\].*/\1/')
    echo "Latest changelog version: $CHANGELOG_VERSION"
    
    if [ "$CURRENT_VERSION" != "$CHANGELOG_VERSION" ]; then
        echo -e "${YELLOW}Warning: Version mismatch between config.py and CHANGELOG.md${NC}"
    fi
fi
print_status 0 "Version checked"
echo

# Step 5: Validate documentation
echo -e "${YELLOW}Step 5: Validating documentation...${NC}"
REQUIRED_DOCS=(
    "README.md"
    "CHANGELOG.md"
    "docs/USER_GUIDE.md"
    "docs/API_KEY_SETUP.md"
    "docs/README_CN.md"
    "docs/MIGRATION_GUIDE.md"
)

all_docs_present=true
for doc in "${REQUIRED_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "${GREEN}✓${NC} $doc"
    else
        echo -e "${RED}✗${NC} $doc missing"
        all_docs_present=false
    fi
done

if [ "$all_docs_present" = true ]; then
    print_status 0 "All documentation present"
else
    print_status 1 "Some documentation missing"
fi
echo

# Step 6: Check dependencies
echo -e "${YELLOW}Step 6: Checking dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    # Check if all dependencies can be resolved
    python3 -m pip check >/dev/null 2>&1
    print_status $? "Dependencies validated"
else
    echo -e "${RED}Error: requirements.txt not found${NC}"
    exit 1
fi
echo

# Step 7: Create release notes
echo -e "${YELLOW}Step 7: Creating release notes...${NC}"
RELEASE_NOTES_FILE="RELEASE_NOTES_${CURRENT_VERSION}.md"

if [ ! -f "$RELEASE_NOTES_FILE" ]; then
    cat > "$RELEASE_NOTES_FILE" << EOF
# Release Notes for Zen MCP Server v${CURRENT_VERSION}

## Overview
This release includes [brief description of major changes].

## Key Features
- Feature 1
- Feature 2
- Feature 3

## Breaking Changes
- None (or list any breaking changes)

## Bug Fixes
- Fix 1
- Fix 2

## Documentation Updates
- Updated user guide
- Added migration guide
- Enhanced API documentation

## Installation
\`\`\`bash
git clone https://github.com/gptopencn/zen-mcp-server.git
cd zen-mcp-server
./run-server.sh
\`\`\`

## Upgrade Instructions
See [MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) for detailed upgrade instructions.

## Contributors
Thank you to all contributors who made this release possible!

## Full Changelog
See [CHANGELOG.md](CHANGELOG.md) for the complete list of changes.
EOF
    echo -e "${GREEN}✓${NC} Created $RELEASE_NOTES_FILE"
    echo -e "${YELLOW}Please edit the release notes before creating the release${NC}"
else
    echo -e "${GREEN}✓${NC} Release notes already exist: $RELEASE_NOTES_FILE"
fi
echo

# Step 8: Create release checklist
echo -e "${YELLOW}Step 8: Creating release checklist...${NC}"
CHECKLIST_FILE="RELEASE_CHECKLIST_${CURRENT_VERSION}.md"

if [ ! -f "$CHECKLIST_FILE" ]; then
    cat > "$CHECKLIST_FILE" << EOF
# Release Checklist for v${CURRENT_VERSION}

## Pre-release
- [ ] All tests passing
- [ ] Code quality checks passing
- [ ] Version number updated in config.py
- [ ] CHANGELOG.md updated
- [ ] Documentation reviewed and updated
- [ ] Migration guide updated (if needed)
- [ ] Release notes prepared

## Release Process
- [ ] Create git tag: \`git tag -a v${CURRENT_VERSION} -m "Release v${CURRENT_VERSION}"\`
- [ ] Push tag: \`git push origin v${CURRENT_VERSION}\`
- [ ] Create GitHub release
- [ ] Upload release notes
- [ ] Announce in relevant channels

## Post-release
- [ ] Verify release on GitHub
- [ ] Test installation from fresh clone
- [ ] Update version to next development version
- [ ] Monitor issues for any problems

## Rollback Plan
If issues are found:
1. Delete the tag: \`git tag -d v${CURRENT_VERSION}\`
2. Delete remote tag: \`git push origin :refs/tags/v${CURRENT_VERSION}\`
3. Fix issues
4. Re-run release process
EOF
    echo -e "${GREEN}✓${NC} Created $CHECKLIST_FILE"
else
    echo -e "${GREEN}✓${NC} Checklist already exists: $CHECKLIST_FILE"
fi
echo

# Summary
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}    Release Preparation Summary                 ${NC}"
echo -e "${BLUE}================================================${NC}"
echo
echo -e "${GREEN}Release preparation completed successfully!${NC}"
echo
echo "Next steps:"
echo "1. Review and edit: $RELEASE_NOTES_FILE"
echo "2. Follow the checklist in: $CHECKLIST_FILE"
echo "3. When ready, create the release tag:"
echo "   git tag -a v${CURRENT_VERSION} -m \"Release v${CURRENT_VERSION}\""
echo "   git push origin v${CURRENT_VERSION}"
echo
echo -e "${YELLOW}Remember to test everything one more time before releasing!${NC}"