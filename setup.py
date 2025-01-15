# setup.py
from setuptools import setup, find_packages

setup(
    name="kokoro-tts-cli",
    packages=find_packages(),
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