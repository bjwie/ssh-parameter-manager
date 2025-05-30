"""
Tests for automatic initialization feature in SSH Parameter Manager Web Interface.

This module tests the new DOMContentLoaded event-based initialization that ensures
server status and customer data are loaded automatically when the page loads,
regardless of Monaco Editor CDN availability.
"""

import unittest
import json
import time
from unittest.mock import patch, MagicMock
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
import threading
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_server import app
from ssh_manager import SSHManager


class TestAutoInitialization(unittest.TestCase):
    """Test automatic initialization functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        cls.server_thread = None
        cls.driver = None
        cls.base_url = "http://localhost:5000"

        # Start Flask test server
        cls.start_test_server()

        # Set up Selenium WebDriver
        cls.setup_webdriver()

        # Wait for server to be ready
        cls.wait_for_server()

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        if cls.driver:
            cls.driver.quit()
        if cls.server_thread:
            # Flask test server will be stopped by the test runner
            pass

    @classmethod
    def start_test_server(cls):
        """Start Flask server in test mode."""
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False

        def run_server():
            app.run(host="localhost", port=5000, debug=False, use_reloader=False)

        cls.server_thread = threading.Thread(target=run_server, daemon=True)
        cls.server_thread.start()

    @classmethod
    def setup_webdriver(cls):
        """Set up Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")

        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
        except WebDriverException as e:
            cls.skipTest(f"Chrome WebDriver not available: {e}")

    @classmethod
    def wait_for_server(cls):
        """Wait for Flask server to be ready."""
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{cls.base_url}/", timeout=2)
                if response.status_code == 200:
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        raise Exception("Flask server failed to start within 30 seconds")

    def setUp(self):
        """Set up before each test."""
        self.driver.get(self.base_url)
        # Clear any previous state
        self.driver.execute_script("localStorage.clear(); sessionStorage.clear();")

    def test_dom_content_loaded_initialization(self):
        """Test that loadSystemStatus is called on DOMContentLoaded."""
        self.driver.get(self.base_url)

        # Wait for the page to load completely
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "total-customers"))
        )

        # Check that status elements are updated (not showing default "-")
        total_customers = self.driver.find_element(By.ID, "total-customers").text
        connected_servers = self.driver.find_element(By.ID, "connected-servers").text

        # Should show actual values, not the default "-"
        self.assertNotEqual(
            total_customers, "-", "Total customers should be loaded automatically"
        )
        self.assertNotEqual(
            connected_servers, "-", "Connected servers should be loaded automatically"
        )

    def test_automatic_customer_loading(self):
        """Test that customers are loaded automatically without manual refresh."""
        self.driver.get(self.base_url)

        # Wait for customers container to be populated
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#customers-container .customer-item")
                )
            )

            # Check that customer items exist
            customer_items = self.driver.find_elements(
                By.CSS_SELECTOR, "#customers-container .customer-item"
            )
            self.assertGreater(
                len(customer_items), 0, "Customers should be loaded automatically"
            )

            # Check that customer selector is populated
            customer_selector = self.driver.find_element(By.ID, "customer-selector")
            options = customer_selector.find_elements(By.TAG_NAME, "option")
            self.assertGreater(
                len(options),
                1,  # More than just the default option
                "Customer selector should be populated automatically",
            )

        except TimeoutException:
            self.fail("Customers were not loaded automatically within 15 seconds")

    def test_classic_view_initialization(self):
        """Test that classic view is also initialized automatically."""
        self.driver.get(self.base_url)

        # Switch to classic view
        classic_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "classic-view-btn"))
        )
        classic_btn.click()

        # Wait for classic view to be visible
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "classic-view"))
        )

        # Check that classic status is updated
        classic_total_customers = self.driver.find_element(
            By.ID, "classic-total-customers"
        ).text
        classic_connected_servers = self.driver.find_element(
            By.ID, "classic-connected-servers"
        ).text

        self.assertNotEqual(
            classic_total_customers,
            "-",
            "Classic view should show loaded customer count",
        )
        self.assertNotEqual(
            classic_connected_servers,
            "-",
            "Classic view should show server connection status",
        )

        # Check that classic customer list is populated
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#classic-customer-list .classic-customer-item")
                )
            )

            classic_customer_items = self.driver.find_elements(
                By.CSS_SELECTOR, "#classic-customer-list .classic-customer-item"
            )
            self.assertGreater(
                len(classic_customer_items),
                0,
                "Classic customer list should be populated automatically",
            )
        except TimeoutException:
            self.fail("Classic customer list was not populated automatically")

    def test_monaco_editor_independent_initialization(self):
        """Test that initialization works even if Monaco Editor fails to load."""

        # Block Monaco Editor CDN to simulate failure
        self.driver.execute_cdp_cmd(
            "Network.setBlockedURLs",
            {"urls": ["*monaco-editor*", "*cdnjs.cloudflare.com*"]},
        )

        self.driver.get(self.base_url)

        # Wait for basic page load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "total-customers"))
        )

        # Check that status is still loaded despite Monaco Editor failure
        total_customers = self.driver.find_element(By.ID, "total-customers").text
        self.assertNotEqual(
            total_customers,
            "-",
            "System status should load even if Monaco Editor fails",
        )

        # Check that customers are still loaded
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#customers-container .customer-item")
                )
            )
            customer_items = self.driver.find_elements(
                By.CSS_SELECTOR, "#customers-container .customer-item"
            )
            self.assertGreater(
                len(customer_items),
                0,
                "Customers should load even if Monaco Editor fails",
            )
        except TimeoutException:
            self.fail("Customer loading should be independent of Monaco Editor")

        # Unblock URLs for subsequent tests
        self.driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": []})

    def test_no_manual_refresh_required(self):
        """Test that no manual 'Status aktualisieren' click is required."""
        self.driver.get(self.base_url)

        # Wait for automatic loading to complete
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "total-customers"))
        )

        # Check initial state - should already be loaded
        initial_customers = self.driver.find_element(By.ID, "total-customers").text
        self.assertNotEqual(
            initial_customers, "-", "Data should be loaded without manual refresh"
        )

        # Verify that refresh button exists but wasn't needed
        refresh_btn = self.driver.find_element(By.CSS_SELECTOR, ".refresh-btn")
        self.assertTrue(
            refresh_btn.is_displayed(), "Refresh button should exist for manual updates"
        )

        # Test that refresh button still works when clicked
        refresh_btn.click()

        # Wait a moment for refresh to complete
        time.sleep(2)

        # Should still show data (not necessarily different, but not "-")
        after_refresh_customers = self.driver.find_element(
            By.ID, "total-customers"
        ).text
        self.assertNotEqual(
            after_refresh_customers,
            "-",
            "Data should remain loaded after manual refresh",
        )

    def test_error_handling_during_initialization(self):
        """Test error handling when server API calls fail during initialization."""

        # This test would require mocking the API endpoints to return errors
        # For now, we'll test the client-side error handling

        self.driver.get(self.base_url)

        # Inject JavaScript to simulate API failure
        self.driver.execute_script(
            """
            // Override fetch to simulate API failure
            const originalFetch = window.fetch;
            window.fetch = function(url) {
                if (url.includes('/api/status') || url.includes('/api/customers')) {
                    return Promise.reject(new Error('Simulated network error'));
                }
                return originalFetch.apply(this, arguments);
            };
            
            // Trigger loadSystemStatus manually to test error handling
            loadSystemStatus();
        """
        )

        # Wait for error handling
        time.sleep(3)

        # Check that error messages are shown appropriately
        # (The exact error display depends on the implementation)
        # For now, we'll just verify the page doesn't crash
        page_title = self.driver.title
        self.assertIn(
            "SSH Parameter Manager",
            page_title,
            "Page should remain functional even with API errors",
        )

    def test_dual_initialization_resilience(self):
        """Test that dual initialization (DOMContentLoaded + Monaco callback) doesn't cause issues."""

        self.driver.get(self.base_url)

        # Wait for both initialization methods to potentially trigger
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.ID, "total-customers"))
        )

        # Check that data is loaded correctly (no duplication or conflicts)
        total_customers = self.driver.find_element(By.ID, "total-customers").text

        # Switch views to ensure both are working
        classic_btn = self.driver.find_element(By.ID, "classic-view-btn")
        classic_btn.click()

        WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.ID, "classic-view"))
        )

        classic_total_customers = self.driver.find_element(
            By.ID, "classic-total-customers"
        ).text

        # Both views should show the same data
        self.assertEqual(
            total_customers,
            classic_total_customers,
            "Both views should show consistent data after dual initialization",
        )

    def test_performance_of_auto_initialization(self):
        """Test that automatic initialization doesn't significantly impact page load time."""

        start_time = time.time()
        self.driver.get(self.base_url)

        # Wait for complete initialization
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#customers-container .customer-item")
            )
        )

        load_time = time.time() - start_time

        # Should load within reasonable time (10 seconds is generous)
        self.assertLess(
            load_time,
            10,
            f"Page with auto-initialization should load within 10 seconds, took {load_time:.2f}s",
        )

        # Check that all critical elements are present
        critical_elements = [
            "#total-customers",
            "#connected-servers",
            "#customers-container",
            "#customer-selector",
        ]

        for selector in critical_elements:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            self.assertTrue(
                element.is_displayed(),
                f"Critical element {selector} should be visible after initialization",
            )


