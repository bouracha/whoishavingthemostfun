#!/bin/bash
# Test runner script for local development

set -e

echo "🧪 ELO Rating System - Test Runner"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment not detected. Activating venv...${NC}"
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}❌ No virtual environment found. Please run: python3 -m venv venv && source venv/bin/activate${NC}"
        exit 1
    fi
fi

# Install test dependencies
echo -e "${BLUE}📦 Installing test dependencies...${NC}"
pip install -r tests/requirements.txt --quiet

# Create test database directories
echo -e "${BLUE}📁 Creating test database directories...${NC}"
mkdir -p database/{chess,pingpong,backgammon}

# Run tests based on argument
case "${1:-all}" in
    "unit")
        echo -e "${BLUE}🔬 Running unit tests...${NC}"
        pytest tests/unit/ -v
        ;;
    "integration")
        echo -e "${BLUE}🔗 Running integration tests...${NC}"
        pytest tests/integration/ -v
        ;;
    "coverage")
        echo -e "${BLUE}📊 Running tests with coverage...${NC}"
        pytest tests/ --cov=code --cov-report=html --cov-report=term-missing
        echo -e "${GREEN}📈 Coverage report saved to htmlcov/index.html${NC}"
        ;;
    "lint")
        echo -e "${BLUE}🔍 Running code quality checks...${NC}"
        echo "Checking with flake8..."
        flake8 code/ server.py --count --select=E9,F63,F7,F82 --show-source --statistics
        echo "Checking formatting with black..."
        black --check --diff code/ server.py
        echo "Checking imports with isort..."
        isort --check-only --diff code/ server.py
        echo -e "${GREEN}✅ All code quality checks passed${NC}"
        ;;
    "security")
        echo -e "${BLUE}🔒 Running security scans...${NC}"
        echo "Running bandit security scan..."
        bandit -r code/ server.py
        echo "Checking for known vulnerabilities..."
        safety check
        echo -e "${GREEN}✅ Security scans completed${NC}"
        ;;
    "build")
        echo -e "${BLUE}🏗️  Testing build and server startup...${NC}"
        echo "Testing Flask server startup..."
        timeout 30s python server.py &
        SERVER_PID=$!
        sleep 5
        
        if curl -f http://localhost:8080/api/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Server started successfully${NC}"
        else
            echo -e "${RED}❌ Server failed to start or respond${NC}"
            kill $SERVER_PID 2>/dev/null || true
            exit 1
        fi
        
        kill $SERVER_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Build test completed${NC}"
        ;;
    "all"|*)
        echo -e "${BLUE}🚀 Running full test suite...${NC}"
        
        echo -e "\n${BLUE}🔬 Unit Tests${NC}"
        pytest tests/unit/ -v --tb=short
        
        echo -e "\n${BLUE}🔗 Integration Tests${NC}"
        pytest tests/integration/ -v --tb=short
        
        echo -e "\n${BLUE}📊 Coverage Report${NC}"
        pytest tests/ --cov=code --cov-report=term-missing --tb=short
        
        echo -e "\n${GREEN}✅ All tests completed successfully!${NC}"
        ;;
esac

echo -e "\n${GREEN}🎉 Test run completed!${NC}"
echo ""
echo "Available commands:"
echo "  ./run_tests.sh unit        - Run unit tests only"
echo "  ./run_tests.sh integration - Run integration tests only"  
echo "  ./run_tests.sh coverage    - Run tests with coverage report"
echo "  ./run_tests.sh lint        - Run code quality checks"
echo "  ./run_tests.sh security    - Run security scans"
echo "  ./run_tests.sh build       - Test server startup"
echo "  ./run_tests.sh all         - Run full test suite (default)"