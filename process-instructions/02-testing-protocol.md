# Testing Protocol

## Pre-Save Testing
1. Run unit tests before saving files
2. Verify no new tests are broken
3. Run linting checks
4. Type checking (if TypeScript)

## Pre-Restart Testing
1. Run full test suite
2. Check for console errors
3. Verify database migrations
4. Check API endpoints

## Browser Testing
1. Open Puppeteer instance
2. Run UI tests
3. Check console for errors
4. Verify network requests 