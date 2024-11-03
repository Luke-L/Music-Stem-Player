# About
This is my Python Stem Player v0.4. created to make it (slightly) easier to understand the different tracks without using a full DAW like Reaper or Ableton. Is it easier? Maybe. 

The program supports .wav and .mp3 files. Ensure your audio files are in one of these formats.
The program uses threading to handle simultaneous playback of multiple tracks.
Very basic error handling is included to catch exceptions when loading audio files.

# Before Running
Install Required Libraries:

Ensure you have Python 3 installed and install the necessary libraries using pip:
```bash
pip install pygame sounddevice soundfile numpy
```
* The pydub library requires ffmpeg to be installed on your system. Download it from FFmpeg Downloads and ensure it's added to your system's PATH.
* The soundfile library requires libsndfile to be installed on your system. For Windows, libsndfile is usually included with soundfile.

Also if you dont have Segoe UI Emoji and cannot install it, you will have to change to a different font ("Apple Color Emoji" on macOS, or "Noto Color Emoji" on Linux) to see the icons for each track. 


# Playback
There are a few key binds right now to be aware of:

`space` - Play/pause

`L` - Load tracks

`q` - Quit program (broken right now)
