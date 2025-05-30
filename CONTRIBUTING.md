# Contributing to SSH Parameter Manager

Thank you for your interest in contributing to SSH Parameter Manager! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- SSH access to test servers (for testing)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/ssh-parameter-manager.git
   cd ssh-parameter-manager
   ```

2. **Set up development environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   make install-dev
   
   # Set up configuration
   make setup
   ```

3. **Run the application**
   ```bash
   make run
   ```

## 📝 Development Guidelines

### Code Style

We use [Black](https://black.readthedocs.io/) for code formatting and [flake8](https://flake8.pycqa.org/) for linting.

```bash
# Format code
make format

# Check linting
make lint
```

### Type Hints

Please use type hints for all new code:

```python
def update_parameters(customer_id: str, parameters: Dict[str, Any]) -> bool:
    """Update parameters for a customer."""
    pass
```

### Documentation

- Add docstrings to all functions and classes
- Use Google-style docstrings
- Update README.md if adding new features

Example docstring:
```python
def create_backup(server_name: str, customer_name: str) -> Optional[str]:
    """
    Create a backup of customer's parameters file.
    
    Args:
        server_name (str): Name of the server
        customer_name (str): Name of the customer
        
    Returns:
        Optional[str]: Path to backup file if successful, None otherwise
        
    Raises:
        SSHConnectionError: If SSH connection fails
        FileNotFoundError: If parameters file doesn't exist
    """
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
python -m pytest tests/test_ssh_manager.py -v

# Run with coverage
python -m pytest --cov=. --cov-report=html
```

### Writing Tests

- Write tests for all new functionality
- Use pytest fixtures for common setup
- Mock external dependencies (SSH connections, file operations)

Example test:
```python
import pytest
from unittest.mock import Mock, patch
from ssh_manager import SSHManager

def test_update_parameters():
    """Test parameter update functionality."""
    with patch('ssh_manager.paramiko.SSHClient') as mock_ssh:
        manager = SSHManager('test_config.yml')
        result = manager.update_parameters('test_customer', {'key': 'value'})
        assert result is True
```

## 🔧 Project Structure

```
ssh-parameter-manager/
├── ssh_manager.py          # Core SSH management logic
├── web_server.py           # Flask web application
├── parameter_updater.py    # Parameter file operations
├── ssh_web_interface.html  # Web interface
├── tests/                  # Test files
├── docs/                   # Documentation
└── examples/               # Example configurations
```

## 📋 Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the coding standards
   - Add tests for new functionality
   - Update documentation

3. **Test your changes**
   ```bash
   make test
   make lint
   make format
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add bulk parameter update functionality
fix: resolve SSH connection timeout issue
docs: update installation instructions
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment information**
   - Python version
   - Operating system
   - SSH Parameter Manager version

2. **Steps to reproduce**
   - Clear, numbered steps
   - Expected vs actual behavior

3. **Logs and error messages**
   - Include relevant log output
   - Sanitize sensitive information

4. **Configuration details**
   - Anonymized configuration snippets
   - Server setup details (if relevant)

## 💡 Feature Requests

For feature requests, please:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** and problem you're solving
3. **Propose a solution** if you have ideas
4. **Consider backwards compatibility**

## 🔒 Security

If you discover a security vulnerability:

1. **Do NOT open a public issue**
2. **Email the maintainers** directly
3. **Provide detailed information** about the vulnerability
4. **Allow time for a fix** before public disclosure

## 📚 Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Paramiko Documentation](https://docs.paramiko.org/)
- [PyYAML Documentation](https://pyyaml.org/)

## 🏷️ Release Process

For maintainers:

1. **Update version** in `setup.py`
2. **Update CHANGELOG.md**
3. **Create release tag**
   ```bash
   git tag -a v2.1.0 -m "Release version 2.1.0"
   git push origin v2.1.0
   ```
4. **GitHub Actions** will automatically build and test

## 🤝 Code of Conduct

Please be respectful and professional in all interactions. We're here to build great software together!

## 📞 Getting Help

- **Documentation**: Check the README.md first
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact maintainers for sensitive issues

Thank you for contributing to SSH Parameter Manager! 🎉 