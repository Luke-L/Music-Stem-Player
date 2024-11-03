import pygame
import sys
import os
from pygame.locals import *
from tkinter import Tk
from tkinter import filedialog
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio
import threading
import time

# v0.2
# added track label and playback slider

# Initialize Pygame
pygame.init()

# Set up the screen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Music Stem Player and Visualizer")

# List to hold the tracks
tracks = []
total_duration = 0  # Total duration of the longest track
playback_position = 0  # Current playback position in milliseconds
playing = False
play_threads = []
stop_event = threading.Event()

def load_sound_files():
    """Function to load sound files using a file dialog."""
    global total_duration, playback_position, playing
    root = Tk()
    root.withdraw()  # Hide the root window
    file_paths = filedialog.askopenfilenames(filetypes=[("Audio Files", "*.wav *.mp3")])
    root.destroy()
    for file_path in file_paths:
        try:
            sound = AudioSegment.from_file(file_path)
            label = os.path.basename(file_path)
            tracks.append({'sound': sound, 'label': label, 'icon': None, 'muted': False})
            if len(sound) > total_duration:
                total_duration = len(sound)
        except Exception as e:
            print(f"Could not load sound file {file_path}: {e}")
    playback_position = 0  # Reset playback position
    playing = False

def draw_tracks():
    """Function to draw icon boxes for each track."""
    num_tracks = len(tracks)
    if num_tracks == 0:
        return
    box_width = 150
    box_height = 150
    padding = 20
    total_width = num_tracks * (box_width + padding) - padding
    start_x = (SCREEN_WIDTH - total_width) // 2
    y = (SCREEN_HEIGHT - box_height) // 2 - 50

    font = pygame.font.SysFont(None, 24)

    for i, track in enumerate(tracks):
        x = start_x + i * (box_width + padding)
        rect = pygame.Rect(x, y, box_width, box_height)
        track['rect'] = rect  # Store rect in track dict
        # Draw background
        if track.get('muted', False):
            color = (150, 150, 150)  # Gray if muted
        else:
            color = (200, 200, 200)
        pygame.draw.rect(screen, color, rect)
        # Draw label inside the box
        text = font.render(track['label'], True, (0, 0, 0))
        text_rect = text.get_rect(center=(x + box_width // 2, y + box_height // 2))
        screen.blit(text, text_rect)

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

def play_tracks():
    """Function to play all tracks from the current playback position."""
    global play_threads, stop_event
    stop_event.clear()
    play_threads = []
    for track in tracks:
        if not track.get('muted', False):
            # Slice the sound from the current position
            sliced_sound = track['sound'][playback_position:]
            # Play the sliced sound in a separate thread
            thread = threading.Thread(target=_play_with_simpleaudio, args=(sliced_sound,))
            thread.start()
            play_threads.append(thread)

def stop_tracks():
    """Function to stop all tracks."""
    global stop_event
    stop_event.set()
    # simpleaudio automatically stops when the program exits
    # Since we can't stop individual playbacks easily, we rely on stop_event

running = True
last_update_time = time.time()

while running:
    current_time = time.time()
    delta_time = current_time - last_update_time
    last_update_time = current_time

    for event in pygame.event.get():
        if event.type == QUIT:
            stop_event.set()
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                stop_event.set()
                running = False
            elif event.key == K_l:
                stop_event.set()
                tracks.clear()
                load_sound_files()
            elif event.key == K_SPACE:
                if not playing and total_duration > 0:
                    # Play all tracks
                    play_tracks()
                    playing = True
                else:
                    # Stop all tracks
                    stop_tracks()
                    playing = False
        elif event.type == MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if 'slider_rect' in globals() and slider_rect.collidepoint(pos):
                # Calculate new playback position
                x = pos[0] - slider_rect.x
                ratio = x / slider_rect.width
                playback_position = int(total_duration * ratio)
                if playing:
                    stop_tracks()
                    play_tracks()
            else:
                for track in tracks:
                    if 'rect' in track and track['rect'].collidepoint(pos):
                        # Toggle mute
                        track['muted'] = not track.get('muted', False)
                        if playing:
                            stop_tracks()
                            play_tracks()

    if playing:
        playback_position += delta_time * 1000  # Convert to milliseconds
        if playback_position >= total_duration:
            playback_position = total_duration
            playing = False

    screen.fill((50, 50, 50))
    draw_tracks()
    draw_playback_slider()
    pygame.display.flip()

pygame.quit()
sys.exit()
