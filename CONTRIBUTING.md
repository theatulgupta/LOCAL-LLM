"""Contributing Guidelines

This document outlines how to contribute to the Local LLM Server project.
"""

# Contributing to Local LLM Server

## Code Standards

### Python Style Guide

- Follow PEP 8
- Use type hints for all function parameters and returns
- Max line length: 88 characters (Black formatter)
- Use docstrings for all modules, classes, and functions

### Code Quality

```bash
# Format code
make format

# Check linting
make lint

# Type checking
make typecheck
```

### Commit Messages

- Use present tense: "Add feature" not "Added feature"
- Use imperative mood: "Move cursor to..." not "Moves cursor to..."
- Limit first line to 50 characters
- Add detailed explanation if needed

Examples:

```
Add streaming response support
Fix rate limiting for concurrent requests
Improve error messages for Ollama connection failures
```

## Testing Requirements

All changes must include tests:

```bash
# Write tests in tests/
# Run all tests
make test

# Run with coverage
make test-cov

# Minimum 80% code coverage required
```

Test structure:

```python
def test_feature_behavior():
    """Clear description of what's being tested"""
    # Arrange
    setup_data = ...

    # Act
    result = function(setup_data)

    # Assert
    assert result == expected_value
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/my-feature
```

### 2. Make Changes

```bash
# Edit files
vim app/routes/llm.py

# Format
make format

# Run tests
make test
```

### 3. Commit Changes

```bash
git add .
git commit -m "Add new endpoint for model management"
```

### 4. Push & Create PR

```bash
git push origin feature/my-feature
# Create pull request on GitHub
```

## Project Structure Guidelines

When adding new features:

1. **API Endpoints** → `app/routes/llm.py`
2. **Business Logic** → `app/services/`
3. **Data Models** → `app/models.py`
4. **Configuration** → `app/config.py`
5. **Tests** → `tests/test_*.py`
6. **Documentation** → Docstrings + README updates

## Adding New Endpoint Example

```python
# 1. Add Pydantic model in app/models.py
class MyRequest(BaseModel):
    data: str = Field(..., description="Input data")

class MyResponse(BaseModel):
    result: str = Field(..., description="Output result")

# 2. Add route in app/routes/llm.py
@router.post("/my-endpoint", response_model=MyResponse)
async def my_endpoint(request: MyRequest, client_ip: str = Depends(apply_rate_limit)):
    """Endpoint description"""
    try:
        # Process request
        result = process_data(request.data)
        return MyResponse(result=result)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

# 3. Add test in tests/test_routes.py
def test_my_endpoint(client):
    """Test my endpoint"""
    response = client.post("/api/my-endpoint", json={"data": "test"})
    assert response.status_code == 200
    assert response.json()["result"] == "expected"

# 4. Update documentation in README.md
```

## Documentation Standards

### Docstrings Format

```python
def generate(
    prompt: str,
    model: str = "llama3"
) -> str:
    """
    Generate response from LLM

    Args:
        prompt: Input prompt for the model
        model: Model name to use

    Returns:
        Generated response text

    Raises:
        OllamaConnectionError: If unable to connect
        OllamaError: If model returns error
    """
```

### README Updates

Update README.md when you:

- Add new endpoints
- Change configuration options
- Add new features
- Fix bugs with user impact

## Performance Considerations

When making changes:

1. **Async/Await** - Use async for I/O operations
2. **Caching** - Cache frequently accessed data
3. **Error Early** - Validate inputs before processing
4. **Monitor** - Add logging to new code

## Security Best Practices

- ✅ Validate all user inputs
- ✅ Use Pydantic models for validation
- ✅ Don't log sensitive data (passwords, tokens)
- ✅ Use environment variables for secrets
- ✅ Keep dependencies updated
- ✅ Add rate limiting to new endpoints

## Dependency Updates

```bash
# Check for outdated packages
pip list --outdated

# Update a package
pip install --upgrade package-name

# Update requirements.txt
pip freeze > requirements.txt

# Test after updating
make test
```

## Release Process

1. Update version in `app/__init__.py`
2. Update CHANGELOG.md
3. Create git tag: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`
5. Create release on GitHub

## Code Review Checklist

When reviewing PRs:

- [ ] Code follows PEP 8 style guide
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance is acceptable
- [ ] Error handling is comprehensive
- [ ] Logging is appropriate
- [ ] No hardcoded values

## Asking for Help

- Check existing issues and documentation
- Create detailed bug reports with:
  - Steps to reproduce
  - Expected behavior
  - Actual behavior
  - Error logs
- Join discussions for feature requests

## Code of Conduct

- Be respectful and inclusive
- Give credit for contributions
- Help others learn
- Report issues privately if sensitive
