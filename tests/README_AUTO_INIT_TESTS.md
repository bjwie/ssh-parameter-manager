# Automatic Initialization Tests

This directory contains comprehensive tests for the **automatic initialization feature** of the SSH Parameter Manager web interface.

## 🎯 What This Feature Does

The automatic initialization feature ensures that:
- ✅ Server status and customer data load **automatically** when the page opens
- ✅ No manual "Status aktualisieren" button click is required
- ✅ Both VSCode and Classic views work immediately upon loading
- ✅ Initialization works even if Monaco Editor CDN fails
- ✅ Robust error handling for network issues

## 📋 Test Coverage

### 1. Browser Tests (`test_auto_initialization.py`)
**Selenium-based end-to-end tests**

- `test_dom_content_loaded_initialization()` - Verifies DOMContentLoaded event triggers loading
- `test_automatic_customer_loading()` - Ensures customers load without manual interaction
- `test_classic_view_initialization()` - Tests classic view auto-loading
- `test_monaco_editor_independent_initialization()` - Verifies independence from Monaco Editor
- `test_no_manual_refresh_required()` - Confirms no manual refresh is needed
- `test_error_handling_during_initialization()` - Tests error scenarios
- `test_dual_initialization_resilience()` - Tests both DOMContentLoaded + Monaco callbacks
- `test_performance_of_auto_initialization()` - Performance impact measurement

### 2. Unit Tests (`test_auto_initialization_unit.py`)
**Fast unit tests for JavaScript and API logic**

#### JavaScript Logic Tests:
- `test_dom_content_loaded_event_structure()` - HTML contains correct event listeners
- `test_monaco_editor_callback_structure()` - Monaco callback includes loadSystemStatus
- `test_global_variables_initialization()` - All required globals are declared
- `test_function_definitions_present()` - Required functions exist
- `test_css_elements_for_status_display()` - Status display elements present
- `test_error_handling_structure()` - Error handling code exists
- `test_fetch_api_usage()` - API calls are implemented correctly

#### API Endpoint Tests:
- `test_status_endpoint_returns_required_data()` - /api/status returns correct format
- `test_customers_endpoint_returns_required_data()` - /api/customers returns correct format
- `test_status_endpoint_error_handling()` - Error handling in status endpoint
- `test_customers_endpoint_error_handling()` - Error handling in customers endpoint
- `test_concurrent_api_requests()` - Concurrent request handling

#### Performance Tests:
- `test_page_load_performance()` - Page loads within time limits
- `test_api_response_times()` - API endpoints respond quickly

#### Robustness Tests:
- `test_initialization_with_empty_data()` - Handles empty/missing data
- `test_initialization_with_partial_data()` - Handles corrupted data

### 3. Test Runner (`run_auto_init_tests.py`)
**Comprehensive test orchestration**

- **Unit Tests**: Fast JavaScript and API logic validation
- **Browser Tests**: Full end-to-end Selenium testing
- **Performance Tests**: Load time and responsiveness measurement
- **Integration Tests**: Full-stack functionality verification

## 🚀 Running the Tests

### Prerequisites
```bash
# Install dependencies
pip install selenium requests

# For browser tests, install Chrome and ChromeDriver
# Chrome: https://www.google.com/chrome/
# ChromeDriver: https://chromedriver.chromium.org/
```

### Run All Tests
```bash
cd tests/
python run_auto_init_tests.py
```

### Run Specific Test Types
```bash
# Unit tests only (fast)
python run_auto_init_tests.py --unit

# Browser tests only (requires Chrome)
python run_auto_init_tests.py --browser

# Performance tests only
python run_auto_init_tests.py --performance

# Integration tests only
python run_auto_init_tests.py --integration
```

### Run Individual Test Files
```bash
# Browser tests
python -m pytest test_auto_initialization.py -v

# Unit tests
python -m pytest test_auto_initialization_unit.py -v

# Or with unittest
python -m unittest test_auto_initialization.py -v
python -m unittest test_auto_initialization_unit.py -v
```

## 📊 Expected Results

