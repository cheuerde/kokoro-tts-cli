import warnings 
warnings.simplefilter("ignore")  # Suppress all warnings
# Or if you want to be more specific:
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
import os
import sys
import queue
import time
import curses
import argparse
import sounddevice as sd
import numpy as np
import re
from typing import List, Tuple, Optional, Iterator
from pathlib import Path

def process_text_stream(text_iterator: Iterator[str]) -> Iterator[str]:
    """Process text into meaningful chunks (sentences/paragraphs)."""
    buffer = ""
    sentence_end = re.compile(r'[.!?]\s+')
    
    for chunk in text_iterator:
        buffer += chunk
        
        while True:
            match = sentence_end.search(buffer)
            if not match:
                break
                
            # Extract the complete sentence
            yield buffer[:match.end()].strip()
            buffer = buffer[match.end():]
    
    # Don't forget remaining text
    if buffer.strip():
        yield buffer.strip()

def find_kokoro_path() -> Path:
    """Find Kokoro-82M directory from common locations or environment variable."""
    if 'KOKORO_PATH' in os.environ:
        path = Path(os.environ['KOKORO_PATH'])
        if (path / 'kokoro-v0_19.pth').exists():
            return path
    
    common_paths = [
        Path.cwd() / 'Kokoro-82M',
        Path.home() / 'Kokoro-82M',
        Path.cwd().parent / 'Kokoro-82M',
    ]
    
    for path in common_paths:
        if (path / 'kokoro-v0_19.pth').exists():
            return path
    
    raise FileNotFoundError(
        "Kokoro-82M directory not found. Please either:\n"
        "1. Clone it in the current directory: git clone https://huggingface.co/hexgrad/Kokoro-82M\n"
        "2. Set KOKORO_PATH environment variable to point to your Kokoro-82M directory\n"
        "3. Place it in your home directory"
    )

# Find and add Kokoro to path
KOKORO_PATH = find_kokoro_path()
sys.path.append(str(KOKORO_PATH))

# Now import from Kokoro
from models import build_model
import torch
from kokoro import generate, phonemize, tokenize

