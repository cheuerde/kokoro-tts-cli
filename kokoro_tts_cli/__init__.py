from .streamer import (
    AudioStreamer,
    InteractiveTTS,
    main,
    create_chunks,
    find_kokoro_path,
)

__version__ = "0.1.0"
__author__ = "Claas Heuer"
__email__ = "claasheuer@googlemail.com"

# Export main classes and functions
__all__ = [
    "AudioStreamer",
    "InteractiveTTS",
    "main",
    "create_chunks",
    "find_kokoro_path",
]