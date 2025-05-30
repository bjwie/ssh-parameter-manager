#!/usr/bin/env python3
"""
Tests for the web server module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os

# Import the web server module
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_server import app, init_ssh_manager


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_ssh_manager():
    """Create a mock SSH manager."""
    with patch("web_server.ssh_manager") as mock:
        mock_instance = MagicMock()
        mock_instance.list_all_customers.return_value = {
            "customer1": {
                "server": "production",
                "path": "/var/www/customer1/app/config/parameters.yml",
                "description": "Test Customer 1",
            }
        }
        mock_instance.config = {
            "servers": {
                "production": {
                    "host": "test-server.com",
                    "customers": {
                        "customer1": {
                            "parameters_path": "/var/www/customer1/app/config/parameters.yml"
                        }
                    },
                }
            }
        }
        mock.return_value = mock_instance
        yield mock_instance


class TestWebServer:
    """Test cases for the web server."""

    def test_index_route(self, client):
        """Test the index route serves the HTML file."""
        with patch("web_server.send_from_directory") as mock_send:
            mock_send.return_value = "<html>Test</html>"
            response = client.get("/")
            mock_send.assert_called_once_with(".", "ssh_web_interface.html")

    def test_get_customers_success(self, client, mock_ssh_manager):
        """Test successful customer retrieval."""
        with patch("web_server.ssh_manager", mock_ssh_manager):
            response = client.get("/api/customers")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert "customers" in data
            assert data["count"] == 1

    def test_get_customers_no_ssh_manager(self, client):
        """Test customer retrieval without SSH manager."""
        with patch("web_server.ssh_manager", None):
            response = client.get("/api/customers")

            assert response.status_code == 500
            data = json.loads(response.data)
            assert "error" in data

    def test_get_system_status(self, client, mock_ssh_manager):
        """Test system status endpoint."""
        mock_ssh_manager.test_connection.return_value = True

        with patch("web_server.ssh_manager", mock_ssh_manager):
            response = client.get("/api/status")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert "servers" in data
            assert "total_customers" in data

    def test_generate_secret(self, client):
        """Test secret generation endpoint."""
        response = client.post("/api/generate-secret")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "secret" in data
        assert len(data["secret"]) == 64

    def test_bulk_update_no_targets(self, client, mock_ssh_manager):
        """Test bulk update with no targets."""
        with patch("web_server.ssh_manager", mock_ssh_manager):
            response = client.post(
                "/api/bulk-update",
                json={"parameter_name": "test", "parameter_value": "value"},
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data

    def test_bulk_update_success(self, client, mock_ssh_manager):
        """Test successful bulk update."""
        mock_ssh_manager.bulk_update_parameter.return_value = {"customer1": True}

        with patch("web_server.ssh_manager", mock_ssh_manager):
            response = client.post(
                "/api/bulk-update",
                json={
                    "targets": ["customer1"],
                    "parameter_name": "database_host",
                    "parameter_value": "new-server.com",
                },
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert "results" in data

    def test_invalid_customer_format(self, client, mock_ssh_manager):
        """Test invalid customer ID format."""
        with patch("web_server.ssh_manager", mock_ssh_manager):
            response = client.get("/api/customer/invalid_format/parameters")

            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data

    def test_404_handler(self, client):
        """Test 404 error handler."""
        response = client.get("/api/nonexistent")

        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data


class TestInitialization:
    """Test initialization functions."""

    @patch("web_server.SSHManager")
    def test_init_ssh_manager_success(self, mock_ssh_class):
        """Test successful SSH manager initialization."""
        mock_instance = MagicMock()
        mock_ssh_class.return_value = mock_instance

        result = init_ssh_manager()

        assert result is True
        mock_ssh_class.assert_called_once_with("ssh_config.yml", "INFO")

    @patch("web_server.SSHManager")
    def test_init_ssh_manager_failure(self, mock_ssh_class):
        """Test SSH manager initialization failure."""
        mock_ssh_class.side_effect = Exception("Config file not found")

        result = init_ssh_manager()

        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])
