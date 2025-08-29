# Contributing to BioNewsBot

First off, thank you for considering contributing to BioNewsBot! It's people like you that make BioNewsBot such a great tool for the life sciences community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How Can I Contribute?](#how-can-i-contribute)
- [Style Guidelines](#style-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Testing Requirements](#testing-requirements)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [conduct@bionewsbot.com](mailto:conduct@bionewsbot.com).

## Getting Started

Before you begin:
- Have you read the [README](README.md)?
- Check out the [existing issues](https://github.com/romwil/bionewsbot/issues)
- For major changes, please open an issue first to discuss what you would like to change

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Git
- PostgreSQL client tools (optional, for database debugging)
- Redis client tools (optional, for cache debugging)

### Setting Up Your Development Environment

1. **Fork and Clone the Repository**
   ```bash
   # Fork the repository on GitHub first, then:
   git clone https://github.com/YOUR_USERNAME/bionewsbot.git
   cd bionewsbot
   git remote add upstream https://github.com/romwil/bionewsbot.git
   ```

2. **Set Up Python Environment**
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # On Linux/Mac:
   source venv/bin/activate
   # On Windows:
   # venv\Scripts\activate

   # Install backend dependencies
   cd backend
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   cd ..
   ```

3. **Set Up Node.js Environment**
   ```bash
   # Install frontend dependencies
   cd frontend
   npm install
   cd ..
   ```

4. **Configure Environment Variables**
   ```bash
   # Copy example environment file
   cp .env.example .env

   # Edit .env with your local configuration
   # Make sure to set up test database credentials
   ```

5. **Start Development Services**
   ```bash
   # Start all services in development mode
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

   # Or start specific services:
   docker-compose up -d postgres redis
   ```

6. **Initialize Database**
   ```bash
   # Run database migrations
   cd backend
   alembic upgrade head

   # Seed development data (optional)
   python scripts/seed_dev_data.py
   ```

7. **Verify Setup**
   ```bash
   # Run tests to ensure everything is working
   ./run-tests.sh

   # Start development servers
   # Backend (in one terminal):
   cd backend
   uvicorn main:app --reload --port 8000

   # Frontend (in another terminal):
   cd frontend
   npm run dev
   ```

### Development Tools

We use several tools to maintain code quality:

- **Black**: Code formatting for Python
- **ESLint**: Code linting for JavaScript/TypeScript
- **Prettier**: Code formatting for JavaScript/TypeScript
- **MyPy**: Static type checking for Python
- **Pytest**: Testing framework for Python
- **Jest**: Testing framework for JavaScript

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- A clear and descriptive title
- Exact steps to reproduce the problem
- Expected behavior vs actual behavior
- Screenshots (if applicable)
- Your environment details (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- A clear and descriptive title
- Step-by-step description of the suggested enhancement
- Explanation of why this enhancement would be useful
- Possible implementation approach (if you have one)

### Your First Code Contribution

Unsure where to begin? Look for issues labeled:
- `good first issue` - Simple issues good for beginners
- `help wanted` - Issues where we need community help
- `documentation` - Documentation improvements

### Pull Requests

1. Create your feature branch from `develop`
2. Make your changes following our style guidelines
3. Add or update tests as needed
4. Update documentation as needed
5. Submit a pull request to the `develop` branch

## Style Guidelines

### Python Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use Black for code formatting (configuration in `pyproject.toml`)
- Use type hints for all function signatures
- Maximum line length: 88 characters (Black default)
- Use descriptive variable names
- Add docstrings to all functions, classes, and modules

```python
# Good example
def calculate_sentiment_score(text: str, model: SentimentModel) -> float:
    """Calculate sentiment score for given text.

    Args:
        text: The text to analyze
        model: Pre-trained sentiment model

    Returns:
        Sentiment score between -1.0 (negative) and 1.0 (positive)
    """
    # Implementation here
    pass
```

### JavaScript/TypeScript Code Style

- Use ESLint configuration provided
- Use Prettier for formatting
- Prefer functional components in React
- Use TypeScript for type safety
- Use meaningful component and variable names

```typescript
// Good example
interface CompanyCardProps {
  company: Company;
  onSelect: (id: string) => void;
}

export const CompanyCard: React.FC<CompanyCardProps> = ({ company, onSelect }) => {
  // Component implementation
};
```

### API Design Guidelines

- Follow RESTful principles
- Use consistent naming conventions
- Version APIs appropriately
- Include proper error responses
- Document all endpoints

### Database Guidelines

- Name tables in plural (e.g., `companies`, `articles`)
- Use snake_case for column names
- Always include created_at and updated_at timestamps
- Add appropriate indexes for query performance
- Document complex queries

## Commit Messages

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks
- **ci**: CI/CD changes

### Examples

```
feat(api): add endpoint for company sentiment analysis

Implemented new /api/v1/companies/{id}/sentiment endpoint that
returns historical sentiment data for a specific company.

Closes #123
```

```
fix(notifications): correct Slack message formatting

Fixed issue where markdown formatting was not properly rendered
in Slack notifications for company alerts.
```

## Pull Request Process

1. **Before Submitting**
   - Ensure all tests pass locally
   - Update documentation if needed
   - Add tests for new functionality
   - Run linters and fix any issues
   - Rebase on latest `develop` branch

2. **PR Title and Description**
   - Use clear, descriptive title following commit message format
   - Reference related issues (e.g., "Closes #123")
   - Include screenshots for UI changes
   - List any breaking changes
   - Describe testing performed

3. **PR Checklist**
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Comments added for complex code
   - [ ] Documentation updated
   - [ ] Tests added/updated
   - [ ] All tests passing
   - [ ] No merge conflicts

4. **Review Process**
   - At least one maintainer approval required
   - Address all review comments
   - Keep PR focused and reasonably sized
   - Be responsive to feedback

## Testing Requirements

### Python Tests

- Write tests using pytest
- Aim for >80% code coverage
- Include unit and integration tests
- Mock external services appropriately

```python
# Example test
def test_sentiment_analysis():
    """Test sentiment analysis returns expected score."""
    analyzer = SentimentAnalyzer()
    score = analyzer.analyze("This drug shows promising results")
    assert 0.5 <= score <= 1.0
```

### JavaScript Tests

- Write tests using Jest and React Testing Library
- Test component behavior, not implementation
- Include snapshot tests for UI components
- Test error states and edge cases

```typescript
// Example test
describe('CompanyCard', () => {
  it('should call onSelect when clicked', () => {
    const handleSelect = jest.fn();
    const { getByText } = render(
      <CompanyCard company={mockCompany} onSelect={handleSelect} />
    );

    fireEvent.click(getByText(mockCompany.name));
    expect(handleSelect).toHaveBeenCalledWith(mockCompany.id);
  });
});
```

### End-to-End Tests

- Use Playwright for E2E tests
- Cover critical user journeys
- Run against staging environment
- Include in CI pipeline

## Questions?

Feel free to:
- Open an issue for discussion
- Join our [Slack community](https://bionewsbot.slack.com)
- Email us at [dev@bionewsbot.com](mailto:dev@bionewsbot.com)

## Recognition

Contributors are recognized in our:
- [Contributors page](https://github.com/romwil/bionewsbot/contributors)
- Release notes
- Project documentation

Thank you for contributing to BioNewsBot! 🎉
