#!/usr/bin/env python3
"""
Setup script for SSH Parameter Manager

A professional tool for managing Symfony parameters.yml files
across multiple servers via SSH connections.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
requirements_file = this_directory / "requirements.txt"
if requirements_file.exists():
    requirements = requirements_file.read_text().strip().split('\n')

setup(
    name="ssh-parameter-manager",
    version="2.1.0",
    author="SSH Parameter Manager Team",
    author_email="",
    description="A professional tool for managing Symfony parameters.yml files via SSH",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ssh-parameter-manager",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "black",
            "flake8",
            "pytest",
            "pytest-cov",
        ],
    },
    entry_points={
        "console_scripts": [
            "ssh-parameter-manager=web_server:main",
            "ssh-manager=ssh_manager:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.html", "*.yml", "*.yaml", "*.md"],
    },
    keywords="symfony, parameters, ssh, devops, configuration, management",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/ssh-parameter-manager/issues",
        "Source": "https://github.com/yourusername/ssh-parameter-manager",
        "Documentation": "https://github.com/yourusername/ssh-parameter-manager#readme",
    },
) 