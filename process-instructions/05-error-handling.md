# Error Handling Protocol

## Error Priority
1. Security issues
2. Data integrity
3. User-facing functionality
4. Performance issues
5. Code style/formatting

## Debug Steps
1. Reproduce error
2. Create failing test
3. Implement fix
4. Verify fix
5. Document solution
6. Push to debug branch

## Logging Requirements
1. Error stack trace
2. Environment context
3. Test results
4. Fix verification
5. Performance impact

# Error Handling Guidelines

## Logging Requirements
- All processes must output logs to both console and log files
- Logs should be visible in real-time during process execution
- Critical information like window detection, pixel colors, and button clicks must be logged
- Error messages must include full stack traces for debugging
- Log files should be rotated to prevent excessive disk usage

## Error Recovery 