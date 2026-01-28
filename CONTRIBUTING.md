# Contributing to DevContext

Thank you for your interest in contributing to DevContext! This document provides guidelines for contributing.

## Ways to Contribute

- **Report bugs** - Open an issue describing the problem
- **Suggest features** - Open an issue with your idea
- **Submit PRs** - Fix bugs or add features
- **Improve docs** - Help make the documentation clearer
- **Spread the word** - Star the repo, share with friends

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/tsunderland/devcontext.git
cd devcontext
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
```

3. Install in development mode:
```bash
pip install -e ".[dev]"
```

4. Run tests:
```bash
pytest
```

## Code Style

- We use [ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Run `ruff check .` before committing
- Run `ruff format .` to auto-format code

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Run linting (`ruff check .`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Commit Messages

- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Keep the first line under 50 characters

Examples:
- `Add note command to CLI`
- `Fix session end timestamp bug`
- `Update README with installation instructions`

## Questions?

Open an issue or reach out to tsunderland@bitfuturistic.com.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
