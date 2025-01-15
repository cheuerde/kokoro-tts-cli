from setuptools import setup, find_packages

setup(
    name="kokoro-tts-cli",
    version="0.1.0",
    author="Claas Heuer",
    author_email="claasheuer@googlemail.com",
    description="A CLI for Kokoro TTS with streaming and voice mixing capabilities",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "torch",
        "sounddevice",
        "scipy",
    ],
    entry_points={
        'console_scripts': [
            'kokoro-tts=kokoro_tts_cli.streamer:main',  # existing CLI
            'kokoro-tts-server=kokoro_tts_cli.server:run_server',  # new server
            'kokoro-tts-client=kokoro_tts_cli.client_cli:run_client',  # new client
        ],
    },
    python_requires='>=3.7',
)