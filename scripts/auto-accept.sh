#!/bin/bash

# Function to simulate cursor accept action
accept_changes() {
  # Using xdotool to simulate keyboard/mouse actions
  # This assumes the Cursor accept button is in a consistent location
  xdotool search --name "Cursor" windowactivate --sync key Return
}

# Watch for changes and auto-accept
watch_and_accept() {
  while true; do
    if [[ -f ".cursor-changes-pending" ]]; then
      accept_changes
      sleep 1
    fi
    sleep 0.5
  done
}

# Install xdotool if not present
if ! command -v xdotool &> /dev/null; then
    echo "Installing xdotool..."
    sudo apt-get update && sudo apt-get install -y xdotool
fi

# Start the watcher
watch_and_accept 