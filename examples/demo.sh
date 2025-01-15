#!/bin/bash

# Function to safely echo text with exclamation marks
safe_echo() {
    echo -e "$1"
}

# Simple example
safe_echo "Hello! Basic test." | kokoro-tts

# Process a longer story
cat examples/story.txt | kokoro-tts --verbose

# Try different voices
cat examples/technical.txt | kokoro-tts --voice af_bella
cat examples/technical.txt | kokoro-tts --voice bf_emma

# Interactive mode with mixed content
kokoro-tts -i < examples/mixed.txt

# Save to file
cat examples/story.txt | kokoro-tts --save story.wav