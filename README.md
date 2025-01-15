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
pip install kokoro-tts-cli
```

## Usage

### Basic TTS

```bash
# Simple text-to-speech
echo "Hello, world!" | kokoro-tts

# Specify voice
echo "Hello!" | kokoro-tts --voice af_bella

# Use specific speed
echo "Hello!" | kokoro-tts --speed 1.2

# Save to file
echo "Hello!" | kokoro-tts --save output.wav
```

### Interactive Mode

```bash
# Process text file with interactive controls
kokoro-tts -i < input.txt
```

Controls:
- Space: Pause/Resume
- Left/Right arrows: Adjust speed
- Esc: Exit

### Additional Options

```bash
# Show help
kokoro-tts --help

# Generate without playback
echo "Hello!" | kokoro-tts --no-play --save output.wav

# Show progress
echo "Hello!" | kokoro-tts --verbose

# Specify Kokoro model path
echo "Hello!" | kokoro-tts --kokoro-path /path/to/Kokoro-82M
```

## Available Voices

- af (default)
- af_bella
- af_sarah
- am_adam
- am_michael
- bf_emma
- bf_isabella
- bm_george
- bm_lewis
- af_nicole
- af_sky

## Environment Variables

- `KOKORO_PATH`: Path to Kokoro-82M directory

## Acknowledgements

This is a command-line interface for the [Kokoro TTS model](https://huggingface.co/hexgrad/Kokoro-82M). All credit for the model goes to:
- Original StyleTTS 2 architecture by [Li et al](https://github.com/yl4579/StyleTTS2)
- Kokoro training by [@rzvzn](https://huggingface.co/hexgrad/Kokoro-82M)

Claude Sonnet wrote 100% of the code and had most of the ideas for the features!

## License

Apache License 2.0 (matching Kokoro's license)