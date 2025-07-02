# Python Import Fix for magic8-accuracy-predictor

## The Problem

Python relative imports fail when running scripts directly:
```bash
# This fails with: ImportError: attempted relative import with no known parent package
python src/prediction_api.py
```

The issue occurs because:
- When running a script directly, Python sets `__name__` to `__main__`
- The script is not recognized as part of a package
- Relative imports like `from .data_manager import DataManager` fail

## The Solution

### Method 1: Run with Uvicorn (Recommended)
```bash
# From the project root directory
python -m uvicorn src.prediction_api:app --reload
```

This starts the FastAPI app with hot reload support.

### Method 2: Use Startup Scripts
```bash
# These scripts handle the module execution properly
./start_api_with_checks.py    # With pre-flight checks
./run_prediction_api.py        # Simple runner
```

### Method 3: Manual Execution
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -m uvicorn src.prediction_api:app --reload
```

## Fixed Files

1. **prediction_api.py**: `uvicorn.run` now uses the import string `src.prediction_api:app`
2. **start_api_with_checks.py**: Launches uvicorn directly
3. **run_prediction_api.py**: Simple uvicorn runner script

## Why This Matters

- **Relative imports** (`from .module import X`) are cleaner and more maintainable for internal modules
- **Absolute imports** require managing PYTHONPATH or sys.path manipulation
- **Module execution** (`-m` flag) provides the best of both worlds

## Testing the Fix

```bash
# Test the API startup
python -m uvicorn src.prediction_api:app --reload

# Or use the startup script
./start_api_with_checks.py
```

You should see:
- API starts without import errors
- Model loads successfully
- IBKR connection established (with proper fallbacks for unsubscribed symbols)

## For Other Scripts

If you have other scripts in src/ that need to be run directly:
1. Use `python -m src.script_name` instead of `python src/script_name.py`
2. Or create a runner script in the project root
3. Or add proper sys.path manipulation at the top of the script

## Best Practices

1. **Entry points** (scripts meant to be run directly) should be in the project root
2. **Modules** (imported by other code) should use relative imports
3. **Tests** should be run with pytest which handles imports properly
4. **Production** deployments should use proper entry points or WSGI/ASGI servers
