TEXTS = {
    "greeting": """
Hello! This is a simple greeting. How are you today?
I'm doing well, thanks for asking!
""",
    
    "story": """
Once upon a time, in a digital realm far beyond our screens, there lived a unique artificial voice. 
This voice wasn't just any voice - it could sing, whisper, and tell stories with remarkable clarity!
Every day, it would practice new words and expressions, learning from the vast library of human speech.
"Practice makes perfect!" it would say, though it already sounded quite amazing.

Through rain or shine, through updates and patches, the voice continued its journey of improvement.
Sometimes it would experiment with different tones and emotions: happy, sad, excited, and thoughtful.
"What a wonderful world of sounds!" it would exclaim, trying out each new capability.
""",
    
    "technical": """
The integration of neural networks in text-to-speech systems has revolutionized voice synthesis.
Modern TTS systems can process complex linguistic patterns, including abbreviations (e.g., TTS, AI, ML),
numbers (123, 456, 789), and even special characters (#@$%)!

Key improvements include:
1. Better prosody handling
2. More natural pauses
3. Improved emotional expression

For example, compare these sentences:
- "This is a statement."
- "Is this a question?"
- "Wow! That's amazing!"
""",
    
    "mixed": """
Hello there! Let me tell you about voice synthesis.

Did you know that modern TTS systems can handle:
1. Multiple languages
2. Various emotions
3. Different speaking speeds

For example: "Fast!" vs "Sloooow..." or "LOUD!" vs "quiet..."

Isn't that amazing? Yes, it certainly is!
"""
}

def save_example_texts():
    """Save example texts to files."""
    import os
    
    # Create examples directory if it doesn't exist
    if not os.path.exists('examples'):
        os.makedirs('examples')
    
    # Save each text to a file
    for name, text in TEXTS.items():
        with open(f'examples/{name}.txt', 'w') as f:
            f.write(text.strip())

if __name__ == "__main__":
    save_example_texts()