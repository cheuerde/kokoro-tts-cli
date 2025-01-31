import os
import sys
import socket
import json
import torch
import threading
import argparse
from pathlib import Path
from .streamer import (
    find_kokoro_path,
    build_model,
    generate,
    create_chunks
)

class KokoroTTSServer:
    def __init__(self, host: str = 'localhost', port: int = 5000):
        self.host = host
        self.port = port
        self.server_socket = None
        self.model = None
        self.voices = {}
        self.running = False
        
        # Initialize model
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        kokoro_path = find_kokoro_path()
        self.model = build_model(kokoro_path / 'kokoro-v0_19.pth', device)
        self.voices_dir = kokoro_path / 'voices'
        
    def load_voice(self, voice_spec: str) -> tuple:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        if ':' in voice_spec:
            voice_mix = {}
            for part in voice_spec.split(','):
                name, weight = part.split(':')
                weight = float(weight)
                if name not in self.voices:
                    self.voices[name] = torch.load(
                        self.voices_dir / f'{name}.pt',
                        weights_only=True
                    ).to(device)
                voice_mix[name] = weight
            
            mixed_voice = sum(
                self.voices[name] * weight
                for name, weight in voice_mix.items()
            )
            primary_voice = max(voice_mix.items(), key=lambda x: x[1])[0]
            return mixed_voice, primary_voice
        else:
            if voice_spec not in self.voices:
                self.voices[voice_spec] = torch.load(
                    self.voices_dir / f'{voice_spec}.pt',
                    weights_only=True
                ).to(device)
            return self.voices[voice_spec], voice_spec

    def handle_client(self, client_socket: socket.socket):
        """Handle individual client connection."""
        try:
            # Receive the request data
            request_data = b''
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                request_data += chunk
                
                try:
                    request = json.loads(request_data.decode())
                    break  # Valid JSON received
                except json.JSONDecodeError:
                    continue  # Keep reading until we have complete JSON
            
            text = request.get('text', '')
            voice_spec = request.get('voice', 'af')
            speed = request.get('speed', 1.0)
            
            voicepack, primary_voice = self.load_voice(voice_spec)
            lang = primary_voice[0]
            
            # Process text
            chunks = create_chunks(text, lang)
            
            # Generate audio for all chunks
            audio = None
            for chunk in chunks:
                chunk_audio, _ = generate(
                    self.model,
                    chunk,
                    voicepack,
                    lang,
                    speed
                )
                if chunk_audio is not None:
                    if audio is None:
                        audio = chunk_audio
                    else:
                        audio = np.concatenate([audio, chunk_audio])
            
            # Send audio data
            if audio is not None:
                client_socket.sendall(audio.tobytes())
                
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()


    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f"KokoroTTS Server running on {self.host}:{self.port}")
        
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"New connection from {addr}")
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,)
                )
                client_thread.start()
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()

def run_server():
    parser = argparse.ArgumentParser(description='Kokoro TTS Server')
    parser.add_argument('--host', default='localhost',
                      help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=5000,
                      help='Server port (default: 5000)')
    parser.add_argument('--kokoro-path', type=str,
                      help='Path to Kokoro-82M directory')
    args = parser.parse_args()

    if args.kokoro_path:
        os.environ['KOKORO_PATH'] = args.kokoro_path
        
    server = KokoroTTSServer(host=args.host, port=args.port)
    try:
        print("Starting Kokoro TTS Server - Press Ctrl+C to stop")
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop()

if __name__ == "__main__":
    run_server()