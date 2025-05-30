"""
Unit tests for automatic initialization feature JavaScript functions.

These tests use pytest and mock to test the JavaScript initialization logic
without requiring a full browser environment.
"""

import unittest
import json
from unittest.mock import patch, MagicMock, Mock
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_server import app


class TestInitializationJavaScriptLogic(unittest.TestCase):
    """Unit tests for JavaScript initialization logic."""
    
    def setUp(self):
        """Set up test environment."""
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_dom_content_loaded_event_structure(self):
        """Test that the HTML contains the correct DOMContentLoaded event listener."""
        response = self.client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check that DOMContentLoaded event listener is present
        self.assertIn("document.addEventListener('DOMContentLoaded'", html_content,
                     "DOMContentLoaded event listener should be present")
        
        # Check that loadSystemStatus is called in the event listener
        self.assertIn("loadSystemStatus();", html_content,
                     "loadSystemStatus should be called in DOMContentLoaded")
        
        # Check that setupClassicEventListeners is called
        self.assertIn("setupClassicEventListeners();", html_content,
                     "setupClassicEventListeners should be called in DOMContentLoaded")
    
    def test_monaco_editor_callback_structure(self):
        """Test that Monaco Editor callback still includes loadSystemStatus."""
        response = self.client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check that require callback includes loadSystemStatus
        monaco_callback_start = html_content.find("require(['vs/editor/editor.main'], function ()")
        monaco_callback_end = html_content.find("});", monaco_callback_start)
        
        if monaco_callback_start != -1 and monaco_callback_end != -1:
            monaco_callback = html_content[monaco_callback_start:monaco_callback_end]
            self.assertIn("loadSystemStatus();", monaco_callback,
                         "Monaco callback should also call loadSystemStatus")
        else:
            self.fail("Monaco Editor callback not found in HTML")
    
    def test_global_variables_initialization(self):
        """Test that global variables are properly declared."""
        response = self.client.get('/')
        html_content = response.data.decode('utf-8')
        
        required_globals = [
            "let editor = null;",
            "let currentCustomer = null;",
            "let originalContent = '';",
            "let isDarkTheme = true;",
            "let customers = [];",
            "let yamlLib = null;",
            "let currentView = 'vscode';",
            "let classicSelectedCustomers = new Set();",
            "let classicCurrentCustomer = null;"
        ]
        
        for global_var in required_globals:
            self.assertIn(global_var, html_content,
                         f"Global variable '{global_var}' should be declared")
    
    def test_function_definitions_present(self):
        """Test that all required functions are defined in the HTML."""
        response = self.client.get('/')
        html_content = response.data.decode('utf-8')
        
        required_functions = [
            "function loadSystemStatus()",
            "function loadCustomers()",
            "function setupClassicEventListeners()",
            "function loadClassicView()",
            "function switchView(",
            "function showStatus(",
            "function showClassicStatus("
        ]
        
        for func in required_functions:
            self.assertIn(func, html_content,
                         f"Function '{func}' should be defined")
    
    def test_css_elements_for_status_display(self):
        """Test that CSS elements for status display are present."""
        response = self.client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check for status display elements
        status_elements = [
            'id="total-customers"',
            'id="connected-servers"', 
            'id="selected-customers"',
            'id="classic-total-customers"',
            'id="classic-connected-servers"',
            'id="customers-container"',
            'id="customer-selector"'
        ]
        
        for element in status_elements:
            self.assertIn(element, html_content,
                         f"Status element '{element}' should be present in HTML")
    
    def test_error_handling_structure(self):
        """Test that error handling structure is present in JavaScript."""
        response = self.client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check for try-catch blocks in critical functions
        self.assertIn("try {", html_content,
                     "Try-catch error handling should be present")
        self.assertIn("catch (error)", html_content,
                     "Error catching should be implemented")
        
        # Check for error status display
        self.assertIn("showStatus('error'", html_content,
                     "Error status display should be implemented")
    
    def test_fetch_api_usage(self):
        """Test that fetch API is used correctly for initialization."""
        response = self.client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check for API endpoints
        api_endpoints = [
            "'/api/status'",
            "'/api/customers'",
            "'/api/customer/'"
        ]
        
        for endpoint in api_endpoints:
            self.assertIn(endpoint, html_content,
                         f"API endpoint '{endpoint}' should be used")
        
        # Check for proper fetch usage
        self.assertIn("await fetch(", html_content,
                     "Async fetch should be used")
        self.assertIn("response.ok", html_content,
                     "Response status checking should be implemented")


