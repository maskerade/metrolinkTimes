# Modernization Guide: Tornado → FastAPI + uv + Python 3.12

This document outlines the complete modernization of the Metrolink Times project from Tornado to FastAPI with modern Python tooling.

## What Changed

### Major Updates
- **Python**: Upgraded from 3.7+ to 3.12+ (latest stable)
- **Package Manager**: Migrated from pip to uv for faster, more reliable dependency management
- **Web Framework**: Replaced Tornado with FastAPI
- **Build System**: Switched from setuptools to hatchling
- **Code Quality**: Added ruff for linting and formatting
- **Testing**: Modern pytest setup with async support

### Dependencies
- **Removed**: `tornado~=6.1.0`
- **Added**: `fastapi>=0.104.0`, `uvicorn[standard]>=0.24.0`
- **Updated**: All dependencies to latest compatible versions
- **Modernized**: Dependency specifications (removed upper bounds where appropriate)

### New Files
- `metrolinkTimes/api.py` - New FastAPI-based web application
- `metrolinkTimes/__init__.py` - Package version information
- `run_fastapi.py` - Development script with uv integration
- `Dockerfile.fastapi` - Modern Docker configuration with uv
- `scripts/dev.py` - Development utilities
- `tests/` - Modern test suite with pytest
- `.github/workflows/ci.yml` - GitHub Actions CI/CD pipeline
- `.python-version` - Python version specification for uv
- `uv.lock` - Dependency lock file
- `.gitignore` - Comprehensive gitignore for Python projects

### Modified Files
- `pyproject.toml` - Updated dependencies and Python version
- `metrolinkTimes/__main__.py` - Updated to use FastAPI/uvicorn
- `metrolinkTimes/metrolinkTimes.py` - Converted to legacy compatibility wrapper
- `README.md` - Updated installation and usage instructions

## Key Improvements

### 1. Automatic API Documentation
FastAPI provides interactive API docs out of the box:
- Swagger UI: `http://localhost:5000/docs`
- ReDoc: `http://localhost:5000/redoc`

### 2. Type Safety
- Pydantic models for request/response validation
- Automatic type checking and conversion
- Better error messages for invalid requests

### 3. Modern Python Features
- Type hints throughout the codebase
- Async/await syntax (though the core logic remains the same)
- Better error handling with HTTP status codes

### 4. Query Parameter Validation
FastAPI automatically validates and documents query parameters:
```python
async def get_platform_info(
    station_name: str,
    platform_id: str,
    predictions: bool = Query(True, description="Include predictions"),
    # ... other parameters
):
```

### 5. Better Development Experience
- Auto-reload during development
- Better error messages
- Built-in request/response logging

## API Compatibility

The FastAPI version maintains full backward compatibility with the original Tornado API:

- All endpoints remain the same (`/`, `/debug/`, `/station/`, etc.)
- Query parameters work identically
- Response formats are unchanged
- CORS configuration is preserved

## Running the Application

### With uv (Recommended)
```bash
# Install dependencies and run
uv sync
uv run python -m metrolinkTimes

# Development with auto-reload
uv run python run_fastapi.py

# Run tests
uv run pytest

# Lint and format code
uv run ruff check metrolinkTimes/
uv run ruff format metrolinkTimes/
```

### Traditional Python
```bash
# Install and run
pip install -e .
python -m metrolinkTimes
```

### Docker (Modern)
```bash
# Build with uv
docker build -f Dockerfile.fastapi -t metrolink-times .
docker run -p 5000:5000 -v /path/to/config:/etc/metrolinkTimes metrolink-times
```

## Core Logic Unchanged

The migration only affects the web layer. All the core tram tracking logic in `tramGraph.py` and `tfgmMetrolinksAPI.py` remains exactly the same:

- Tram prediction algorithms
- Graph-based network modeling  
- Real-time data processing
- Background update loops

## Benefits of the Migration

### Web Framework (FastAPI)
1. **Automatic Documentation**: OpenAPI/Swagger docs at `/docs` and `/redoc`
2. **Type Safety**: Pydantic validation prevents runtime errors
3. **Performance**: One of the fastest Python web frameworks
4. **Modern Async**: Built-in async support with proper error handling
5. **Standards Compliant**: Full OpenAPI 3.0+ and JSON Schema support

### Package Management (uv)
1. **Speed**: 10-100x faster than pip for dependency resolution
2. **Reliability**: Deterministic builds with lock files
3. **Simplicity**: Single tool for virtual environments and package management
4. **Cross-platform**: Consistent behavior across all platforms
5. **Modern**: Built in Rust, actively developed by Astral

### Python 3.12
1. **Performance**: Significant speed improvements over 3.7
2. **Type System**: Better type hints and error messages
3. **Security**: Latest security patches and improvements
4. **Language Features**: Pattern matching, better error messages, and more

### Development Experience
1. **Fast Setup**: `uv sync` installs everything in seconds
2. **Modern Tooling**: Ruff for lightning-fast linting and formatting
3. **CI/CD**: GitHub Actions workflow with comprehensive testing
4. **Docker**: Multi-stage builds with uv for smaller, faster images

## Backward Compatibility

The original Tornado implementation is preserved in `metrolinkTimes.py` as a compatibility wrapper, but the FastAPI version is now the recommended approach for new deployments.