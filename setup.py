from setuptools import setup, find_packages

setup(
    name="kokoro-tts-cli",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'kokoro-tts=kokoro_tts_cli.streamer:main',
            'kokoro-tts-server=kokoro_tts_cli.server:run_server',
            'kokoro-tts-client=kokoro_tts_cli.client_cli:run_client',
        ],
    },
    install_requires=[
        "torch>=2.0.0",
        "tqdm",
        "sounddevice",
        "scipy",
        "numpy",
        "phonemizer",
        "transformers",
    ],
)