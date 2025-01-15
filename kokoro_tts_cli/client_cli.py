import argparse
import sys
from .client import KokoroTTSClient
from .streamer import show_usage_guide

def run_client():
    """Entry point for the client CLI tool."""
    parser = argparse.ArgumentParser(description='Kokoro TTS Client')
    parser.add_argument('--voice', default='af',
                      help='Voice to use for TTS or mix specification (e.g., "af_bella:0.7,bf_emma:0.3")')
    parser.add_argument('--speed', type=float, default=1.0,
                      help='Speech speed multiplier (0.5-2.0)')
    parser.add_argument('--save', type=str,
                      help='Save audio to WAV file')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Show detailed progress')
    parser.add_argument('--output-raw', action='store_true',
                      help='Output raw audio data for piping')
    parser.add_argument('--play', action='store_true', default=True,
                      help='Play audio while processing')
    parser.add_argument('--no-play', action='store_false', dest='play',
                      help='Do not play audio while processing')
    parser.add_argument('--host', default='localhost',
                      help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=5000,
                      help='Server port (default: 5000)')
    parser.add_argument('--help-guide', action='store_true',
                      help='Show detailed usage guide')
    args = parser.parse_args()

    if args.help_guide:
        show_usage_guide()
        return

    try:
        client = KokoroTTSClient(host=args.host, port=args.port)
        text = sys.stdin.read()
        
        if args.verbose:
            print(f"Connecting to server at {args.host}:{args.port}", file=sys.stderr)
            
        client.synthesize(
            text=text,
            voice=args.voice,
            speed=args.speed,
            save_path=args.save,
            play_audio=args.play,
            output_raw=args.output_raw
        )
        
    except ConnectionRefusedError:
        print(f"\nError: Could not connect to server at {args.host}:{args.port}", file=sys.stderr)
        print("Make sure the server is running using: kokoro-tts-server", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_client()