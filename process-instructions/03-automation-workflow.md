# Automation Workflow

## Process Management
1. Never start a long-running process without proper monitoring
2. Always implement timeouts for every operation:
   - Window detection: 10 seconds
   - Button detection: 5 seconds
   - Overall process: 5 minutes
3. Stop immediately when errors occur - don't continue with partial failures
4. Provide clear console output about process status
5. Allow clean interruption with Ctrl+C

## Logging Best Practices
1. Log Levels:
   - ERROR: Any error that stops the process
   - WARNING: Issues that might need attention
   - INFO: Important state changes and actions
   - DEBUG: Detailed technical information
2. Required Log Information:
   - Timestamp for every log entry
   - Process name and ID
   - Full error stack traces
   - Screen coordinates and regions
   - Color values and pixel data
   - Button detection results
3. Log File Management:
   - Separate log files by component (watcher.log, button_finder.log)
   - Rotate logs to prevent disk space issues
   - Save debug screenshots with timestamps
4. Real-time Monitoring:
   - Always pipe output to both console and log file
   - Use tee for simultaneous console/file logging
   - Show periodic status updates (every 30 seconds)

## Error Recovery
1. Stop process immediately on first error
2. Log full error context
3. Save debug screenshots
4. Clean up resources
5. Exit with appropriate status code

## Debug Protocol
1. Check logs first
2. Analyze screenshots
3. Verify coordinates
4. Test color detection
5. Validate window regions

## Feature Implementation
1. Create feature branch
2. Set up test cases first
3. Implement minimal viable code
4. Run test suite
5. Push to remote
6. Move to next feature only when current is stable

## Debug Process
1. Identify single error
2. Create debug branch
3. Write failing test
4. Fix error
5. Verify fix
6. Push branch
7. Move to next error

## Monitoring
1. Watch log files
2. Monitor test results
3. Track performance metrics
4. Log all automated actions 