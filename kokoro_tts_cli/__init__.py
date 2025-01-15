from .streamer import (
    AudioStreamer,
    InteractiveTTS,
    main,
    create_chunks,
    find_kokoro_path,
)

# Optional server/client components
from .server import KokoroTTSServer
from .client import KokoroTTSClient

__version__ = "0.1.0"
__author__ = "Claas Heuer"
__email__ = "claasheuer@googlemail.com"

# Export main classes and functions
__all__ = [
    # Core components
    "AudioStreamer",
    "InteractiveTTS",
    "main",
    "create_chunks",
    "find_kokoro_path",
    # Server/Client components
    "KokoroTTSServer",
    "KokoroTTSClient",
]