# TrustVoice Mini App Integration Tests

Comprehensive test suite to validate that mini apps are properly integrated with the backend.

## Test Coverage

### 1. **Smoke Tests** (`smoke_test.py`)
Quick validation of basic integration without full test framework.

**Tests:**
- ✅ Server is running and accessible
- ✅ Static HTML files are served correctly
- ✅ Critical API endpoints exist
- ✅ Voice endpoints accept audio uploads
- ✅ Campaign data has correct structure
- ✅ CORS headers are configured

**Run:** `python tests/smoke_test.py`

### 2. **Frontend Validation** (`test_frontend_validation.py`)
Validates HTML files, JavaScript code, and frontend structure.

**Tests:**
- ✅ All expected HTML files exist
- ✅ Telegram Web App script is included
- ✅ HTML structure is valid
- ✅ API endpoints are called correctly
- ✅ Voice features are implemented
- ✅ Form validation exists
- ✅ Error handling is present
- ✅ Responsive design meta tags
- ✅ Accessibility features
- ✅ Progress indicators in wizards
- ✅ Navigation links work

**Run:** `pytest tests/test_frontend_validation.py -v`

### 3. **Backend Integration** (`test_miniapp_integration.py`)
Tests backend API endpoints that mini apps depend on.

**Tests:**
- ✅ Campaign listing and retrieval
- ✅ Campaign creation
- ✅ Donation processing
- ✅ NGO registration
- ✅ Voice wizard endpoint
- ✅ Voice dictation endpoint
- ✅ Voice search endpoint
- ✅ Analytics endpoints
- ✅ Static file serving
- ✅ CORS configuration
- ✅ Error handling
- ✅ Data validation
- ✅ Performance checks

**Run:** `pytest tests/test_miniapp_integration.py -v`

## Quick Start

### Prerequisites

1. **Start the FastAPI server:**
```bash
uvicorn main:app --reload --port 8001
```

2. **Install test dependencies:**
```bash
pip install -r tests/requirements-test.txt
```

### Run All Tests

```bash
python tests/run_tests.py
```

This will run:
1. Smoke tests (quick validation)
2. Frontend validation (HTML/JS checks)
3. Backend integration (API tests)

### Run Individual Test Suites

**Quick smoke test (30 seconds):**
```bash
python tests/smoke_test.py
```

**Frontend only (no server needed):**
```bash
pytest tests/test_frontend_validation.py -v
```

**Backend only (requires server):**
```bash
pytest tests/test_miniapp_integration.py -v
```

**Specific test class:**
```bash
pytest tests/test_miniapp_integration.py::TestCampaignEndpoints -v
```

**Specific test:**
```bash
pytest tests/test_miniapp_integration.py::TestCampaignEndpoints::test_list_campaigns -v
```

## Test Results Interpretation

### Smoke Test Output

```
✓ Server is running at http://localhost:8001
✓ index.html accessible
✓ campaigns.html accessible
✓ donate.html accessible
✓ Campaign list (GET /api/campaigns/)
✓ Voice wizard (POST /api/voice/wizard-step)
✓ Voice endpoint accepts audio uploads
✓ Campaign objects have required fields

Summary:
  Tests Passed: 15/15 (100.0%)
  Time: 2.34s

✓ All tests passed! Integration looks good.
```

### Expected Test Status

| Test Suite | Expected Pass Rate | Notes |
|------------|-------------------|-------|
| Smoke Tests | 100% | If server is running properly |
| Frontend Validation | 95-100% | Some tests may be skipped |
| Backend Integration | 80-100% | Some endpoints may not be implemented yet |

## Common Issues

### Issue: Server not accessible
**Solution:** Start the FastAPI server:
```bash
uvicorn main:app --reload --port 8001
```

### Issue: Import errors in tests
**Solution:** Install test dependencies:
```bash
pip install -r tests/requirements-test.txt
```

### Issue: Some API tests fail with 404
**Solution:** Check that the endpoint is implemented in the backend routers.

### Issue: Voice endpoint tests fail
**Solution:** Ensure voice routers are properly mounted in main.py:
```python
app.include_router(miniapp_voice_router, prefix="/api/voice", tags=["voice"])
```

## Test Organization

```
tests/
├── README.md                       # This file
├── requirements-test.txt           # Test dependencies
├── run_tests.py                    # Main test runner
├── smoke_test.py                   # Quick smoke tests
├── test_frontend_validation.py     # HTML/JS validation
└── test_miniapp_integration.py     # Backend API tests
```

## Writing New Tests

### Adding a New Smoke Test

