import socket
import json
import numpy as np
from typing import Optional

class KokoroTTSClient:
    def __init__(self, host: str = 'localhost', port: int = 5000):
        self.host = host
        self.port = port
        
    def synthesize(self, text: str, voice: str = 'af', speed: float = 1.0,
                  save_path: Optional[str] = None, play_audio: bool = True,
                  output_raw: bool = False):
        from .streamer import AudioStreamer
        
        streamer = AudioStreamer(
            save_path=save_path,
            play_audio=play_audio,
            output_raw=output_raw
        )
        streamer.speed_multiplier = speed
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((self.host, self.port))
            
            request = {
                'text': text,
                'voice': voice,
                'speed': speed,
                'save_path': save_path
            }
            client_socket.send(json.dumps(request).encode('utf-8'))
            
            response = json.loads(client_socket.recv(1024).decode('utf-8'))
            num_chunks = response['chunks']
            
            for _ in range(num_chunks):
                audio_data = client_socket.recv(1024000)
                audio = np.frombuffer(audio_data, dtype=np.float32)
                streamer.play_audio(audio)
            
            streamer.wait_until_done()