def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences at natural boundaries."""
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in sentences if s.strip()]

def get_chunk_tokens(text: str, lang='a') -> List[int]:
    """Get actual token count for a piece of text."""
    ps = phonemize(text, lang)
    return tokenize(ps)

def split_long_sentence(sentence: str, lang='a', max_tokens: int = 450) -> List[str]:
    """Split a long sentence into smaller chunks that fit within token limit."""
    tokens = get_chunk_tokens(sentence, lang)
    if len(tokens) <= max_tokens:
        return [sentence]

    # Split points in order of preference
    split_points = [
        (r', (?=and |but |or |nor |for |so |yet )', ', '),  # Conjunctions with commas
        (r'; ', '; '),  # Semicolons
        (r', ', ', '),  # Plain commas
        (r' (?=and |but |or |nor |for |so |yet )', ' '),  # Conjunctions without commas
    ]
    
    for pattern, separator in split_points:
        parts = re.split(pattern, sentence)
        if len(parts) > 1:
            chunks = []
            current_chunk = []
            current_tokens = []
            
            for part in parts:
                test_chunk = (separator if current_chunk else '') + part
                test_tokens = get_chunk_tokens(' '.join(current_chunk) + test_chunk, lang)
                
                if len(test_tokens) > max_tokens and current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [part]
                    current_tokens = get_chunk_tokens(part, lang)
                else:
                    current_chunk.append(test_chunk)
                    current_tokens = test_tokens
            
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            
            # Verify all chunks are within token limit
            valid_chunks = True
            for chunk in chunks:
                if len(get_chunk_tokens(chunk, lang)) > max_tokens:
                    valid_chunks = False
                    break
            
            if valid_chunks:
                return chunks

    # If no good split points found, split on word boundaries as last resort
    words = sentence.split()
    chunks = []
    current_chunk = []
    current_tokens = []
    
    for word in words:
        test_chunk = ' '.join(current_chunk + [word])
        test_tokens = get_chunk_tokens(test_chunk, lang)
        
        if len(test_tokens) > max_tokens:
            if current_chunk:
                chunks.append(' '.join(current_chunk) + '...')
                current_chunk = ['...', word]
                current_tokens = get_chunk_tokens(' '.join(current_chunk), lang)
            else:
                print(f"Warning: Word '{word}' exceeds token limit and will be truncated")
                chunks.append(word[:int(len(word) * (max_tokens / len(test_tokens)))] + '...')
        else:
            current_chunk.append(word)
            current_tokens = test_tokens
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def create_chunks(text: str, lang='a', max_tokens: int = 450) -> List[str]:
    """Create chunks of text that will fit within token limit."""
    sentences = split_into_sentences(text)
    chunks = []
    current_chunk = []
    current_tokens = []
    
    for sentence in sentences:
        # Check if single sentence exceeds limit
        sentence_tokens = get_chunk_tokens(sentence, lang)
        if len(sentence_tokens) > max_tokens:
            # Process any accumulated chunks first
            if current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_tokens = []
            
            # Split the long sentence only if necessary
            sentence_chunks = split_long_sentence(sentence, lang, max_tokens)
            chunks.extend(sentence_chunks)
        else:
            # Try to add to current chunk
            test_tokens = current_tokens + sentence_tokens if current_tokens else sentence_tokens
            if not current_chunk or len(test_tokens) <= max_tokens:
                current_chunk.append(sentence)
                current_tokens = test_tokens
            else:
                # Save current chunk and start new one
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_tokens = sentence_tokens
    
    # Add the last chunk if it exists
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

class AudioStreamer:
    def __init__(self, sample_rate=24000, save_path: Optional[str] = None, 
                 play_audio: bool = True, output_raw: bool = False):
        self.sample_rate = sample_rate
        self.audio_queue = queue.Queue()
        self.current_audio = None
        self.is_playing = False
        self.is_paused = False
        self.stream = None
        self.finished = False
        self.speed_multiplier = 1.0
        self.save_path = save_path
        self.all_audio = [] if save_path else None
        self.play_audio_flag = play_audio
        self.output_raw = output_raw
        
    def callback(self, outdata, frames, time, status):
        if self.is_paused:
            outdata[:] = 0
            return
            
        try:
            if self.current_audio is None:
                self.current_audio = self.audio_queue.get_nowait()
            
            chunk_size = len(outdata)
            if len(self.current_audio) < chunk_size:
                outdata[:len(self.current_audio)] = self.current_audio.reshape(-1, 1)
                outdata[len(self.current_audio):] = 0
                self.current_audio = None
                if self.audio_queue.empty():
                    self.finished = True
                    raise sd.CallbackStop()
            else:
                outdata[:] = self.current_audio[:chunk_size].reshape(-1, 1)
                self.current_audio = self.current_audio[chunk_size:]
                
        except queue.Empty:
            outdata[:] = 0
            self.finished = True
            self.current_audio = None
            raise sd.CallbackStop()
    
    def play_audio(self, audio):
        if self.speed_multiplier != 1.0:
            from scipy import signal
            audio = signal.resample(audio, int(len(audio) / self.speed_multiplier))
        
        if self.save_path and self.all_audio is not None:
            self.all_audio.append(audio)
            
        if self.output_raw:
            sys.stdout.buffer.write(audio.astype(np.float32).tobytes())
            sys.stdout.buffer.flush()
        
        if not self.play_audio_flag:
            return
            
        self.finished = False
        self.audio_queue.put(audio)
        
        if not self.is_playing:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=self.callback
            )
            self.stream.start()
            self.is_playing = True
    
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        
    def adjust_speed(self, delta):
        self.speed_multiplier = max(0.5, min(2.0, self.speed_multiplier + delta))
    
    def wait_until_done(self):
        if not self.play_audio_flag:
            while not self.audio_queue.empty():
                _ = self.audio_queue.get()
            return
            
        while not self.finished or not self.audio_queue.empty():
            time.sleep(0.1)
            if not self.is_playing and not self.audio_queue.empty():
                self.stream = sd.OutputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    callback=self.callback
                )
                self.stream.start()
                self.is_playing = True
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.is_playing = False
            
        if self.save_path and self.all_audio:
            final_audio = np.concatenate(self.all_audio)
            from scipy.io.wavfile import write as wavfile_write
            wavfile_write(self.save_path, self.sample_rate, final_audio)

class InteractiveTTS:
    def __init__(self, model, voicepack, streamer, voice='af'):
        self.model = model
        self.voicepack = voicepack
        self.streamer = streamer
        self.voice = voice
        self.lang = voice[0]
        self.stdscr = None
        
    def process_text(self, text, verbose=False):
        chunks = create_chunks(text, self.lang)
        
        for i, chunk in enumerate(chunks, 1):
            if verbose:
                print(f"\nProcessing chunk {i}/{len(chunks)}:", file=sys.stderr)
                print(chunk, file=sys.stderr)
            
            audio, ps = generate(self.model, chunk, self.voicepack, self.lang, self.streamer.speed_multiplier)
            if audio is not None:
                self.streamer.play_audio(audio)
    
    def handle_keyboard(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        stdscr.nodelay(1)
        
        while not self.streamer.finished or not self.streamer.audio_queue.empty():
            try:
                key = stdscr.getch()
                if key != -1:
                    if key == ord(' '):
                        self.streamer.toggle_pause()
                    elif key == curses.KEY_LEFT:
                        self.streamer.adjust_speed(-0.1)
                    elif key == curses.KEY_RIGHT:
                        self.streamer.adjust_speed(0.1)
                    elif key == 27:  # ESC
                        break
                
                self.update_status()
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                break
    
    def update_status(self):
        if not self.stdscr:
            return
            
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, "Kokoro TTS Stream Controls:")
        self.stdscr.addstr(2, 0, f"Speed: {self.streamer.speed_multiplier:.1f}x [←/→]")
        self.stdscr.addstr(3, 0, f"Voice: {self.voice}")
        self.stdscr.addstr(4, 0, f"Status: {'Paused' if self.streamer.is_paused else 'Playing'} [Space]")
        self.stdscr.addstr(6, 0, "Press [Esc] to exit")
        self.stdscr.refresh()

def process_text_chunks(text: str, model, voicepack, primary_voice, 
                       streamer: AudioStreamer, speed: float, verbose: bool = False):
    """Process text in chunks for interactive mode."""
    chunks = create_chunks(text, primary_voice[0])
    for chunk in chunks:
        if verbose:
            print(f"Processing: {chunk[:50]}...", file=sys.stderr)
        audio, _ = generate(
            model,
            chunk,
            voicepack,
            primary_voice[0],
            speed
        )
        if audio is not None:
            streamer.play_audio(audio)

def show_usage_guide():
    """Show detailed usage guide with examples and explanations."""
    print("""
