# Crystallize Demo Recording
# Run with: vhs demo.tape
# Install vhs: https://github.com/charmbracelet/vhs

# Configuration
Output demo.gif
Set FontSize 14
Set Width 1200
Set Height 700
Set Theme "Dracula"
Set Padding 20

# Start with a clean terminal
Type "# Crystallize - Reproducible ML Experiments"
Enter
Sleep 1s

Type "crystallize"
Sleep 500ms
Enter
Sleep 2s

# Navigate to an experiment (arrow down to select)
Down
Sleep 300ms
Down
Sleep 300ms

# Select and run the experiment
Enter
Sleep 1.5s

# Run the experiment
Type "R"
Sleep 3s

# Show the summary
Type "S"
Sleep 2s

# Toggle through some views
Type "t"
Sleep 1s
Type "t"
Sleep 1s

# Exit gracefully
Escape
Sleep 500ms
Type "q"
Sleep 500ms