### ✅ Successful Test Run Output:
```
🚀 SSH Parameter Manager - Auto-Initialization Test Suite
============================================================
Testing automatic page loading functionality
This ensures server status and customers load without manual refresh
============================================================

🧪 Running Unit Tests for Auto-Initialization...
============================================================
test_dom_content_loaded_event_structure ... ok
test_monaco_editor_callback_structure ... ok
test_global_variables_initialization ... ok
...

🌐 Running Browser Tests for Auto-Initialization...
============================================================
test_dom_content_loaded_initialization ... ok
test_automatic_customer_loading ... ok
test_classic_view_initialization ... ok
...

⚡ Running Performance Tests for Auto-Initialization...
============================================================
📊 Testing page load time...
✅ Page loaded in 1.23 seconds
📊 Testing API response times...
✅ /api/status: 0.45 seconds
✅ /api/customers: 0.67 seconds
...

🔗 Running Integration Tests for Auto-Initialization...
============================================================
📊 Testing full page integration...
✅ All required initialization elements present
📊 Testing API data consistency...
✅ Data consistency check passed: 2 customers
...

============================================================
🏁 TEST SUMMARY
============================================================
Unit Tests                    ✅ PASSED
Browser Tests                 ✅ PASSED
Performance Tests             ✅ PASSED
Integration Tests             ✅ PASSED
------------------------------------------------------------
Total: 4/4 test suites passed
🎉 All automatic initialization tests passed!
```

## 🔧 Test Configuration

### Browser Test Configuration
- **Headless Chrome**: Tests run without opening browser windows
- **Timeout Settings**: 10-15 second timeouts for network operations
- **Screen Resolution**: 1920x1080 for consistent testing
- **Network Simulation**: Can block CDNs to test fallback behavior

### Performance Thresholds
- **Page Load Time**: < 3 seconds (warning > 3s)
- **API Response Time**: < 2 seconds per endpoint (warning > 2s)
- **Concurrent Requests**: Handle 10+ simultaneous requests
- **Initialization Time**: Complete loading < 10 seconds

### Error Scenarios Tested
- 🌐 **Network Failures**: API endpoints unreachable
- 🖥️ **CDN Failures**: Monaco Editor CDN blocked
- 📊 **Data Issues**: Empty, partial, or corrupted server responses
- ⏱️ **Timeout Scenarios**: Slow server responses
- 🔄 **Concurrent Access**: Multiple users loading simultaneously

## 🐛 Troubleshooting

### Common Issues

**Browser Tests Fail:**
```bash
# Install Chrome and ChromeDriver
sudo apt-get install google-chrome-stable  # Linux
brew install chromedriver                   # macOS

# Or run without browser tests
python run_auto_init_tests.py --unit --performance --integration
```

**Server Connection Errors:**
```bash
# Make sure SSH configuration is set up
cp ssh_config.example.yml ssh_config.yml
# Edit ssh_config.yml with your server details

# Start web server in another terminal
python web_server.py
```

**Performance Test Timeouts:**
```bash
# Check if server is running
curl http://localhost:5000/api/status

# Increase timeout in test configuration if server is slow
```

## 📈 Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Auto-Initialization Tests
  run: |
    cd tests/
    python run_auto_init_tests.py --unit --integration
    # Skip browser tests in CI unless Chrome is available
```

## 🔍 Test Development

### Adding New Tests

1. **For Browser Testing**: Add to `TestAutoInitialization` class
2. **For Unit Testing**: Add to appropriate class in unit test file
3. **For API Testing**: Add to `TestAPIEndpointsForInitialization` class

### Test Naming Convention
- `test_functionality_being_tested()` - Clear, descriptive names
- Group related tests in same class
- Use docstrings to explain test purpose

### Mock Usage
Tests use Python `unittest.mock` to simulate:
- SSH connections
- API responses  
- Network failures
- Timing conditions

This ensures tests run quickly and reliably without requiring actual SSH servers.

---

## 📚 Related Documentation

- [Main README](../README.md) - Project overview
- [Contributing Guidelines](../CONTRIBUTING.md) - Development workflow  
- [Changelog](../CHANGELOG.md) - Feature history

---

**💡 Need Help?** Check the test output for detailed error messages, or review the implementation in `ssh_web_interface.html` lines 1083-1103 for the DOMContentLoaded initialization code. 