Edit `smoke_test.py`:
```python
def test_new_feature(base_url):
    """Test new feature"""
    print(f"\n{BLUE}Testing New Feature:{RESET}")
    
    try:
        response = requests.get(f"{base_url}/api/new-endpoint")
        if response.status_code == 200:
            print_status("New feature works", "success")
            return True
        else:
            print_status("New feature failed", "error")
            return False
    except Exception as e:
        print_status(f"Error: {e}", "error")
        return False
```

### Adding a New Integration Test

Edit `test_miniapp_integration.py`:
```python
class TestNewFeature:
    """Test new feature endpoints"""
    
    def test_new_endpoint(self, client):
        """Test new endpoint"""
        response = client.get("/api/new-endpoint")
        assert response.status_code == 200
        data = response.json()
        assert 'expected_field' in data
```

### Adding a Frontend Validation Test

Edit `test_frontend_validation.py`:
```python
class TestNewFeatureValidation:
    """Validate new feature in HTML"""
    
    @pytest.fixture
    def frontend_dir(self):
        return Path(__file__).parent.parent / "frontend-miniapps"
    
    def test_new_feature_exists(self, frontend_dir):
        """Test that new feature is implemented"""
        content = (frontend_dir / "some-file.html").read_text()
        assert "newFeature" in content
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Mini App Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r tests/requirements-test.txt
    
    - name: Start server
      run: |
        uvicorn main:app --port 8001 &
        sleep 5
    
    - name: Run tests
      run: python tests/run_tests.py
```

## Test Metrics

### Current Coverage

| Component | Files | Tests | Coverage |
|-----------|-------|-------|----------|
| Campaign APIs | 3 endpoints | 12 tests | High |
| Donation APIs | 2 endpoints | 6 tests | Medium |
| NGO APIs | 2 endpoints | 6 tests | Medium |
| Voice APIs | 3 endpoints | 8 tests | High |
| Static Files | 8 files | 16 tests | High |
| Frontend JS | 8 files | 25+ tests | High |

### Test Execution Time

- **Smoke Tests**: ~3-5 seconds
- **Frontend Validation**: ~2-3 seconds
- **Backend Integration**: ~10-15 seconds
- **Total**: ~15-23 seconds

## Debugging Failed Tests

### Enable Verbose Output

```bash
pytest tests/test_miniapp_integration.py -v -s
```

### Run Specific Test with Debugging

```bash
pytest tests/test_miniapp_integration.py::TestVoiceEndpoints::test_voice_wizard_endpoint_exists -v -s --tb=long
```

### Check Server Logs

While tests run, watch server logs:
```bash
tail -f logs/app.log
```

### Test with Different Base URL

```bash
python tests/smoke_test.py http://production-server.com
```

## Integration with Development Workflow

### Before Committing

```bash
# Quick validation
python tests/smoke_test.py

# If all clear, commit
git commit -m "Feature: Add new mini app feature"
```

### Before Deploying

```bash
# Full test suite
python tests/run_tests.py

# Only deploy if all tests pass
```

### After Adding New Mini App

1. Add HTML file validation to `test_frontend_validation.py`
2. Add API endpoint tests to `test_miniapp_integration.py`
3. Add quick check to `smoke_test.py`
4. Run full test suite

## Best Practices

1. **Always run smoke test first** - Catches basic issues quickly
2. **Test frontend independently** - Validates HTML/JS without server
3. **Mock external dependencies** - Don't rely on external APIs in tests
4. **Keep tests fast** - Total runtime should be under 30 seconds
5. **Test error cases** - Not just happy paths
6. **Update tests with features** - When adding features, add tests

## Troubleshooting

### Tests hang indefinitely

**Cause:** Server not responding or wrong URL  
**Solution:** Check server is running: `curl http://localhost:8001`

### Random test failures

**Cause:** Race conditions or shared state  
**Solution:** Each test should be independent, clean database between runs

### Import errors

**Cause:** Missing dependencies  
**Solution:** `pip install -r tests/requirements-test.txt`

### CORS errors in tests

**Cause:** CORS middleware not configured  
**Solution:** Add CORS middleware in main.py:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Contributing

When adding new tests:
1. Follow existing test structure
2. Add descriptive docstrings
3. Use appropriate assertions
4. Keep tests focused and atomic
5. Update this README

## Support

For issues with tests:
1. Check test output for specific errors
2. Review server logs
3. Verify all dependencies installed
4. Ensure database is set up correctly

---

**Last Updated:** December 31, 2025  
**Test Framework:** pytest 7.4+  
**Python Version:** 3.9+
