#!/bin/bash
# Alternative demo recording using tmux + asciinema
#
# Usage:
#   1. Start recording:  asciinema rec demo.cast
#   2. In another terminal: ./scripts/record-demo.sh
#   3. Stop recording: Ctrl+D in the asciinema terminal
#   4. Convert to GIF: agg demo.cast demo.gif (or use asciinema web)
#
# Or just run this while screen recording with OBS/etc.

set -e

SESSION="crystallize-demo"

# Kill any existing session
tmux kill-session -t "$SESSION" 2>/dev/null || true

# Create new session
tmux new-session -d -s "$SESSION" -x 120 -y 30

# Give it a moment
sleep 0.5

# Type the intro comment
tmux send-keys -t "$SESSION" "# Crystallize - Reproducible ML Experiments" Enter
sleep 1

# Launch crystallize
tmux send-keys -t "$SESSION" "crystallize"
sleep 0.5
tmux send-keys -t "$SESSION" Enter
sleep 2

# Navigate down to an experiment
tmux send-keys -t "$SESSION" Down
sleep 0.3
tmux send-keys -t "$SESSION" Down
sleep 0.3

# Run selected experiment
tmux send-keys -t "$SESSION" Enter
sleep 1.5

# Start the run
tmux send-keys -t "$SESSION" "R"
sleep 3

# Show summary
tmux send-keys -t "$SESSION" "S"
sleep 2

# Toggle plain text view
tmux send-keys -t "$SESSION" "t"
sleep 1
tmux send-keys -t "$SESSION" "t"
sleep 1

# Exit
tmux send-keys -t "$SESSION" Escape
sleep 0.5
tmux send-keys -t "$SESSION" "q"
sleep 0.5

echo ""
echo "Demo complete! Attach to see the result:"
echo "  tmux attach -t $SESSION"
echo ""
echo "Or kill the session:"
echo "  tmux kill-session -t $SESSION"
