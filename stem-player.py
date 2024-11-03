import pygame
import sys
import os
from pygame.locals import *
from tkinter import Tk
from tkinter import filedialog
import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import time

# v0.5
# Changed icon emojis for image files. Made a grid for the tracks to use instead of overflowing offscreen. Added timecode display and play/pause button.

# Initialize Pygame
pygame.init()

# Set up the screen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Music Stem Player and Visualizer")

# List to hold the tracks
tracks = []
total_duration = 0  # Total duration of the longest track in seconds
playback_position = 0  # Current playback position in seconds
playing = False
mute_flags = []
audio_thread = None
stop_event = threading.Event()
seek_event = threading.Event()
seek_position = 0

# Mapping of track types to icon image filenames
# Adjust the icon_location to point to your icons directory
icon_location = "C:\\Users\\games\\Documents\\icons"
track_type_icons = {
    'guitar': os.path.join(icon_location, 'electric-guitar.png'),
    'bass': os.path.join(icon_location, 'bass-guitar.png'),
    'drums': os.path.join(icon_location, 'drums.png'),
    'percussion': os.path.join(icon_location, 'drums.png'),
    'piano': os.path.join(icon_location, 'piano-keyboard.png'),
    'synth': os.path.join(icon_location, 'sound mixer.png'),
    'instrum': os.path.join(icon_location, 'mixing-table.png'),
    'vocals': os.path.join(icon_location, 'microphone.png'),
    'other': os.path.join(icon_location, 'wave-sound.png'),
}

# UI Elements
MENU_BAR_HEIGHT = 40
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 30
PLAY_BUTTON_SIZE = 50

# Load play and pause button images or create simple shapes
play_button_image = pygame.Surface((PLAY_BUTTON_SIZE, PLAY_BUTTON_SIZE), pygame.SRCALPHA)
pygame.draw.polygon(play_button_image, (0, 255, 0), [(15, 10), (15, 40), (40, 25)])

pause_button_image = pygame.Surface((PLAY_BUTTON_SIZE, PLAY_BUTTON_SIZE), pygame.SRCALPHA)
pygame.draw.rect(pause_button_image, (255, 0, 0), (15, 10, 10, 30))
pygame.draw.rect(pause_button_image, (255, 0, 0), (30, 10, 10, 30))

def get_track_type(filename):
    """Determine the track type based on keywords in the filename."""
    filename_lower = filename.lower()
    if 'electric-guitar' in filename_lower or 'guitar' in filename_lower:
        return 'guitar'
    elif 'bass-guitar' in filename_lower or 'bass' in filename_lower:
        return 'bass'
    elif 'drums' in filename_lower:
        return 'drums'
    elif 'percussion' in filename_lower:
        return 'percussion'
    elif 'piano' in filename_lower or 'piano-keyboard' in filename_lower:
        return 'piano'
    elif 'synth' in filename_lower or 'sound mixer' in filename_lower:
        return 'synth'
    elif 'instrum' in filename_lower or 'mixing-table' in filename_lower:
        return 'instrum'
    elif 'vocals' in filename_lower or 'microphone' in filename_lower:
        return 'vocals'
    else:
        return 'other'

def load_sound_files():
    """Function to load sound files using a file dialog."""
    global total_duration, playback_position, playing, tracks, mute_flags, stop_event, audio_thread
    root = Tk()
    root.withdraw()  # Hide the root window
    file_paths = filedialog.askopenfilenames(filetypes=[("Audio Files", "*.wav *.mp3 *.flac")])
    root.destroy()
    if not file_paths:
        return
    # Stop any ongoing playback
    if playing:
        stop_event.set()
        audio_thread.join()
        playing = False
    tracks = []
    mute_flags = []
    max_duration = 0
    for file_path in file_paths:
        try:
            # Read audio file
            data, samplerate = sf.read(file_path, dtype='float32')
            if len(data.shape) == 1:
                data = np.expand_dims(data, axis=1)  # Convert mono to stereo
            duration = len(data) / samplerate
            label = os.path.basename(file_path)
            # Replace hyphens with spaces and underscores with line breaks
            label = label.replace('-', ' ')
            label = label.replace('_', '\n')
            track_type = get_track_type(label)
            # Load icon image
            icon_path = track_type_icons.get(track_type, os.path.join(icon_location, 'music-notes.png'))
            icon_image = pygame.image.load(icon_path).convert_alpha()
            # Scale icon to fit in the box
            icon_size = (64, 64)
            icon_image = pygame.transform.smoothscale(icon_image, icon_size)
            tracks.append({
                'data': data,
                'samplerate': samplerate,
                'label': label,
                'type': track_type,
                'icon': icon_image,
            })
            mute_flags.append(False)  # Initially, all tracks are unmuted
            if duration > max_duration:
                max_duration = duration
        except Exception as e:
            print(f"Could not load sound file {file_path}: {e}")
    total_duration = max_duration
    playback_position = 0  # Reset playback position
    playing = False

