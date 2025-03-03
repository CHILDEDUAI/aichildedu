# Development Guide

This document provides guidelines and instructions for setting up and working with the AICHILDEDU development environment.

## Development Environment Setup

### Option 1: Using pip (Traditional)

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. For development, also install development dependencies:
   ```bash
   pip install pytest black isort mypy flake8 pytest-cov
   ```

### Option 2: Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver that can significantly speed up your dependency management.

1. Install uv:
   ```bash
   pip install uv
   ```

2. Create and activate a virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   uv pip install -e ".[dev]"  # Install the project with development dependencies
   ```

   Alternatively, you can use the lock file for exact dependency versioning:
   ```bash
   uv pip install -r requirements-uv.lock
   ```

## Development Workflow

### Code Style

This project uses:
- [Black](https://black.readthedocs.io/en/stable/) for code formatting
- [isort](https://pycqa.github.io/isort/) for import sorting
- [mypy](https://mypy.readthedocs.io/en/stable/) for static type checking
- [flake8](https://flake8.pycqa.org/en/latest/) for linting

Run the following commands to ensure your code meets the style guidelines:

```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy aichildedu

# Linting
flake8 aichildedu
```

### Running Tests

Run tests using pytest:

```bash
pytest

# With coverage report
pytest --cov=aichildedu
```

### Running Services Locally

To run a service locally:

```bash
# User Service
uvicorn aichildedu.user_service.main:app --reload --port 8001

# Content Service
uvicorn aichildedu.content_service.main:app --reload --port 8002

# AI Text Generator
uvicorn aichildedu.ai_service.text_generator.main:app --reload --port 8010
```

### Updating Dependencies

#### Using pip

1. Update the `requirements.txt` file directly.
2. Install the updated dependencies:
   ```bash
   pip install -r requirements.txt
   ```

#### Using uv

1. Update the dependencies in `pyproject.toml`.
2. Update the lock file:
   ```bash
   uv pip compile pyproject.toml -o requirements-uv.lock
   ```
3. Install the updated dependencies:
   ```bash
   uv pip install -r requirements-uv.lock
   ```

## Docker Development

For Docker-based development:

1. Build and run the services:
   ```bash
   docker-compose up -d
   ```

2. Build a specific service:
   ```bash
   docker-compose build user_service
   ```

3. View logs:
   ```bash
   docker-compose logs -f
   ```

## Environment Variables

Create a `.env` file in the root directory with the necessary environment variables for local development. See the example in the README.

## Contribution Guidelines

1. Create a feature branch from `main`
2. Make your changes, following the code style guidelines
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

Before submitting a pull request, please:
- Update the documentation if needed
- Add your changes to the CHANGELOG.md file
- Ensure your code passes all linting and tests 