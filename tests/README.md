# Testing Documentation

This directory contains the comprehensive test suite for the ELO Rating System.

## Structure

```
tests/
├── unit/                    # Automated unit tests
│   ├── test_elo_calculations.py
│   ├── test_player_management.py
│   └── test_config.py
├── integration/             # Automated API tests  
│   ├── test_api_endpoints.py
│   └── test_chart_generation.py
├── manual/                  # Manual test checklists
│   ├── frontend_checklist.md
│   └── deployment_checklist.md
├── fixtures/               # Test data and helpers
│   ├── sample_chess_player.csv
│   ├── sample_pingpong_player.csv
│   ├── sample_backgammon_player.csv
│   └── test_data.py
├── conftest.py            # Pytest configuration
├── requirements.txt       # Test dependencies
└── README.md             # This file
```

## Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Create test database directories
mkdir -p database/{chess,pingpong,backgammon}
```

### Automated Tests
```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run integration tests only  
pytest tests/integration/

# Run with coverage
pytest tests/ --cov=code --cov-report=html

# Run specific test file
pytest tests/unit/test_elo_calculations.py -v

# Run specific test method
pytest tests/unit/test_elo_calculations.py::TestELOCalculations::test_equal_ratings_win -v
```

### Manual Tests
1. **Frontend Testing**: Follow `tests/manual/frontend_checklist.md`
2. **Deployment Testing**: Follow `tests/manual/deployment_checklist.md`

## Test Coverage

### Unit Tests
- ✅ ELO calculation accuracy and edge cases
- ✅ Player creation and deletion
- ✅ Game configuration (K-factors)
- ✅ Input validation and error handling

### Integration Tests  
- ✅ Flask API endpoints (`/api/health`, `/api/players/<game>`)
- ✅ Chart generation subprocess calls
- ✅ CORS headers and error responses
- ✅ Static file serving

### Manual Tests
- ✅ Frontend user interface and interactions
- ✅ Cross-browser compatibility
- ✅ Mobile responsiveness  
- ✅ Production deployment verification
- ✅ Performance and security checks

## Continuous Integration

Tests run automatically on GitHub Actions for:
- **Python versions**: 3.9, 3.10, 3.11
- **Test execution**: Unit and integration tests
- **Code quality**: Linting with flake8, formatting with black
- **Security**: Bandit security scanning, safety vulnerability checks
- **Build verification**: Server startup, chart generation

## Test Data

Sample test data is provided in `fixtures/`:
- Player CSV files with realistic game histories
- Test scenarios for different rating situations
- Helper functions for creating temporary test databases

## Writing New Tests

### Unit Tests
```python
# tests/unit/test_new_feature.py
import pytest
from code.new_module import new_function

class TestNewFeature:
    def test_basic_functionality(self):
        result = new_function(input_data)
        assert result == expected_output
    
    def test_edge_case(self):
        with pytest.raises(ValueError):
            new_function(invalid_input)
```

### Integration Tests
```python  
# tests/integration/test_new_endpoint.py
def test_new_api_endpoint(client):
    response = client.post('/api/new-endpoint',
                          json={'data': 'test'})
    assert response.status_code == 200
    assert response.json['status'] == 'success'
```

### Manual Test Updates
When adding new features:
1. Update relevant checklist in `tests/manual/`
2. Add new test scenarios
3. Document expected behaviors
4. Include cross-browser considerations

## Debugging Tests

### Common Issues
- **Import errors**: Make sure you're running from project root
- **Database path issues**: Tests use temporary directories
- **Mock failures**: Verify mock patches match actual function signatures

### Useful Commands
```bash
# Run with verbose output
pytest tests/ -v -s

# Run and drop into debugger on failure
pytest tests/ --pdb

# Run only failed tests from last run
pytest tests/ --lf

# Show local variables in tracebacks
pytest tests/ -l
```

## Performance Testing

For performance testing:
1. Use `pytest-benchmark` for timing critical functions
2. Profile chart generation with large datasets
3. Load test API endpoints with multiple concurrent requests
4. Monitor memory usage during batch operations

## Security Testing

Security considerations:
- Input validation for player names
- SQL injection prevention (though we use CSV files)
- XSS prevention in frontend
- CORS configuration verification
- SSL/TLS certificate validation

Run security scans:
```bash
bandit -r code/ server.py
safety check
```

## Contributing

When contributing tests:
1. Follow existing naming conventions
2. Include docstrings explaining test purpose
3. Use descriptive test names
4. Add parametrized tests for multiple scenarios
5. Update this README if adding new test categories