# Git Workflow Process

## Branch Strategy
1. Feature Branches
   - Format: `feature/[feature-number]-[feature-name]`
   - Example: `feature/1-referral-gating`
   - One branch per feature implementation

2. Debug Branches
   - Format: `debug/[feature-number]-[bug-description]`
   - Example: `debug/1-referral-validation-fix`
   - Can be multiple per feature

3. Branch Management
   - Never merge directly to main
   - Push all branches to remote
   - Leave merging for human review

## Commit Strategy
1. Atomic commits with clear messages
2. Format: `[type]([scope]): [description]`
   - Example: `feat(referral): add code validation endpoint`
   - Example: `fix(auth): resolve token expiration issue` 