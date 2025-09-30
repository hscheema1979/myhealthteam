"""
Setup script for google-oauth-streamlit package
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'INTEGRATION_GUIDE.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Google OAuth integration for Streamlit applications"

# Read requirements from requirements.txt
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return [
        'streamlit>=1.28.0',
        'requests>=2.31.0',
        'python-dotenv>=1.0.0',
        'urllib3>=2.0.0'
    ]

setup(
    name="google-oauth-streamlit",
    version="1.0.0",
    author="Harpreet Singh",
    author_email="harpreet@myhealthteam.org",
    description="Simple Google OAuth integration for Streamlit applications",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/google-oauth-streamlit",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Streamlit",
        "Topic :: Internet :: WWW/HTTP :: Session",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration :: Authentication/Directory",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "examples": [
            "pandas>=2.0.0",
            "numpy>=1.24.0",
        ]
    },
    include_package_data=True,
    package_data={
        "google_oauth_streamlit": [
            "*.md",
            "*.txt",
            "*.template",
        ],
    },
    entry_points={
        "console_scripts": [
            "google-oauth-streamlit=google_oauth_streamlit.oauth_module:main",
        ],
    },
    keywords=[
        "streamlit",
        "oauth",
        "google",
        "authentication",
        "login",
        "security",
        "web",
        "app"
    ],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/google-oauth-streamlit/issues",
        "Source": "https://github.com/yourusername/google-oauth-streamlit",
        "Documentation": "https://github.com/yourusername/google-oauth-streamlit/blob/main/INTEGRATION_GUIDE.md",
    },
)