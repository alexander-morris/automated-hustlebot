#!/bin/bash

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate Python environment if it exists
if [ -d "$DIR/.venv" ]; then
    source "$DIR/.venv/bin/activate"
fi

# Install required packages if needed
pip install -r "$DIR/requirements.txt" > /dev/null 2>&1

# Start the clickbot in the background
echo "Starting ClickBot..."
python "$DIR/clickbot.py" &

# Save the process ID
echo $! > "$DIR/temp/clickbot.pid"

echo "ClickBot started. To stop it, run: kill $(cat "$DIR/temp/clickbot.pid")" 