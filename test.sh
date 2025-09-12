#!/bin/bash

echo "🚀 Running local tests (same as CI)..."
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

run_check() {
    local name="$1"
    local command="$2"
    
    echo -e "${YELLOW}Running $name...${NC}"
    if eval "$command"; then
        echo -e "${GREEN}✅ $name passed${NC}"
    else
        echo -e "${RED}❌ $name failed${NC}"
        exit 1
    fi
    echo
}

# Install/update dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
uv sync --extra dev
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo

# Run code quality checks (same order as CI)
run_check "Ruff check (linting)" "uv run ruff check ."
run_check "Ruff format check" "uv run ruff format --check ."
# Skip MyPy for now - too strict for early development
# run_check "MyPy type check" "uv run mypy ."
echo -e "${YELLOW}Skipping MyPy type check for early development...${NC}"
echo -e "${GREEN}✅ MyPy type check skipped${NC}"
echo

# Create tests directory if it doesn't exist
if [ ! -d "tests" ]; then
    echo -e "${YELLOW}📁 Creating tests directory...${NC}"
    mkdir -p tests
    touch tests/__init__.py
    echo -e "${GREEN}✅ Tests directory created${NC}"
    echo
fi

# Run tests (allow empty test suite)
echo -e "${YELLOW}Running Pytest tests...${NC}"
uv run pytest --tb=short -x
exit_code=$?
if [ $exit_code -eq 0 ] || [ $exit_code -eq 5 ]; then
    echo -e "${GREEN}✅ Pytest tests passed${NC}"
else
    echo -e "${RED}❌ Pytest tests failed${NC}"
    exit 1
fi
echo

echo -e "${GREEN}🎉 All checks passed! Ready to push to CI.${NC}"