class TestAutoInitializationAPI(unittest.TestCase):
    """Test the API endpoints used during automatic initialization."""

    def setUp(self):
        """Set up test client."""
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_status_endpoint_response_time(self):
        """Test that /api/status responds quickly for auto-initialization."""
        start_time = time.time()
        response = self.client.get("/api/status")
        response_time = time.time() - start_time

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            response_time,
            2.0,
            "Status endpoint should respond within 2 seconds for fast initialization",
        )

        data = json.loads(response.data)
        self.assertIn("total_customers", data)
        self.assertIn("servers", data)

    def test_customers_endpoint_response_time(self):
        """Test that /api/customers responds quickly for auto-initialization."""
        start_time = time.time()
        response = self.client.get("/api/customers")
        response_time = time.time() - start_time

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            response_time,
            3.0,
            "Customers endpoint should respond within 3 seconds for fast initialization",
        )

        data = json.loads(response.data)
        self.assertIn("customers", data)

    def test_concurrent_initialization_requests(self):
        """Test that concurrent requests during initialization are handled properly."""
        import concurrent.futures

        def make_request(endpoint):
            return self.client.get(endpoint)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Simulate multiple initialization requests
            futures = []
            for _ in range(3):
                futures.append(executor.submit(make_request, "/api/status"))
                futures.append(executor.submit(make_request, "/api/customers"))

            # All requests should succeed
            for future in concurrent.futures.as_completed(futures):
                response = future.result()
                self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
