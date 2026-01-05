# Contributing to Weather Ensemble Agent

Thank you for your interest in contributing! This document provides guidelines for development and releasing new versions.

## Development Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git
- Anthropic API key

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/rmcd-mscb/weather-ensemble-agent.git
cd weather-ensemble-agent

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Install pre-commit hooks
pre-commit install
```

## Development Workflow

### Code Style

This project uses automated code quality tools:

- **ruff**: Linting and formatting (line length: 100)
- **bandit**: Security analysis
- **pyupgrade**: Python syntax modernization
- **Pre-commit hooks**: Run automatically on `git commit`

```bash
# Run formatters manually
ruff format .

# Run linters manually
ruff check .

# Run all pre-commit hooks
pre-commit run --all-files
```

### Making Changes

1. Create a new branch for your feature/fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following these guidelines:
   - Write clear, concise commit messages
   - Follow existing code patterns and structure
   - Add docstrings to new functions/classes
   - Update documentation as needed

3. Ensure pre-commit hooks pass:
   ```bash
   git add .
   git commit -m "feat: Add new feature"
   # Pre-commit hooks run automatically
   ```

4. Push your branch and create a Pull Request

### Commit Message Convention

Use conventional commits for clear history:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks (dependencies, build config)

Examples:
```
feat: Add caching layer for API responses
fix: Handle timeout errors in weather API calls
docs: Update installation instructions
chore: Bump version to 0.2.0
```

## Testing

**Note**: The test suite is currently under development (see TODO section in README).

When tests are available:
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=weather_agent
```

## Releasing New Versions

This project uses [semantic versioning](https://semver.org/):
- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backward compatible
- **PATCH** (0.0.1): Bug fixes, backward compatible

### Release Workflow

#### 1. Prepare the Release

```bash
# Ensure you're on main with latest changes
git checkout main
git pull origin main

# Ensure all tests pass (when available)
pytest

# Ensure pre-commit checks pass
pre-commit run --all-files
```

#### 2. Update Version

Use hatch to bump the version (updates both `pyproject.toml` and `src/weather_agent/__init__.py`):

```bash
# For a patch release (0.1.0 → 0.1.1)
hatch version patch

# For a minor release (0.1.0 → 0.2.0)
hatch version minor

# For a major release (0.1.0 → 1.0.0)
hatch version major

# Or set a specific version
hatch version 0.2.0
```

#### 3. Update CHANGELOG.md

Add a new version section at the top of `CHANGELOG.md`:

```markdown
## [0.2.0] - 2026-01-XX

### Added
- New feature descriptions

### Changed
- Changes to existing functionality

### Fixed
- Bug fixes

### Deprecated
- Features that will be removed

### Removed
- Removed features

### Security
- Security improvements
```

Include the comparison link at the bottom:
```markdown
[0.2.0]: https://github.com/rmcd-mscb/weather-ensemble-agent/compare/v0.1.0...v0.2.0
```

#### 4. Commit Version Bump

```bash
# Stage the changed files
git add pyproject.toml src/weather_agent/__init__.py CHANGELOG.md

# Commit with conventional format
git commit -m "chore: Bump version to $(hatch version)"
```

#### 5. Create Git Tag

```bash
# Create annotated tag
git tag -a "v$(hatch version)" -m "Release v$(hatch version)"

# Verify tag
git tag -l
```

#### 6. Push to GitHub

```bash
# Push commits and tags
git push origin main
git push origin --tags
```

#### 7. Build Distribution Packages

```bash
# Clean previous builds
rm -rf dist/

# Build with uv
uv build

# Verify build artifacts
ls -lh dist/
# Should see:
# - weather_ensemble_agent-X.Y.Z-py3-none-any.whl
# - weather_ensemble_agent-X.Y.Z.tar.gz
```

#### 8. Publish to PyPI

```bash
# Publish to PyPI
uv publish

# Or with explicit token
uv publish --token pypi-YOUR_TOKEN_HERE
```

#### 9. Create GitHub Release (Optional)

1. Go to https://github.com/rmcd-mscb/weather-ensemble-agent/releases/new
2. Select the tag you just created (e.g., `v0.2.0`)
3. Title: `Release 0.2.0` or similar
4. Description: Copy relevant sections from CHANGELOG.md
5. Click "Publish release"

### Quick Reference

Complete release in one script:

```bash
#!/bin/bash
# Release script - saves to scripts/release.sh

set -e  # Exit on error

VERSION_TYPE=${1:-patch}  # Default to patch

echo "🚀 Starting release process..."

# 1. Verify clean working directory
if [[ -n $(git status -s) ]]; then
    echo "❌ Working directory is not clean. Commit or stash changes first."
    exit 1
fi

# 2. Update version
echo "📝 Bumping version ($VERSION_TYPE)..."
hatch version $VERSION_TYPE
NEW_VERSION=$(hatch version)

# 3. Prompt for CHANGELOG update
echo "⚠️  Please update CHANGELOG.md with changes for v$NEW_VERSION"
echo "Press Enter when ready to continue..."
read

# 4. Commit version bump
echo "💾 Committing version bump..."
git add pyproject.toml src/weather_agent/__init__.py CHANGELOG.md
git commit -m "chore: Bump version to $NEW_VERSION"

# 5. Create tag
echo "🏷️  Creating tag v$NEW_VERSION..."
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"

# 6. Push
echo "⬆️  Pushing to GitHub..."
git push origin main
git push origin --tags

# 7. Build
echo "🔨 Building distribution..."
rm -rf dist/
uv build

# 8. Publish
echo "📦 Publishing to PyPI..."
uv publish

echo "✅ Release v$NEW_VERSION complete!"
echo "🔗 View on PyPI: https://pypi.org/project/weather-ensemble-agent/$NEW_VERSION/"
echo "🔗 Create GitHub release: https://github.com/rmcd-mscb/weather-ensemble-agent/releases/new?tag=v$NEW_VERSION"
```

Usage:
```bash
# Patch release (0.1.0 → 0.1.1)
./scripts/release.sh patch

# Minor release (0.1.0 → 0.2.0)
./scripts/release.sh minor

# Major release (0.1.0 → 1.0.0)
./scripts/release.sh major
```

## Project Structure

```
weather-ensemble-agent/
├── src/weather_agent/
│   ├── __init__.py              # Version definition
│   ├── agent.py                 # Main agentic loop
│   ├── cli.py                   # Command-line interface
│   ├── tools/                   # Agent tools
│   │   ├── geocoding.py
│   │   ├── weather_api.py
│   │   └── statistics.py
│   └── visualization/
│       └── plotter.py
├── tests/                       # Test suite (TODO)
├── examples/                    # Example scripts
├── outputs/                     # Default output directory
├── README.md                    # User documentation
├── CHANGELOG.md                 # Version history
├── CONTRIBUTING.md              # This file
├── LICENSE                      # MIT License
└── pyproject.toml              # Project metadata
```

## Questions or Issues?

- **Bug reports**: Open an issue with details and reproduction steps
- **Feature requests**: Open an issue describing the feature and use case
- **Questions**: Open a discussion or issue

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Weather Ensemble Agent! 🌤️
