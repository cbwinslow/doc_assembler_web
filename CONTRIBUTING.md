# Contributing to MCP Server

First off, thank you for considering contributing to MCP Server! It's people like you that make MCP Server such a great tool.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Development Setup](#development-setup)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Guidelines](#testing-guidelines)
6. [Documentation](#documentation)
7. [Pull Request Process](#pull-request-process)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Development Setup

### Prerequisites

- Python 3.12 or higher
- Docker and Docker Compose
- Make
- Git
- Poetry (Python package manager)
- Node.js and npm (for Playwright)

### Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/mcp-server.git
   cd mcp-server
   ```

2. Run the setup script:
   ```bash
   make setup
   ```
   This will:
   - Create a Python virtual environment
   - Install dependencies
   - Set up pre-commit hooks
   - Configure development tools

3. Start the development environment:
   ```bash
   make up
   ```

4. Verify the setup:
   ```bash
   make status
   ```

### Available Development Commands

- `make help` - Show all available commands
- `make up` - Start development environment
- `make down` - Stop development environment
- `make test` - Run tests
- `make format` - Format code
- `make lint` - Run linters
- `make docs` - Generate documentation

## Development Workflow

### Git Branch Strategy

We follow a trunk-based development workflow:

- `main` - Production-ready code
- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation changes
- `refactor/*` - Code refactoring
- `test/*` - Test additions or modifications

### Development Process

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, following our coding standards

3. Ensure all tests pass:
   ```bash
   make check
   ```

4. Update documentation as needed:
   ```bash
   make docs
   ```

5. Commit your changes using conventional commits:
   ```bash
   <type>(<scope>): <description>

   [optional body]

   [optional footer(s)]
   ```
   Types: feat, fix, docs, style, refactor, test, chore

## Coding Standards

### Python Coding Standards

- Follow PEP 8 style guide
- Use type hints for all function arguments and return values
- Maximum line length: 88 characters (Black default)
- Docstrings: Google style
- Import ordering: isort default

### Code Formatting

We use automated tools to ensure consistent code formatting:

- Black for Python code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

To format your code:
```bash
make format
```

To check for issues:
```bash
make lint
```

## Testing Guidelines

### Test Requirements

- All new features must include tests
- Maintain or improve code coverage
- Tests must be documented
- Integration tests for API endpoints
- Unit tests for business logic

### Running Tests

```bash
# Run all tests
make test

# Run tests in watch mode during development
make test-watch

# Run specific test file
make test PYTEST_ARGS="tests/test_specific.py"
```

## Documentation

### Documentation Requirements

- API endpoints must be documented with OpenAPI/Swagger
- Python functions must have docstrings
- Complex logic must include inline comments
- Update README.md for significant changes
- Include example usage where appropriate

### Building Documentation

```bash
# Generate documentation
make docs

# Serve documentation locally
make docs-serve
```

## Pull Request Process

1. Update the README.md with details of significant changes

2. Ensure all tests pass and documentation is updated:
   ```bash
   make check
   make docs
   ```

3. PR title should follow conventional commits format

4. PR description should include:
   - Purpose of the change
   - Links to related issues
   - Testing steps
   - Screenshots (if UI changes)
   - Migration steps (if any)

5. PR must be reviewed by at least one maintainer

6. All conversations must be resolved before merging

### PR Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Code formatting checked
- [ ] PR title follows conventional commits
- [ ] Dependencies updated
- [ ] Breaking changes noted
- [ ] Migration steps documented

## Additional Resources

- [Project Wiki](wiki-link)
- [API Documentation](api-docs-link)
- [Architecture Overview](architecture-link)
- [Troubleshooting Guide](troubleshooting-link)

## Questions or Problems?

- File an issue in the GitHub issue tracker
- Contact the maintainers
- Check the [FAQ](faq-link)

Thank you for contributing to MCP Server! 🚀

