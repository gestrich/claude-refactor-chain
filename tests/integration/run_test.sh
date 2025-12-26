#!/bin/bash
# Run ClaudeStep integration tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}ClaudeStep Integration Test Runner${NC}"
echo "===================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi
echo "  ✓ Python 3 found: $(python3 --version)"

# Check pytest
if ! python3 -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}Warning: pytest not installed${NC}"
    echo "  Installing pytest..."
    pip install pytest
fi
echo "  ✓ pytest installed"

# Check gh CLI
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: gh CLI not found${NC}"
    echo "  Install with: brew install gh"
    exit 1
fi
echo "  ✓ gh CLI found: $(gh --version | head -n1)"

# Check gh auth
if ! gh auth status &> /dev/null; then
    echo -e "${RED}Error: gh CLI not authenticated${NC}"
    echo "  Run: gh auth login"
    exit 1
fi
echo "  ✓ gh authenticated"

# Check git config
if ! git config user.name &> /dev/null || ! git config user.email &> /dev/null; then
    echo -e "${YELLOW}Warning: git not configured${NC}"
    echo "  Setting temporary git config..."
    git config --global user.name "Integration Test"
    git config --global user.email "test@example.com"
fi
echo "  ✓ git configured"

echo ""
echo "Running integration tests..."
echo "This may take 5-10 minutes..."
echo ""

# Run the test
cd "$(dirname "$0")/../.."
pytest tests/integration/test_workflow_e2e.py -v -s -m integration "$@"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo ""
    echo -e "${RED}✗ Tests failed${NC}"
fi

exit $exit_code
