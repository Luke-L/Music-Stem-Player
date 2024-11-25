# About
This is my Python Stem Player. created to make it (slightly) easier to understand the different tracks without using a full DAW like Reaper or Ableton. Is it easier? Maybe. 

The program supports .wav and .mp3 files. Ensure your audio files are in one of these formats.
The program uses threading to handle simultaneous playback of multiple tracks.
Very basic error handling is included to catch exceptions when loading audio files.
<details>
    <summary>Attributions</summary>
    <ul>
        <li><a href="https://www.flaticon.com/free-icons/drum" title="drum icons">Drum icons created by Smashicons - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/headstock" title="headstock icons">Headstock icons created by Smashicons - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/mixer" title="mixer icons">Mixer icons created by Vitaly Gorbachev - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/microphone" title="microphone icons">Microphone icons created by sonnycandra - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/electric-guitar" title="electric guitar icons">Electric guitar icons created by Yellow Frog Factory - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/mixing-table" title="mixing table icons">Mixer icons created by Freepik - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/music" title="music icons">Music icons created by Freepik - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/radio" title="radio icons">Radio icons created by Freepik - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/piano" title="piano icons">Piano icons created by Freepik - Flaticon</a></li>
    </ul>
</details>

# Before Running
Install Required Libraries:

Ensure you have Python 3 installed and install the necessary libraries using pip:
```bash
pip install pygame sounddevice soundfile numpy
```
* The pydub library requires ffmpeg to be installed on your system. Download it from FFmpeg Downloads and ensure it's added to your system's PATH.
* The soundfile library requires libsndfile to be installed on your system. For Windows, libsndfile is usually included with soundfile.

Icons for tracks require specific files instead of emoji. Ensure the location in the program is customized to match your file structure. 

# Playback
There are a few key binds right now to be aware of:

`Left Mouse` - Toggles a track on/off. Draging a track vertically adjusts the volume. 

`Right Mouse` - Temporarily <i>Solo</i>'s any track you hover over. 

`Space` - Play/pause

`L` - Load tracks

`Q` - Quit program

# Changelog

- v0.2
    - added track label and playback slider
- v0.3
    - fixed track labeling and some bugs
- v0.4
    - added icons for track buttons. These may be broken for users whose system doesnt include certain characters or fonts. 
- v0.5
    - Changed icon emojis for image files. 
    - Made a grid for the tracks to use instead of overflowing offscreen. 
    - Added timecode display and play/pause button.
- v0.6
    - Fixed audio stuttering/skipping issue due to the playback_position being updated both in the audio callback and in the main loop.
- v0.7
    - Adjusted UI elements and window size. 
    - Changed track icon names to be unified formats. 
- v0.8
    - Added a new function to find the common pattern among the loaded filenames.
    - Removed common pattern from track labels, displaying and formatting this pattern as a Title.
- v0.9
    - Added settings button to adjust the visuals of track label and title.
    - Now uses Q to exit the program with a confirm prompt.
- v1.0
    - Settings menu `show_full_labels` bug fix 
    - Cleaning up some redundant or useless code snippets.
- v1.01
    - Each track type now has a unique tint color. 
- v1.02
    - Tracks now show black or white icon and label depending on its status. 
- v1.1
    - Added Solo mode used with RMB. 
    - Better(?) icon color logic. 
- v1.2
    - Added volume controls per track. 
- v1.3
    - Adjusted icon_location to use the root/icons/ directory relative to the script, added specific track types for percussion instruments.