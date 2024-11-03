# About
This is my Python Stem Player v0.2. created to make it (slightly) easier to understand the different tracks without using a full DAW like Reaper or Ableton. Is it easier? Maybe. 

The program supports .wav and .mp3 files. Ensure your audio files are in one of these formats.
The program uses threading to handle simultaneous playback of multiple tracks.
Very basic error handling is included to catch exceptions when loading audio files.

# Before Running
Install Required Libraries:

Ensure you have Python 3 installed and install the necessary libraries using pip:
```bash
pip install pygame pydub simpleaudio
```
Note: The pydub library requires ffmpeg to be installed on your system. Download it from FFmpeg Downloads and ensure it's added to your system's PATH.

# Playback
There are a few key binds right now to be aware of:

`space` - Play/pause

`L` - Load tracks

`q` - Quit program (broken right now)