Kokoro TTS CLI - Text-to-Speech Interface
========================================

Basic Usage:
-----------
  echo 'Your text here' | kokoro-tts    # Basic TTS with default voice
  cat file.txt | kokoro-tts             # Process a text file
  kokoro-tts -i < story.txt             # Interactive mode with controls

Voice Options:
-------------
Single Voice:
  kokoro-tts --voice af_bella           # American female (Bella)
  kokoro-tts --voice bf_emma            # British female (Emma)
  kokoro-tts --voice am_adam            # American male (Adam)

Voice Mixing:
  kokoro-tts --voice "af_bella:0.7,bf_emma:0.3"   # 70% Bella, 30% Emma

Available Voices:
  American (en-us): af_bella, af_sarah, am_adam, am_michael, af_nicole, af_sky
  British (en-gb):  bf_emma, bf_isabella, bm_george, bm_lewis

Playback Controls:
----------------
  --speed 1.2                           # Adjust speech speed (0.5-2.0)
  --save output.wav                     # Save to WAV file
  --no-play                             # Generate without playback
  --verbose                             # Show processing details

Interactive Mode Controls:
-----------------------
  Space:        Pause/Resume
  Left/Right:   Adjust speed
  Esc:          Exit

Server/Client Usage:
------------------
For faster repeated processing, you can run a persistent server:

1. Start the server in one terminal:
   kokoro-tts-server [--host HOST] [--port PORT]

2. Use the client in another terminal:
   echo 'Your text' | kokoro-tts-client [options]
   
The server keeps the model loaded in memory for faster processing.
All regular options (voice, speed, etc.) work with the client.

Server options:
  --host HOST     Server host (default: localhost)
  --port PORT     Server port (default: 5000)

Examples:
--------
1. Basic TTS:
   echo 'Hello! How are you today?' | kokoro-tts

2. Specific voice with speed:
   echo 'Reading quickly!' | kokoro-tts --voice af_bella --speed 1.3

3. Voice mixing:
   echo 'Mixed voice test.' | kokoro-tts --voice "af_bella:0.6,bf_emma:0.4"

4. Process file interactively:
   kokoro-tts -i < story.txt

5. Save without playing:
   cat text.txt | kokoro-tts --no-play --save output.wav

