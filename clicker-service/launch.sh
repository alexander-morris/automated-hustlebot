#!/bin/bash

# Check for screen recording permission
if ! tccutil query Screen | grep -q "python.*AUTHORIZED"; then
    echo "Requesting screen recording permission..."
    osascript -e '
        tell application "System Events"
            activate
            display dialog "Cursor Watcher needs screen recording permission to function.\n\nPlease grant permission in System Preferences." buttons {"Open System Preferences", "Cancel"} default button 1
        end tell
    '
    if [ $? -eq 0 ]; then
        open "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"
        echo "Please grant permission and run the script again"
        exit 1
    fi
fi

# Start the watcher with proper permissions
python3 cursor_watcher.py 