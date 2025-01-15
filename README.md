# Kokoro TTS CLI

A command-line interface for [Kokoro TTS](https://huggingface.co/hexgrad/Kokoro-82M) with streaming and voice mixing capabilities.

## Prerequisites

1. Install espeak-ng:
```bash
# macOS
brew install espeak-ng

# Ubuntu/Debian
sudo apt-get install espeak-ng

# Windows
# Download installer from https://github.com/espeak-ng/espeak-ng/releases
```

2. Download Kokoro model and voices:
```bash
# Install git-lfs if you haven't
git lfs install

# Clone Kokoro repository
git clone https://huggingface.co/hexgrad/Kokoro-82M
```

## Installation

```bash
pip install git+https://github.com/cheuerde/kokoro-tts-cli.git
```

## Usage Examples

### Quick Start
```bash
# Simple text (use single quotes for text with exclamation marks)
echo 'Hello! How are you today?' | kokoro-tts

# Longer text
echo 'Once upon a time, in a digital realm far beyond our screens, there lived a unique artificial voice. This voice was not just any voice - it could sing, whisper, and tell stories with remarkable clarity!' | kokoro-tts
```

### Voice Selection
```bash
# American female voice (Bella)
echo 'The quick brown fox jumps over the lazy dog. This sentence contains all letters of the alphabet!' | kokoro-tts --voice af_bella

# British female voice (Emma)
echo 'Would you like a cup of tea? British voices have their own unique charm.' | kokoro-tts --voice bf_emma

# American male voice (Adam)
echo 'Deep in the mountains, a lone traveler found an ancient manuscript.' | kokoro-tts --voice am_adam
```

### Voice Mixing
```bash
# Mix American female voices (70% Bella, 30% Sarah)
echo 'Voice mixing creates interesting new voice characteristics!' | kokoro-tts --voice "af_bella:0.7,af_sarah:0.3"

# Mix female and male voices
echo 'This is a balanced mix of different voice types.' | kokoro-tts --voice "bf_emma:0.4,am_adam:0.3,af_bella:0.3"

# Create smooth transitions between voices
echo 'First part in one voice, second part in another.' | kokoro-tts --voice "af_bella:0.6,bf_emma:0.4"
```

### Speed Control
```bash
# Faster speech
echo 'This will be spoken quickly, perfect for speed reading!' | kokoro-tts --speed 1.5

# Slower speech
echo 'This will be spoken slowly and clearly, good for learning pronunciation.' | kokoro-tts --speed 0.8
```

### File Processing
```bash
# Process a text file
cat story.txt | kokoro-tts --verbose

# Save to audio file
cat article.txt | kokoro-tts --save output.wav

# Process and save without playback
cat script.txt | kokoro-tts --no-play --save output.wav
```

### Interactive Mode
```bash
# Process file with interactive controls
kokoro-tts -i < story.txt

# Process text from clipboard (macOS)
pbpaste | kokoro-tts -i
```

Interactive Controls:
- Space: Pause/Resume
- Left/Right arrows: Adjust speed (0.5x - 2.0x)
- Esc: Exit

### Example Text Files

The repository includes example texts in `examples/`:
```bash
# Story example
cat examples/story.txt | kokoro-tts --voice af_bella

# Technical text
cat examples/technical.txt | kokoro-tts --voice "af_bella:0.6,am_adam:0.4"

# Mixed content with voice mixing
cat examples/mixed.txt | kokoro-tts --voice "bf_emma:0.5,af_sarah:0.5"
```

### Server Mode

For faster repeated processing, you can run Kokoro TTS in server mode. This keeps the model loaded in memory, significantly reducing processing time for subsequent requests.

1. Start the server in one terminal:
```bash
# Start with default settings (localhost:5000)
kokoro-tts-server

# Custom host and port
kokoro-tts-server --host 0.0.0.0 --port 5001
```

2. Use the client in another terminal:
```bash
# Basic usage
echo 'Hello!' | kokoro-tts-client

# All regular options work with the client
echo 'Mixed voice test' | kokoro-tts-client --voice "af_bella:0.7,bf_emma:0.3" --speed 1.2

# Process files
cat story.txt | kokoro-tts-client --voice af_bella

# Save to audio file
cat script.txt | kokoro-tts-client --save output.wav
```

Server options:
- `--host`: Server host (default: localhost)
- `--port`: Server port (default: 5000)
- `--kokoro-path`: Path to Kokoro-82M directory

Client options:
- All options available in regular mode (voice, speed, save, etc.)
- `--host`: Server host (default: localhost)
- `--port`: Server port (default: 5000)

The server mode is particularly useful when:
- Processing multiple texts in succession
- Running a TTS service on a powerful machine
- Reducing startup time for frequent TTS operations

## Available Voices

American English (en-us):
- af_bella - Bella (female)
- af_sarah - Sarah (female)
- am_adam - Adam (male)
- am_michael - Michael (male)
- af_nicole - Nicole (female)
- af_sky - Sky (female)

British English (en-gb):
- bf_emma - Emma (female)
- bf_isabella - Isabella (female)
- bm_george - George (male)
- bm_lewis - Lewis (male)

## Environment Variables

- `KOKORO_PATH`: Path to Kokoro-82M directory
  ```bash
  export KOKORO_PATH=/path/to/Kokoro-82M
  ```

## Tips

1. Use single quotes for text with exclamation marks:
```bash
echo 'Wow! This is amazing!' | kokoro-tts
```

2. For long texts, use files:
```bash
echo 'Long text...' > input.txt
kokoro-tts < input.txt
```

3. Mix voices for unique characteristics:
```bash
# Warm, friendly voice
kokoro-tts --voice "af_bella:0.6,bf_emma:0.4"

# Authoritative voice
kokoro-tts --voice "am_adam:0.7,bm_george:0.3"
```

## Acknowledgements

This is a command-line interface for the [Kokoro TTS model](https://huggingface.co/hexgrad/Kokoro-82M). All credit for the model goes to:
- Original StyleTTS 2 architecture by [Li et al](https://github.com/yl4579/StyleTTS2)
- Kokoro training by [@rzvzn](https://huggingface.co/hexgrad/Kokoro-82M)

Claude Sonnet wrote 100% of the code and had most of the ideas for the features!

## License

Apache License 2.0 (matching Kokoro's license)