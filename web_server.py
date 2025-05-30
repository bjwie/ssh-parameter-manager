#!/usr/bin/env python3
"""
SSH Parameter Manager Web Server

A Flask-based web server providing REST API endpoints for managing
Symfony parameters.yml files across multiple servers via SSH.

Author: SSH Parameter Manager Team
License: MIT
"""

import os
import sys
import json
import logging
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

try:
    from flask import Flask, request, jsonify, send_from_directory
    from flask_cors import CORS
    import yaml
except ImportError as e:
    print("❌ Required packages not installed! Please run:")
    print("pip install flask flask-cors pyyaml")
    sys.exit(1)

from ssh_manager import SSHManager

# Flask application setup
app = Flask(__name__)
CORS(app)

# Global SSH Manager instance
ssh_manager: Optional[SSHManager] = None

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def init_ssh_manager() -> bool:
    """
    Initialize the SSH Manager with configuration.

    Returns:
        bool: True if initialization successful, False otherwise
    """
    global ssh_manager
    try:
        ssh_manager = SSHManager("ssh_config.yml", "INFO")
        logger.info("SSH Manager initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize SSH Manager: {e}")
        return False


@app.route("/")
def index() -> str:
    """
    Serve the main web interface.

    Returns:
        str: HTML content of the web interface
    """
    return send_from_directory(".", "ssh_web_interface.html")


