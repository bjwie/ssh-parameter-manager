#!/usr/bin/env python3
"""
Test runner for automatic initialization feature tests.

This script runs all tests related to the automatic initialization feature
including Selenium browser tests, unit tests, and API tests.
"""

import sys
import os
import unittest
import argparse
import time
from io import StringIO

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_unit_tests():
    """Run unit tests for automatic initialization."""
    print("🧪 Running Unit Tests for Auto-Initialization...")
    print("=" * 60)
    
    # Import test modules
    from test_auto_initialization_unit import (
        TestInitializationJavaScriptLogic,
        TestAPIEndpointsForInitialization,
        TestInitializationTiming,
        TestInitializationRobustness
    )
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestInitializationJavaScriptLogic,
        TestAPIEndpointsForInitialization,
        TestInitializationTiming,
        TestInitializationRobustness
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_browser_tests():
    """Run Selenium browser tests for automatic initialization."""
    print("\n🌐 Running Browser Tests for Auto-Initialization...")
    print("=" * 60)
    
    try:
        from test_auto_initialization import (
            TestAutoInitialization,
            TestAutoInitializationAPI
        )
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add test classes
        test_classes = [
            TestAutoInitialization,
            TestAutoInitializationAPI
        ]
        
        for test_class in test_classes:
            tests = loader.loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"⚠️  Browser tests skipped: {e}")
        print("   Install selenium and chrome driver to run browser tests")
        return True  # Don't fail if selenium is not available


def run_performance_tests():
    """Run performance tests for automatic initialization."""
    print("\n⚡ Running Performance Tests for Auto-Initialization...")
    print("=" * 60)
    
    from web_server import app
    import requests
    import threading
    import time
    
    # Start test server
    app.config['TESTING'] = True
    
    def start_server():
        app.run(host='localhost', port=5001, debug=False, use_reloader=False)
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    base_url = "http://localhost:5001"
    
    try:
        # Test 1: Page load time
        print("📊 Testing page load time...")
        start_time = time.time()
        response = requests.get(base_url, timeout=10)
        load_time = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ Page loaded in {load_time:.2f} seconds")
            if load_time > 3.0:
                print(f"⚠️  Warning: Page load time ({load_time:.2f}s) is longer than expected")
        else:
            print(f"❌ Page failed to load: {response.status_code}")
            return False
        
        # Test 2: API response times
        print("\n📊 Testing API response times...")
        api_endpoints = ['/api/status', '/api/customers']
        
        for endpoint in api_endpoints:
            start_time = time.time()
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ {endpoint}: {response_time:.2f} seconds")
                if response_time > 2.0:
                    print(f"⚠️  Warning: {endpoint} response time ({response_time:.2f}s) is longer than expected")
            else:
                print(f"❌ {endpoint} failed: {response.status_code}")
                return False
        
        # Test 3: Concurrent requests
        print("\n📊 Testing concurrent request handling...")
        
        def make_request():
            return requests.get(f"{base_url}/api/status", timeout=5)
        
        threads = []
        results = []
        
        start_time = time.time()
        
        # Create 10 concurrent requests
        for _ in range(10):
            thread = threading.Thread(target=lambda: results.append(make_request()))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        concurrent_time = time.time() - start_time
        
        successful_requests = sum(1 for r in results if r.status_code == 200)
        print(f"✅ {successful_requests}/10 concurrent requests successful in {concurrent_time:.2f} seconds")
        
        if successful_requests < 10:
            print(f"⚠️  Warning: Some concurrent requests failed")
        
        return successful_requests >= 8  # Allow some tolerance
        
    except Exception as e:
        print(f"❌ Performance tests failed: {e}")
        return False


def run_integration_tests():
    """Run integration tests for automatic initialization."""
    print("\n🔗 Running Integration Tests for Auto-Initialization...")
    print("=" * 60)
    
    from web_server import app
    import json
    
    app.config['TESTING'] = True
    client = app.test_client()
    
    try:
        # Test 1: Full page integration
        print("📊 Testing full page integration...")
        response = client.get('/')
        
        if response.status_code == 200:
            html_content = response.data.decode('utf-8')
            
            # Check for key initialization elements
            required_elements = [
                "document.addEventListener('DOMContentLoaded'",
                "loadSystemStatus();",
                "setupClassicEventListeners();",
                'id="total-customers"',
                'id="customers-container"',
                'id="customer-selector"'
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in html_content:
                    missing_elements.append(element)
            
            if not missing_elements:
                print("✅ All required initialization elements present")
            else:
                print(f"❌ Missing elements: {missing_elements}")
                return False
        else:
            print(f"❌ Page failed to load: {response.status_code}")
            return False
        
        # Test 2: API data consistency
        print("\n📊 Testing API data consistency...")
        status_response = client.get('/api/status')
        customers_response = client.get('/api/customers')
        
        if status_response.status_code == 200 and customers_response.status_code == 200:
            status_data = json.loads(status_response.data)
            customers_data = json.loads(customers_response.data)
            
            # Check data consistency
            reported_customers = status_data.get('total_customers', 0)
            actual_customers = len(customers_data.get('customers', {}))
            
            if reported_customers == actual_customers:
                print(f"✅ Data consistency check passed: {actual_customers} customers")
            else:
                print(f"⚠️  Data inconsistency: status reports {reported_customers}, customers endpoint has {actual_customers}")
        else:
            print(f"❌ API endpoints failed: status={status_response.status_code}, customers={customers_response.status_code}")
            return False
        
        # Test 3: Error handling integration
        print("\n📊 Testing error handling integration...")
        
        # Test with invalid customer ID
        invalid_response = client.get('/api/customer/invalid_customer_id/parameters')
        if invalid_response.status_code in [404, 500]:
            print("✅ Error handling for invalid customer ID works correctly")
        else:
            print(f"⚠️  Unexpected response for invalid customer: {invalid_response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration tests failed: {e}")
        return False


def print_test_summary(results):
    """Print a summary of all test results."""
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:30} {status}")
    
    print("-" * 60)
    print(f"Total: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("🎉 All automatic initialization tests passed!")
        return True
    else:
        print("💥 Some tests failed. Please check the output above.")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Run automatic initialization tests')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--browser', action='store_true', help='Run only browser tests')
    parser.add_argument('--performance', action='store_true', help='Run only performance tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    
    args = parser.parse_args()
    
    # If no specific test type is specified, run all
    if not any([args.unit, args.browser, args.performance, args.integration]):
        args.all = True
    
    print("🚀 SSH Parameter Manager - Auto-Initialization Test Suite")
    print("=" * 60)
    print("Testing automatic page loading functionality")
    print("This ensures server status and customers load without manual refresh")
    print("=" * 60)
    
    results = {}
    
    # Run selected test suites
    if args.unit or args.all:
        results['Unit Tests'] = run_unit_tests()
    
    if args.browser or args.all:
        results['Browser Tests'] = run_browser_tests()
    
    if args.performance or args.all:
        results['Performance Tests'] = run_performance_tests()
    
    if args.integration or args.all:
        results['Integration Tests'] = run_integration_tests()
    
    # Print summary and exit with appropriate code
    success = print_test_summary(results)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main() 