class TestAPIEndpointsForInitialization(unittest.TestCase):
    """Test API endpoints used during automatic initialization."""
    
    def setUp(self):
        """Set up test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    @patch('ssh_manager.SSHManager')
    def test_status_endpoint_returns_required_data(self, mock_ssh_manager):
        """Test that /api/status returns all required data for initialization."""
        # Mock SSH manager
        mock_instance = MagicMock()
        mock_instance.get_connection_status.return_value = {
            'tennis-software.de': {
                'connected': True,
                'customers': ['test', 'tsv-deizisau']
            }
        }
        mock_ssh_manager.return_value = mock_instance
        
        response = self.client.get('/api/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        
        # Check required fields for initialization
        required_fields = ['total_customers', 'servers']
        for field in required_fields:
            self.assertIn(field, data,
                         f"Field '{field}' should be in status response")
        
        # Check servers structure
        self.assertIsInstance(data['servers'], dict,
                            "Servers should be a dictionary")
        
        # Check total_customers is a number
        self.assertIsInstance(data['total_customers'], int,
                            "Total customers should be an integer")
    
    @patch('ssh_manager.SSHManager')
    def test_customers_endpoint_returns_required_data(self, mock_ssh_manager):
        """Test that /api/customers returns properly formatted data."""
        # Mock SSH manager
        mock_instance = MagicMock()
        mock_instance.get_all_customers.return_value = {
            'tennis-software.de:test': {
                'server': 'tennis-software.de',
                'customer': 'test',
                'path': '/var/www/test/app/config/parameters.yml',
                'description': 'Test Customer',
                'host': '192.168.1.100'
            }
        }
        mock_ssh_manager.return_value = mock_instance
        
        response = self.client.get('/api/customers')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        
        # Check required structure
        self.assertIn('customers', data,
                     "Response should contain 'customers' field")
        
        self.assertIsInstance(data['customers'], dict,
                            "Customers should be a dictionary")
        
        # Check customer data structure
        if data['customers']:
            first_customer = next(iter(data['customers'].values()))
            required_customer_fields = ['server', 'customer', 'path', 'description', 'host']
            
            for field in required_customer_fields:
                self.assertIn(field, first_customer,
                             f"Customer should have '{field}' field")
    
    def test_status_endpoint_error_handling(self):
        """Test error handling in status endpoint."""
        with patch('ssh_manager.SSHManager') as mock_ssh_manager:
            # Mock SSH manager to raise exception
            mock_ssh_manager.side_effect = Exception("Connection failed")
            
            response = self.client.get('/api/status')
            
            # Should still return 200 with error information
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            self.assertIn('error', data,
                         "Error information should be included in response")
    
    def test_customers_endpoint_error_handling(self):
        """Test error handling in customers endpoint."""
        with patch('ssh_manager.SSHManager') as mock_ssh_manager:
            # Mock SSH manager to raise exception
            mock_ssh_manager.side_effect = Exception("Connection failed")
            
            response = self.client.get('/api/customers')
            
            # Should handle error gracefully
            self.assertIn(response.status_code, [200, 500],
                         "Should handle errors gracefully")
    
    def test_concurrent_api_requests(self):
        """Test that API can handle concurrent requests during initialization."""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = self.client.get('/api/status')
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        for status_code in results:
            self.assertEqual(status_code, 200,
                           "All concurrent requests should succeed")


class TestInitializationTiming(unittest.TestCase):
    """Test timing aspects of automatic initialization."""
    
    def setUp(self):
        """Set up test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_page_load_performance(self):
        """Test that page loads quickly despite automatic initialization."""
        import time
        
        start_time = time.time()
        response = self.client.get('/')
        end_time = time.time()
        
        load_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(load_time, 2.0,
                       f"Page should load within 2 seconds, took {load_time:.2f}s")
    
    def test_api_response_times(self):
        """Test that API endpoints respond quickly for initialization."""
        import time
        
        endpoints = ['/api/status', '/api/customers']
        
        for endpoint in endpoints:
            start_time = time.time()
            response = self.client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            self.assertEqual(response.status_code, 200)
            self.assertLess(response_time, 1.5,
                           f"{endpoint} should respond within 1.5 seconds, took {response_time:.2f}s")


class TestInitializationRobustness(unittest.TestCase):
    """Test robustness of automatic initialization."""
    
    def setUp(self):
        """Set up test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_initialization_with_empty_data(self):
        """Test initialization handles empty data gracefully."""
        with patch('ssh_manager.SSHManager') as mock_ssh_manager:
            # Mock empty data
            mock_instance = MagicMock()
            mock_instance.get_connection_status.return_value = {}
            mock_instance.get_all_customers.return_value = {}
            mock_ssh_manager.return_value = mock_instance
            
            # Status endpoint
            response = self.client.get('/api/status')
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            self.assertEqual(data['total_customers'], 0,
                           "Should handle zero customers gracefully")
            
            # Customers endpoint
            response = self.client.get('/api/customers')
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            self.assertEqual(len(data['customers']), 0,
                           "Should handle empty customer list gracefully")
    
    def test_initialization_with_partial_data(self):
        """Test initialization handles partial/corrupted data."""
        with patch('ssh_manager.SSHManager') as mock_ssh_manager:
            # Mock partial data
            mock_instance = MagicMock()
            mock_instance.get_connection_status.return_value = {
                'server1': {'connected': True},
                'server2': None  # Corrupted data
            }
            mock_instance.get_all_customers.return_value = {
                'server1:customer1': {
                    'server': 'server1',
                    'customer': 'customer1'
                    # Missing some fields
                }
            }
            mock_ssh_manager.return_value = mock_instance
            
            response = self.client.get('/api/status')
            self.assertEqual(response.status_code, 200,
                           "Should handle partial data gracefully")
            
            response = self.client.get('/api/customers')
            self.assertEqual(response.status_code, 200,
                           "Should handle partial customer data gracefully")


if __name__ == '__main__':
    unittest.main(verbosity=2) 