@app.route("/api/status", methods=["GET"])
def get_system_status() -> Tuple[Dict[str, Any], int]:
    """
    Get system status including server connections and customer count.

    Returns:
        Tuple[Dict[str, Any], int]: JSON response and HTTP status code
    """
    try:
        if not ssh_manager:
            return jsonify({"error": "SSH Manager not initialized"}), 500

        # Get server status
        servers_status = {}
        for server_name in ssh_manager.config.get("servers", {}):
            try:
                # Test connection
                connection_ok = ssh_manager.test_connection(server_name)
                servers_status[server_name] = {
                    "connected": connection_ok,
                    "error": None if connection_ok else "Connection failed",
                }
            except Exception as e:
                servers_status[server_name] = {"connected": False, "error": str(e)}

        # Count total customers
        total_customers = len(ssh_manager.list_all_customers())

        return (
            jsonify(
                {
                    "success": True,
                    "servers": servers_status,
                    "total_customers": total_customers,
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/customers", methods=["GET"])
def get_customers() -> Tuple[Dict[str, Any], int]:
    """
    Get all available customers with their configuration.

    Returns:
        Tuple[Dict[str, Any], int]: JSON response and HTTP status code
    """
    try:
        if not ssh_manager:
            return jsonify({"error": "SSH Manager not initialized"}), 500

        customers = ssh_manager.list_all_customers()
        return (
            jsonify({"success": True, "customers": customers, "count": len(customers)}),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting customers: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/customer/<path:customer_id>/parameters", methods=["GET"])
def get_customer_parameters(customer_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Load current parameters for a specific customer.

    Args:
        customer_id (str): Customer identifier in format 'server:customer'

    Returns:
        Tuple[Dict[str, Any], int]: JSON response and HTTP status code
    """
    try:
        if not ssh_manager:
            return jsonify({"error": "SSH Manager not initialized"}), 500

        if ":" not in customer_id:
            return (
                jsonify(
                    {"error": "Invalid customer format (expected: server:customer)"}
                ),
                400,
            )

        server_name, customer_name = customer_id.split(":", 1)

        # Get customer configuration
        try:
            server_config = ssh_manager.config["servers"][server_name]
            customer_config = server_config["customers"][customer_name]
            remote_path = customer_config["parameters_path"]
        except KeyError as e:
            return jsonify({"error": f"Customer or server not found: {e}"}), 404

        # Download parameters file to temporary location
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".yml", delete=False
        ) as temp_file:
            temp_path = temp_file.name

        try:
            success = ssh_manager.download_file(server_name, remote_path, temp_path)
            if not success:
                return jsonify({"error": "Failed to download parameters file"}), 500

            # Parse YAML file
            with open(temp_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                parameters = data.get("parameters", {}) if data else {}

            return (
                jsonify(
                    {
                        "success": True,
                        "customer_id": customer_id,
                        "parameters": parameters,
                        "file_path": remote_path,
                    }
                ),
                200,
            )

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Error getting customer parameters: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/customer/<path:customer_id>/parameters", methods=["POST"])
def update_customer_parameters(customer_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Update parameters for a specific customer.

    Args:
        customer_id (str): Customer identifier in format 'server:customer'

    Returns:
        Tuple[Dict[str, Any], int]: JSON response and HTTP status code
    """
    try:
        if not ssh_manager:
            return jsonify({"error": "SSH Manager not initialized"}), 500

        if ":" not in customer_id:
            return (
                jsonify(
                    {"error": "Invalid customer format (expected: server:customer)"}
                ),
                400,
            )

        data = request.get_json()
        if not data or "parameters" not in data:
            return jsonify({"error": "No parameter data received"}), 400

        server_name, customer_name = customer_id.split(":", 1)
        new_parameters = data["parameters"]

        # Update parameters
        success = ssh_manager.update_remote_parameters(
            server_name, customer_name, new_parameters
        )

        if success:
            logger.info(f"Successfully updated parameters for {customer_id}")
            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Parameters for {customer_id} updated successfully",
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "Failed to update parameters"}), 500

    except Exception as e:
        logger.error(f"Error updating customer parameters: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/bulk-update", methods=["POST"])
def bulk_update_parameters() -> Tuple[Dict[str, Any], int]:
    """
    Perform bulk update for multiple customers.

    Returns:
        Tuple[Dict[str, Any], int]: JSON response and HTTP status code
    """
    try:
        if not ssh_manager:
            return jsonify({"error": "SSH Manager not initialized"}), 500

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        targets = data.get("targets", [])
        parameter_name = data.get("parameter_name")
        parameter_value = data.get("parameter_value")

        if not targets:
            return jsonify({"error": "No targets specified"}), 400
        if not parameter_name:
            return jsonify({"error": "No parameter name specified"}), 400
        if parameter_value is None:
            return jsonify({"error": "No parameter value specified"}), 400

        # Perform bulk update
        results = ssh_manager.bulk_update_parameter(
            targets, parameter_name, parameter_value
        )

        success_count = sum(1 for success in results.values() if success)

        logger.info(f"Bulk update completed: {success_count}/{len(targets)} successful")

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Bulk update completed: {success_count}/{len(targets)} successful",
                    "results": results,
                    "parameter_name": parameter_name,
                    "parameter_value": parameter_value,
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error in bulk update: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/backup/<path:customer_id>", methods=["POST"])
def create_backup(customer_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Create a backup for a specific customer.

    Args:
        customer_id (str): Customer identifier in format 'server:customer'

    Returns:
        Tuple[Dict[str, Any], int]: JSON response and HTTP status code
    """
    try:
        if not ssh_manager:
            return jsonify({"error": "SSH Manager not initialized"}), 500

        if ":" not in customer_id:
            return (
                jsonify(
                    {"error": "Invalid customer format (expected: server:customer)"}
                ),
                400,
            )

        server_name, customer_name = customer_id.split(":", 1)

        # Create backup
        backup_path = ssh_manager.create_backup(server_name, customer_name)

        if backup_path:
            logger.info(f"Backup created for {customer_id}: {backup_path}")
            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Backup created successfully",
                        "backup_path": backup_path,
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "Failed to create backup"}), 500

    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate-secret", methods=["POST"])
def generate_secret() -> Tuple[Dict[str, Any], int]:
    """
    Generate a secure secret key for Symfony applications.

    Returns:
        Tuple[Dict[str, Any], int]: JSON response and HTTP status code
    """
    try:
        import secrets
        import string

        # Generate a secure random string
        alphabet = string.ascii_letters + string.digits
        secret = "".join(secrets.choice(alphabet) for _ in range(64))

        return (
            jsonify(
                {
                    "success": True,
                    "secret": secret,
                    "length": len(secret),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error generating secret: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/download-all", methods=["POST"])
def download_all_configs() -> Tuple[Dict[str, Any], int]:
    """
    Download all customer configurations to local directory.

    Returns:
        Tuple[Dict[str, Any], int]: JSON response and HTTP status code
    """
    try:
        if not ssh_manager:
            return jsonify({"error": "SSH Manager not initialized"}), 500

        # Create download directory
        download_dir = Path("downloaded_configs")
        download_dir.mkdir(exist_ok=True)

        customers = ssh_manager.list_all_customers()
        downloaded_count = 0

        for customer_id, customer_info in customers.items():
            try:
                server_name = customer_info["server"]
                remote_path = customer_info["path"]
                local_path = download_dir / f"{customer_id}_parameters.yml"

                success = ssh_manager.download_file(
                    server_name, remote_path, str(local_path)
                )

                if success:
                    downloaded_count += 1

            except Exception as e:
                logger.warning(f"Failed to download config for {customer_id}: {e}")

        logger.info(f"Downloaded {downloaded_count}/{len(customers)} configurations")

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Downloaded {downloaded_count}/{len(customers)} configurations",
                    "download_directory": str(download_dir.absolute()),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error downloading configurations: {e}")
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error) -> Tuple[Dict[str, str], int]:
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error) -> Tuple[Dict[str, str], int]:
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500


def main() -> None:
    """
    Main entry point for the web server.
    """
    # Initialize SSH Manager
    if not init_ssh_manager():
        logger.error("Failed to initialize SSH Manager. Exiting.")
        sys.exit(1)

    # Start Flask development server
    logger.info("Starting SSH Parameter Manager Web Server...")
    logger.info("Access the web interface at: http://localhost:5000")

    try:
        app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