For more information, use: kokoro-tts --help
""")

def main():
    parser = argparse.ArgumentParser(description='Kokoro TTS Streaming Tool')
    parser.add_argument('--voice', default='af',
                      help='Voice to use for TTS or mix specification (e.g., "af_bella:0.7,bf_emma:0.3")')
    parser.add_argument('--speed', type=float, default=1.0,
                      help='Speech speed multiplier (0.5-2.0)')
    parser.add_argument('--save', type=str,
                      help='Save audio to WAV file')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Show detailed progress')
    parser.add_argument('--interactive', '-i', action='store_true',
                      help='Enable interactive controls')
    parser.add_argument('--output-raw', action='store_true',
                      help='Output raw audio data for piping')
    parser.add_argument('--play', action='store_true', default=True,
                      help='Play audio while processing')
    parser.add_argument('--no-play', action='store_false', dest='play',
                      help='Do not play audio while processing')
    parser.add_argument('--kokoro-path', type=str,
                      help='Path to Kokoro-82M directory')
    parser.add_argument('--batch', action='store_true',
                      help='Process entire input at once (faster for wav generation, no streaming)')
    args = parser.parse_args()
    
    try:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = build_model(KOKORO_PATH / 'kokoro-v0_19.pth', device)
        
        # Handle voice loading with mixing support
        if ':' in args.voice:  # Voice mix specification
            voice_mix = {}
            voices_dir = KOKORO_PATH / 'voices'
            for part in args.voice.split(','):
                name, weight = part.split(':')
                weight = float(weight)
                if not (voices_dir / f'{name}.pt').exists():
                    raise FileNotFoundError(
                        f"Voice '{name}' not found.\n"
                        f"Available voices:\n"
                        f"  {', '.join(v.stem for v in voices_dir.glob('*.pt'))}"
                    )
                voice_mix[name] = weight
            
            mixed_voice = sum(
                torch.load(voices_dir / f'{name}.pt', weights_only=True).to(device) * weight
                for name, weight in voice_mix.items()
            )
            voicepack = mixed_voice
            primary_voice = max(voice_mix.items(), key=lambda x: x[1])[0]
        else:  # Single voice
            voice_path = KOKORO_PATH / 'voices' / f'{args.voice}.pt'
            if not voice_path.exists():
                raise FileNotFoundError(
                    f"Voice '{args.voice}' not found.\n"
                    f"Available voices:\n"
                    f"  {', '.join(v.stem for v in (KOKORO_PATH / 'voices').glob('*.pt'))}"
                )
            voicepack = torch.load(voice_path, weights_only=True).to(device)
            primary_voice = args.voice

        # Initialize audio streamer
        streamer = AudioStreamer(
            save_path=args.save,
            play_audio=args.play,
            output_raw=args.output_raw
        )
        streamer.speed_multiplier = args.speed

        if args.batch or args.interactive:
            # Process everything at once
            text = sys.stdin.read()
            
            if args.interactive:
                curses.wrapper(lambda stdscr: (
                    streamer.handle_keyboard(stdscr),
                    process_text_chunks(text, model, voicepack, primary_voice, 
                                     streamer, args.speed, args.verbose)
                ))
            else:
                # Batch processing
                chunks = create_chunks(text, primary_voice[0])
                
                if args.verbose:
                    print(f"Processing {len(chunks)} chunks in batch mode...", file=sys.stderr)
                
                all_audio = []
                for i, chunk in enumerate(chunks, 1):
                    if args.verbose:
                        print(f"Processing chunk {i}/{len(chunks)}", file=sys.stderr)
                    
                    audio, _ = generate(
                        model,
                        chunk,
                        voicepack,
                        primary_voice[0],
                        args.speed
                    )
                    if audio is not None:
                        all_audio.append(audio)
                
                if all_audio:
                    combined_audio = np.concatenate(all_audio)
                    if args.save:
                        if args.verbose:
                            print(f"Saving audio to {args.save}", file=sys.stderr)
                        from scipy.io.wavfile import write as wavfile_write
                        wavfile_write(args.save, 24000, combined_audio)
                    elif args.play:
                        streamer.play_audio(combined_audio)
                        streamer.wait_until_done()
        else:
            # Streaming mode
            def text_generator():
                while True:
                    chunk = sys.stdin.read(1024)
                    if not chunk:
                        break
                    yield chunk

            # Process input stream in chunks
            for sentence in process_text_stream(text_generator()):
                if sentence.strip():
                    if args.verbose:
                        print(f"Processing: {sentence[:50]}...", file=sys.stderr)
                    
                    chunks = create_chunks(sentence, primary_voice[0])
                    for chunk in chunks:
                        audio, _ = generate(
                            model,
                            chunk,
                            voicepack,
                            primary_voice[0],
                            args.speed
                        )
                        if audio is not None:
                            streamer.play_audio(audio)

            streamer.wait_until_done()
            
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()