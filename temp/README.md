# /temp Directory

This directory contains temporary utilities, reference files, and development scripts that are useful during development but not part of the core application structure.

## Contents

### Utility Scripts
- `verify_database.py` - Manual database state verification tool
- Use for debugging and inspecting current database contents
- Run when you need to check what data exists after running tests

### Validation Scripts
- `test_model_validation.py` - SQLModel class structure and schema alignment validation
- `test_rebuilt_api.py` - API endpoints and database operations validation
- These scripts test model instantiation, field validation, and CRUD operations
- Run to validate schema changes and ensure API-database alignment

### Reference Files
- `schema_design.py` - Complete SQLModel schema design reference
- `api_contract.py` - Complete API endpoint contract reference
- These files contain comprehensive designs for future implementation
- Use as reference when building out the full application

## Usage

These scripts are meant to be run directly from the project root:

```bash
# Verify current database state
python temp/verify_database.py

# Validate SQLModel class structure and field definitions
python temp/test_model_validation.py

# Validate API endpoints and database operations
python temp/test_rebuilt_api.py

# Reference the complete schema design
# (Use schema_design.py as a reference when implementing models)
```

## Note

Files in this directory are:
- **Temporary**: May be removed or reorganized as the project evolves
- **Developmental**: Used for debugging, verification, and reference during development
- **Non-production**: Not part of the main application code or test suite

For production code, see:
- `/app/` - Main application code
- `/tests/` - Pytest test suite