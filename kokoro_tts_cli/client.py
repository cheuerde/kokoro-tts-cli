import socket
import json
import numpy as np
from typing import Optional
import sys

class KokoroTTSClient:
    def __init__(self, host: str = 'localhost', port: int = 5000):
        self.host = host
        self.port = port
        
    def synthesize(self, text: str, voice: str = 'af', speed: float = 1.0,
                  save_path: Optional[str] = None, play_audio: bool = True,
                  output_raw: bool = False, verbose: bool = False):
        from .streamer import AudioStreamer
        
        if verbose:
            print(f"Connecting to server {self.host}:{self.port}...", file=sys.stderr)
        
        streamer = AudioStreamer(
            save_path=save_path,
            play_audio=play_audio,
            output_raw=output_raw
        )
        streamer.speed_multiplier = speed
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                if verbose:
                    print("Establishing connection...", file=sys.stderr)
                    
                client_socket.connect((self.host, self.port))
                
                request = {
                    'text': text,
                    'voice': voice,
                    'speed': speed,
                    'save_path': save_path
                }
                
                if verbose:
                    print("Sending request...", file=sys.stderr)
                    print(f"Text: {text}", file=sys.stderr)
                
                # Send request with length prefix
                request_data = json.dumps(request).encode('utf-8')
                length_prefix = len(request_data).to_bytes(4, byteorder='big')
                client_socket.sendall(length_prefix + request_data)
                
                if verbose:
                    print("Waiting for response...", file=sys.stderr)
                
                # Receive response length
                response_length = int.from_bytes(client_socket.recv(4), byteorder='big')
                
                # Receive full response
                response_data = b''
                while len(response_data) < response_length:
                    chunk = client_socket.recv(min(4096, response_length - len(response_data)))
                    if not chunk:
                        raise ConnectionError("Server connection lost")
                    response_data += chunk
                
                response = json.loads(response_data.decode('utf-8'))
                num_chunks = response['chunks']
                
                if verbose:
                    print(f"Receiving {num_chunks} audio chunks...", file=sys.stderr)
                
                for i in range(num_chunks):
                    if verbose:
                        print(f"Receiving chunk {i+1}/{num_chunks}...", file=sys.stderr)
                    
                    # Receive chunk length
                    chunk_length = int.from_bytes(client_socket.recv(4), byteorder='big')
                    
                    # Receive chunk data
                    audio_data = b''
                    while len(audio_data) < chunk_length:
                        chunk = client_socket.recv(min(32768, chunk_length - len(audio_data)))
                        if not chunk:
                            raise ConnectionError("Server connection lost")
                        audio_data += chunk
                    
                    audio = np.frombuffer(audio_data, dtype=np.float32)
                    streamer.play_audio(audio)
                
                if verbose:
                    print("Waiting for playback to complete...", file=sys.stderr)
                
                streamer.wait_until_done()
                
        except ConnectionRefusedError:
            print(f"Error: Could not connect to server at {self.host}:{self.port}", file=sys.stderr)
            print("Make sure the server is running using: kokoro-tts-server", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)