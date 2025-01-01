# Autonomous Development Configuration

## Overview
The `.cursor.autonomous.json` file configures Cursor's autonomous development behavior, ensuring continuous operation following established processes.

## Configuration Sections

### Autonomous Mode
- `enabled`: Enables fully autonomous operation
- `autoAcceptChanges`: Automatically accepts generated changes
- `continuousOperation`: Continues to next task without prompting

### Process Flow
Defines the order and rules for feature implementation:
1. Read knowledge base
2. Create tests
3. Implement feature
4. Run tests
5. Fix errors
6. Commit changes

### Error Handling
- Single error focus principle
- Automatic retry with limits
- Prioritized error types
- Comprehensive error logging

### Git Workflow
- Standardized branch naming
- Commit message formatting
- Automatic commit and push
- Branch management rules

### Testing Protocol
- Pre-save checks
- Pre-restart verifications
- Continuous testing
- Error validation

### Logging Requirements
- Comprehensive log levels
- Required log information
- Log rotation
- Debug output management

### Monitoring
- Regular status updates
- Progress checkpoints
- Error resolution tracking
- Performance monitoring

### Timeouts
- Window detection: 10 seconds
- Button detection: 5 seconds
- Overall process: 5 minutes

## Usage
1. Place `.cursor.autonomous.json` in repository root
2. Configure paths to match repository structure
3. Adjust timeouts and intervals as needed
4. Enable autonomous mode

## Best Practices
1. Keep knowledge base updated
2. Maintain clear feature specifications
3. Review logs regularly
4. Update configuration as processes evolve 