def draw_menu_bar():
    """Function to draw the top menu bar."""
    # Draw menu bar background
    pygame.draw.rect(screen, (70, 70, 70), (0, 0, SCREEN_WIDTH, MENU_BAR_HEIGHT))
    # Draw "Load Tracks" button
    font = pygame.font.SysFont(None, 24)
    load_text = font.render("Load Tracks", True, (255, 255, 255))
    load_button_rect = pygame.Rect(10, 5, BUTTON_WIDTH, BUTTON_HEIGHT)
    pygame.draw.rect(screen, (100, 100, 100), load_button_rect)
    screen.blit(load_text, (load_button_rect.x + 10, load_button_rect.y + 5))
    # Store button rect for interaction
    global load_button_rect_global
    load_button_rect_global = load_button_rect

def draw_play_pause_button():
    """Function to draw the play/pause button."""
    x = (SCREEN_WIDTH - PLAY_BUTTON_SIZE) // 2
    y = SCREEN_HEIGHT - 150
    play_button_rect = pygame.Rect(x, y, PLAY_BUTTON_SIZE, PLAY_BUTTON_SIZE)
    if playing:
        screen.blit(pause_button_image, (x, y))
    else:
        screen.blit(play_button_image, (x, y))
    # Store button rect for interaction
    global play_button_rect_global
    play_button_rect_global = play_button_rect

def draw_timecode():
    """Function to display the current playback time and total duration."""
    if total_duration == 0:
        return
    font = pygame.font.SysFont(None, 24)
    current_minutes = int(playback_position) // 60
    current_seconds = int(playback_position) % 60
    total_minutes = int(total_duration) // 60
    total_seconds = int(total_duration) % 60
    timecode_text = f"{current_minutes:02d}:{current_seconds:02d} / {total_minutes:02d}:{total_seconds:02d}"
    timecode_surface = font.render(timecode_text, True, (255, 255, 255))
    timecode_rect = timecode_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
    screen.blit(timecode_surface, timecode_rect)

