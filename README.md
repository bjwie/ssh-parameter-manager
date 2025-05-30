# 🔧 SSH Parameter Manager

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A professional web-based tool for managing Symfony `parameters.yml` files across multiple servers via SSH connections. Perfect for DevOps teams managing multiple customer environments.

## 🎯 Überblick

Dieses Tool ermöglicht es Ihnen, Symfony Parameter-Dateien von mehreren Kunden auf verschiedenen Servern zentral über eine benutzerfreundliche Web-Oberfläche zu verwalten. Alle Änderungen erfolgen direkt über SSH-Verbindungen zu Ihren Servern.

## ✨ Features

- 🌐 **Modern Web Interface** - Intuitive, responsive design for easy parameter management
- 🔐 **SSH-Based Remote Access** - Secure connections to multiple servers
- 👥 **Multi-Customer Support** - Manage parameters for multiple customers/projects
- 📦 **Automatic Backups** - Timestamped backups before any changes
- 🔒 **Permission Preservation** - Maintains file ownership and permissions
- ⚡ **Bulk Operations** - Update multiple customers simultaneously
- 🎯 **Template System** - Predefined parameter sets for common operations
- 📊 **Real-time Status** - Live connection status and operation feedback
- 🔑 **Secret Generation** - Built-in secure secret key generator
- 📝 **Comprehensive Logging** - Detailed operation logs for auditing

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- SSH access to target servers
- Symfony projects with `parameters.yml` files

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ssh-parameter-manager.git
   cd ssh-parameter-manager
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure SSH settings**
   ```bash
   cp ssh_config.example.yml ssh_config.yml
   # Edit ssh_config.yml with your server and customer details
   ```

5. **Start the web server**
   ```bash
   python web_server.py
   ```

6. **Open your browser**
   ```
   http://localhost:5000
   ```

## 📋 Configuration

### SSH Configuration File

Create `ssh_config.yml` based on the example file:

```yaml
servers:
  production:
    host: your-server.com
    port: 22
    username: deploy
    description: "Production Server"

customers:
  customer1:
    server: production
    path: /var/www/customer1/app/config/parameters.yml
    description: "Customer 1 - E-commerce Platform"
```

### SSH Key Setup

Ensure your SSH keys are properly configured:

```bash
# Generate SSH key if needed
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Copy public key to servers
ssh-copy-id user@your-server.com
```

## 🖥️ Usage

### Web Interface

The web interface provides:

- **Customer Overview** - Visual list of all configured customers
- **Parameter Editor** - Form-based editing of Symfony parameters
- **Bulk Operations** - Update multiple customers at once
- **Status Monitoring** - Real-time connection and operation status
- **Backup Management** - Create and manage configuration backups

### Command Line Interface

For automation and scripting:

```bash
# List all customers
python ssh_manager.py --list

# Update specific parameter
python ssh_manager.py --update production:customer1 --param database_host=new-server.com

# Apply template to multiple customers
python ssh_manager.py --template database_migration --targets production:customer1,production:customer2

# Create backups for all customers
python ssh_manager.py --backup-all
```

## 🏗️ Architecture

```
ssh-parameter-manager/
├── web_server.py           # Flask web application
├── ssh_manager.py          # Core SSH management logic
├── parameter_updater.py    # Parameter file operations
├── ssh_web_interface.html  # Modern web interface
├── ssh_config.yml          # Configuration file (create from example)
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🔧 API Endpoints

The Flask backend provides RESTful API endpoints:

- `GET /api/status` - System and connection status
- `GET /api/customers` - List all customers
- `GET /api/customer/{id}/parameters` - Get customer parameters
- `POST /api/customer/{id}/parameters` - Update customer parameters
- `POST /api/bulk-update` - Bulk parameter updates
- `POST /api/backup/{id}` - Create customer backup
- `POST /api/generate-secret` - Generate secure secret key

## 🛡️ Security Features

- **SSH Key Authentication** - Secure, password-less connections
- **Permission Preservation** - Maintains original file permissions
- **Backup System** - Automatic backups before changes
- **Input Validation** - Sanitized parameter inputs
- **Audit Logging** - Comprehensive operation logging
- **Secret Generation** - Cryptographically secure secret keys

## 🔍 Troubleshooting

### Common Issues

**SSH Connection Failed**
```bash
# Test SSH connection manually
ssh -i ~/.ssh/id_rsa user@server.com

# Check SSH agent
ssh-add -l
```

**Permission Denied**
```bash
# Ensure correct file permissions
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
```

**YAML Parsing Error**
- Verify YAML syntax in configuration files
- Check for proper indentation (spaces, not tabs)

### Debug Mode

Enable debug logging:

```yaml
# In ssh_config.yml
logging:
  level: DEBUG
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for Symfony framework parameter management
- Inspired by DevOps automation needs
- Uses Flask for the web interface
- Paramiko for SSH connections

## 📞 Support

If you encounter any issues or have questions:

1. Check the [troubleshooting section](#-troubleshooting)
2. Search existing [GitHub issues](https://github.com/yourusername/ssh-parameter-manager/issues)
3. Create a new issue with detailed information

---

**Made with ❤️ for the DevOps community** 