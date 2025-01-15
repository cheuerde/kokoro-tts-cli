import socket
import json
import numpy as np
from typing import Optional, Iterator
import sys
import re

class KokoroTTSClient:
    def __init__(self, host: str = 'localhost', port: int = 5000):
        self.host = host
        self.port = port
        
    def process_chunks(self, text_iterator: Iterator[str]) -> Iterator[str]:
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

    def synthesize(self, text: str, voice: str = 'af', speed: float = 1.0,
                  save_path: Optional[str] = None, play_audio: bool = True,
                  output_raw: bool = False, verbose: bool = False):
        """Process a single chunk of text."""
        if not text.strip():
            return
            
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                if verbose:
                    print(f"Connecting to server {self.host}:{self.port}...", file=sys.stderr)
                    
                client_socket.connect((self.host, self.port))
                
                request = {
                    'text': text,
                    'voice': voice,
                    'speed': speed,
                    'save_path': save_path
                }
                
                if verbose:
                    print(f"Processing chunk: {text[:50]}...", file=sys.stderr)
                
                # Send request
                request_data = json.dumps(request).encode('utf-8')
                client_socket.sendall(request_data)
                
                # Receive response data
                response_data = b''
                while True:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        break
                    response_data += chunk
                
                try:
                    from .streamer import AudioStreamer
                    
                    # Process audio data
                    audio = np.frombuffer(response_data, dtype=np.float32)
                    
                    streamer = AudioStreamer(
                        save_path=save_path,
                        play_audio=play_audio,
                        output_raw=output_raw
                    )
                    streamer.speed_multiplier = speed
                    
                    if len(audio) > 0:
                        streamer.play_audio(audio)
                        streamer.wait_until_done()
                    
                except Exception as e:
                    if verbose:
                        print(f"Error processing audio: {str(e)}", file=sys.stderr)
                    
        except Exception as e:
            if verbose:
                print(f"Error in synthesize: {str(e)}", file=sys.stderr)

    def process_stream(self, input_stream=sys.stdin, **kwargs):
        """Process input stream in chunks."""
        def text_generator():
            while True:
                chunk = input_stream.read(1024)
                if not chunk:
                    break
                yield chunk

        for sentence in self.process_chunks(text_generator()):
            self.synthesize(sentence, **kwargs)