def draw_tracks():
    """Function to draw icon boxes for each track."""
    num_tracks = len(tracks)
    if num_tracks == 0:
        return
    box_width = 150
    box_height = 150
    padding = 20
    start_x = padding
    y = MENU_BAR_HEIGHT + 20  # Start below the menu bar
    max_font_size = 24
    min_font_size = 12
    columns = max(1, (SCREEN_WIDTH - padding * 2) // (box_width + padding))
    rows = (num_tracks + columns - 1) // columns

    for idx, track in enumerate(tracks):
        row = idx // columns
        col = idx % columns
        x = start_x + col * (box_width + padding)
        current_y = y + row * (box_height + padding)
        rect = pygame.Rect(x, current_y, box_width, box_height)
        track['rect'] = rect  # Store rect in track dict
        # Draw background
        if mute_flags[idx]:
            color = (150, 150, 150)  # Gray if muted
        else:
            color = (200, 200, 200)
        pygame.draw.rect(screen, color, rect)

        # Draw icon
        icon_image = track['icon']
        icon_rect = icon_image.get_rect(center=(x + box_width // 2, current_y + 40))
        screen.blit(icon_image, icon_rect)

        # Prepare label
        label = track['label']
        lines = label.split('\n')
        # Adjust font size to fit the text within the box
        font_size = max_font_size
        font = pygame.font.SysFont(None, font_size)
        text_surfaces = [font.render(line, True, (0, 0, 0)) for line in lines]

        # Reduce font size if text is too wide or too tall
        while True:
            # Check if any line is too wide
            too_wide = any(text.get_width() > box_width - 10 for text in text_surfaces)
            # Check if total text height is too tall
            total_text_height = sum(text.get_height() for text in text_surfaces)
            total_height = total_text_height + icon_rect.height + 20  # Include icon height
            if too_wide or total_height > box_height - 10:
                font_size -= 1
                if font_size < min_font_size:
                    break  # Cannot reduce font size further
                font = pygame.font.SysFont(None, font_size)
                text_surfaces = [font.render(line, True, (0, 0, 0)) for line in lines]
            else:
                break

        # Calculate starting y-coordinate to place the label below the icon
        label_y = icon_rect.bottom + 5
        for text in text_surfaces:
            text_rect = text.get_rect(centerx=x + box_width // 2, y=label_y)
            screen.blit(text, text_rect)
            label_y += text.get_height()

def draw_playback_slider():
    """Function to draw the playback slider at the bottom."""
    if total_duration == 0:
        return
    # Slider dimensions
    slider_width = SCREEN_WIDTH - 100
    slider_height = 20
    x = 50
    y = SCREEN_HEIGHT - 100
    # Draw slider background
    pygame.draw.rect(screen, (100, 100, 100), (x, y, slider_width, slider_height))
    # Draw playback progress
    progress = playback_position / total_duration
    progress_width = int(slider_width * progress)
    pygame.draw.rect(screen, (0, 200, 0), (x, y, progress_width, slider_height))
    # Store slider rect for interaction
    global slider_rect
    slider_rect = pygame.Rect(x, y, slider_width, slider_height)

def audio_callback(outdata, frames, time, status):
    """Callback function for sounddevice.OutputStream."""
    global playback_position, total_duration, tracks, mute_flags, stop_event, seek_event, seek_position
    if status.output_underflow:
        print('Output underflow: increase blocksize?', file=sys.stderr)
        raise sd.CallbackAbort
    if stop_event.is_set():
        raise sd.CallbackStop

    if seek_event.is_set():
        seek_event.clear()
        playback_position = seek_position

    start_sample = int(playback_position * tracks[0]['samplerate'])
    end_sample = start_sample + frames
    data = np.zeros((frames, tracks[0]['data'].shape[1]), dtype='float32')

    for i, track in enumerate(tracks):
        if not mute_flags[i]:
            track_data = track['data']
            track_samples = track_data[start_sample:end_sample]
            if track_samples.shape[0] < frames:
                # Pad with zeros if track is shorter
                padding = np.zeros((frames - track_samples.shape[0], track_samples.shape[1]))
                track_samples = np.vstack((track_samples, padding))
            data += track_samples

    # Normalize mixed data to prevent clipping
    max_amp = np.max(np.abs(data))
    if max_amp > 1.0:
        data /= max_amp

    outdata[:] = data

    playback_position += frames / tracks[0]['samplerate']
    if playback_position >= total_duration:
        raise sd.CallbackStop

def play_audio():
    """Function to play audio using sounddevice."""
    global tracks, playing, playback_position, stop_event, seek_event, seek_position
    samplerate = tracks[0]['samplerate']
    blocksize = 1024
    with sd.OutputStream(channels=tracks[0]['data'].shape[1],
                         samplerate=samplerate,
                         blocksize=blocksize,
                         callback=audio_callback):
        while not stop_event.is_set():
            time.sleep(0.1)

    playing = False

running = True
last_update_time = time.time()

while running:
    current_time = time.time()
    delta_time = current_time - last_update_time
    last_update_time = current_time

    for event in pygame.event.get():
        if event.type == QUIT:
            stop_event.set()
            if audio_thread and audio_thread.is_alive():
                audio_thread.join()
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                stop_event.set()
                if audio_thread and audio_thread.is_alive():
                    audio_thread.join()
                running = False
            elif event.key == K_l:
                stop_event.set()
                if audio_thread and audio_thread.is_alive():
                    audio_thread.join()
                load_sound_files()
            elif event.key == K_SPACE:
                if not playing and total_duration > 0:
                    # Play all tracks
                    stop_event.clear()
                    audio_thread = threading.Thread(target=play_audio)
                    audio_thread.start()
                    playing = True
                else:
                    # Stop all tracks
                    stop_event.set()
                    if audio_thread and audio_thread.is_alive():
                        audio_thread.join()
                    playing = False
        elif event.type == MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if 'load_button_rect_global' in globals() and load_button_rect_global.collidepoint(pos):
                # Load tracks
                stop_event.set()
                if audio_thread and audio_thread.is_alive():
                    audio_thread.join()
                load_sound_files()
            elif 'play_button_rect_global' in globals() and play_button_rect_global.collidepoint(pos):
                # Play/Pause toggle
                if not playing and total_duration > 0:
                    # Play all tracks
                    stop_event.clear()
                    audio_thread = threading.Thread(target=play_audio)
                    audio_thread.start()
                    playing = True
                else:
                    # Stop all tracks
                    stop_event.set()
                    if audio_thread and audio_thread.is_alive():
                        audio_thread.join()
                    playing = False
            elif 'slider_rect' in globals() and slider_rect.collidepoint(pos):
                # Calculate new playback position
                x = pos[0] - slider_rect.x
                ratio = x / slider_rect.width
                seek_position = total_duration * ratio
                seek_event.set()
                playback_position = seek_position
            else:
                for i, track in enumerate(tracks):
                    if 'rect' in track and track['rect'].collidepoint(pos):
                        # Toggle mute
                        mute_flags[i] = not mute_flags[i]

    if playing:
        playback_position += delta_time
        if playback_position >= total_duration:
            playback_position = total_duration
            playing = False

    screen.fill((50, 50, 50))
    draw_menu_bar()
    draw_tracks()
    draw_play_pause_button()
    draw_playback_slider()
    draw_timecode()
    pygame.display.flip()

pygame.quit()
sys.exit()
