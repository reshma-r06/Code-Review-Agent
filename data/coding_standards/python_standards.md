# Python Coding Standards

## Naming Conventions
- Use snake_case for variables, functions, and module names.
- Use PascalCase for class names.
- Use UPPER_SNAKE_CASE for constants.
- Prefix private methods and variables with a single underscore _.
- Never use single-letter variable names except for loop indices.

## Function Design
- Each function must do ONE thing only.
- Functions should not exceed 30 lines of code.
- All functions must have type hints for parameters and return values.
- All public functions must have docstrings.
- Avoid mutable default arguments.

## Error Handling
- Always catch specific exceptions, never use bare except clauses.
- Log exceptions with context before re-raising.
- Never silently swallow exceptions.

## Security
- Never hardcode secrets or API keys in source code.
- Use environment variables for sensitive data.
- Always validate and sanitize user inputs.
- Use parameterized queries for database access.
- Avoid eval() or exec() with untrusted input.

## Testing
- Every public function must have at least one unit test.
- Use pytest as the testing framework.
- Aim for minimum 80% code coverage.

## Imports
- Group imports: standard library, third-party, local.
- Avoid wildcard imports.