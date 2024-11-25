import pygame
import sys
import os
from pygame.locals import *
from tkinter import Tk
from tkinter import filedialog, messagebox
import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import json

# v1.3
# Adjusted icon_location to use the root/icons/ directory relative to the script.

# Initialize Pygame
pygame.init()

# Set up the screen
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
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

# Common artist and track name
artist_track_name = ""

# Settings
settings_menu_open = False
show_title = True
show_full_labels = False  # Set to False by default as per your requirement
use_title_case_labels = True

# Load track type configurations from JSON file
script_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(script_dir, "track_types.json")
with open(config_file, "r") as f:
    config_data = json.load(f)

track_types = config_data["track_types"]
default_icon_filename = config_data.get("default_icon", "music-notes.png")
default_color = config_data.get("default_color", [150, 150, 150])

# Adjust the icon_location to point to your icons directory relative to the script directory
icon_location = os.path.join(script_dir, "icons")

# UI Elements
MENU_BAR_HEIGHT = 40
PLAY_BUTTON_SIZE = 50

# Dictionary to hold UI element rectangles for interaction
ui_elements = {}

# Load play and pause button images or create simple shapes
play_button_image = pygame.Surface((PLAY_BUTTON_SIZE, PLAY_BUTTON_SIZE), pygame.SRCALPHA)
pygame.draw.polygon(play_button_image, (0, 255, 0), [(15, 10), (15, 40), (40, 25)])

pause_button_image = pygame.Surface((PLAY_BUTTON_SIZE, PLAY_BUTTON_SIZE), pygame.SRCALPHA)
pygame.draw.rect(pause_button_image, (255, 0, 0), (15, 10, 10, 30))
pygame.draw.rect(pause_button_image, (255, 0, 0), (30, 10, 10, 30))

# State variables for solo mode
rmb_pressed = False
prev_mute_flags = []
soloed_track_idx = None

# State variables for volume adjustment
adjusting_volume = False
volume_adjust_track_idx = None
initial_mouse_y = None
click_detected = False

def get_track_type(filename):
    """Determine the track type based on keywords in the filename."""
    filename_lower = filename.lower()
    for track_type in track_types:
        for keyword in track_type["keywords"]:
            if keyword.lower() in filename_lower:
                return track_type
    # If no match found, return default
    return {
        "type": "default",
        "icon": default_icon_filename,
        "color": default_color
    }

def find_common_words(filenames):
    """Find the common words in the list of filenames, preserving order."""
    if not filenames:
        return []
    # Extract base names without extensions
    bases = [os.path.splitext(os.path.basename(f))[0] for f in filenames]
    # Replace hyphens and underscores with spaces
    bases = [b.replace('-', ' ').replace('_', ' ') for b in bases]
    # Split into words
    split_names = [b.split() for b in bases]
    # Convert all words to lowercase for comparison
    split_names_lower = [[word.lower() for word in words] for words in split_names]
    # Use the first filename's words as the basis for order
    first_words = split_names_lower[0]
    # Initialize common words list
    common_words = []
    for idx, word in enumerate(first_words):
        if all(word in other_words for other_words in split_names_lower[1:]):
            # Use the original word from the first filename to preserve case
            common_words.append(split_names[0][idx])
    return common_words

def load_sound_files():
    """Function to load sound files using a file dialog."""
    global total_duration, playback_position, playing, tracks, mute_flags, stop_event, audio_thread, artist_track_name
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

    # Find common words among filenames
    common_words = find_common_words(file_paths)
    artist_track_name_words = common_words
    artist_track_name = ' '.join(artist_track_name_words)

    for file_path in file_paths:
        try:
            # Read audio file
            data, samplerate = sf.read(file_path, dtype='float32')
            if len(data.shape) == 1:
                data = np.expand_dims(data, axis=1)  # Convert mono to stereo
            duration = len(data) / samplerate

            # Get labels
            full_label = os.path.splitext(os.path.basename(file_path))[0]
            # Replace hyphens and underscores with spaces
            full_label_processed = full_label.replace('-', ' ').replace('_', ' ')
            # Split into words
            words = full_label_processed.split()
            # Remove common words (case-insensitive)
            label_words = [word for word in words if word.lower() not in [w.lower() for w in artist_track_name_words]]
            label_without_common = ' '.join(label_words)
            if not label_without_common.strip():
                label_without_common = 'Track'

            # Get track type information from JSON config
            track_type_info = get_track_type(label_without_common)
            track_type = track_type_info["type"]
            icon_filename = track_type_info["icon"]
            color = track_type_info["color"]

            # Load icon image
            icon_path = os.path.join(icon_location, icon_filename)
            icon_image = pygame.image.load(icon_path).convert_alpha()
            # Scale icon to fit in the box
            icon_size = (64, 64)
            icon_image = pygame.transform.smoothscale(icon_image, icon_size)

            tracks.append({
                'data': data,
                'samplerate': samplerate,
                'full_label': full_label,
                'label_without_common': label_without_common,
                'type': track_type,
                'icon': icon_image,
                'volume': 1.0,  # Initialize volume at 100%
                'color': color  # Store color from JSON
            })
            mute_flags.append(False)  # Initially, all tracks are unmuted
            if duration > max_duration:
                max_duration = duration
        except Exception as e:
            print(f"Could not load sound file {file_path}: {e}")
    total_duration = max_duration
    playback_position = 0  # Reset playback position
    playing = False

def draw_artist_track_name():
    """Function to draw the artist and track name above the track buttons."""
    if artist_track_name and show_title:
        # Prepare the display text
        display_text = artist_track_name
        if use_title_case_labels:
            display_text = display_text.replace('-', ' ').replace('_', ' ').title()
        else:
            display_text = display_text.replace('-', ' ').replace('_', ' ')
        font = pygame.font.SysFont(None, 36)
        text_surface = font.render(display_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, MENU_BAR_HEIGHT + 30))
        screen.blit(text_surface, text_rect)

def draw_menu_bar():
    """Function to draw the top menu bar."""
    # Draw menu bar background
    pygame.draw.rect(screen, (70, 70, 70), (0, 0, SCREEN_WIDTH, MENU_BAR_HEIGHT))
    # Draw "Load Tracks" button
    font = pygame.font.SysFont(None, 24)
    button_padding = 10

    # Load Tracks Button
    load_text = font.render("Load Tracks", True, (255, 255, 255))
    load_text_width, load_text_height = load_text.get_size()
    load_button_rect = pygame.Rect(10, 5, load_text_width + button_padding * 2, load_text_height + button_padding)
    pygame.draw.rect(screen, (100, 100, 100), load_button_rect)
    screen.blit(load_text, (load_button_rect.x + button_padding, load_button_rect.y + button_padding // 2))

    # Settings Button
    settings_text = font.render("Settings", True, (255, 255, 255))
    settings_text_width, settings_text_height = settings_text.get_size()
    # Position settings button next to load tracks button
    settings_button_x = load_button_rect.right + 10  # 10 pixels gap
    settings_button_rect = pygame.Rect(settings_button_x, 5, settings_text_width + button_padding * 2, load_text_height + button_padding)
    pygame.draw.rect(screen, (100, 100, 100), settings_button_rect)
    screen.blit(settings_text, (settings_button_rect.x + button_padding, settings_button_rect.y + button_padding // 2))

    # Store button rects for interaction
    ui_elements['load_button_rect'] = load_button_rect
    ui_elements['settings_button_rect'] = settings_button_rect

def draw_settings_menu():
    """Function to draw the settings menu."""
    menu_width = 300
    menu_height = 200
    x = (SCREEN_WIDTH - menu_width) // 2
    y = (SCREEN_HEIGHT - menu_height) // 2
    # Draw menu background
    pygame.draw.rect(screen, (60, 60, 60), (x, y, menu_width, menu_height))
    pygame.draw.rect(screen, (255, 255, 255), (x, y, menu_width, menu_height), 2)  # Border

    font = pygame.font.SysFont(None, 24)

    # Option 1: Toggle Title Visibility
    title_text = "Show Title"
    title_label = font.render(title_text, True, (255, 255, 255))
    title_checkbox_rect = pygame.Rect(x + 20, y + 30, 20, 20)
    pygame.draw.rect(screen, (255, 255, 255), title_checkbox_rect, 2)
    if show_title:
        pygame.draw.rect(screen, (255, 255, 255), title_checkbox_rect.inflate(-4, -4))
    screen.blit(title_label, (title_checkbox_rect.right + 10, title_checkbox_rect.y))

    # Option 2: Toggle Full Track Labels
    full_label_text = "Show Full Track Labels"
    full_label_label = font.render(full_label_text, True, (255, 255, 255))
    full_label_checkbox_rect = pygame.Rect(x + 20, y + 70, 20, 20)
    pygame.draw.rect(screen, (255, 255, 255), full_label_checkbox_rect, 2)
    if show_full_labels:
        pygame.draw.rect(screen, (255, 255, 255), full_label_checkbox_rect.inflate(-4, -4))
    screen.blit(full_label_label, (full_label_checkbox_rect.right + 10, full_label_checkbox_rect.y))

    # Option 3: Show Raw or Title Case Labels
    label_case_text = "Use Title Case Labels"
    label_case_label = font.render(label_case_text, True, (255, 255, 255))
    label_case_checkbox_rect = pygame.Rect(x + 20, y + 110, 20, 20)
    pygame.draw.rect(screen, (255, 255, 255), label_case_checkbox_rect, 2)
    if use_title_case_labels:
        pygame.draw.rect(screen, (255, 255, 255), label_case_checkbox_rect.inflate(-4, -4))
    screen.blit(label_case_label, (label_case_checkbox_rect.right + 10, label_case_checkbox_rect.y))

    # Store checkbox rects for interaction
    ui_elements['title_checkbox_rect'] = title_checkbox_rect
    ui_elements['full_label_checkbox_rect'] = full_label_checkbox_rect
    ui_elements['label_case_checkbox_rect'] = label_case_checkbox_rect

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
    ui_elements['play_button_rect'] = play_button_rect

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

def recolor_icon(icon_image, color):
    """Recolor the icon image to the specified color, keeping the alpha channel."""
    # Ensure the icon has per-pixel alpha
    icon_image = icon_image.convert_alpha()

    # Create a copy of the icon image
    tinted_icon = icon_image.copy()

    # Clear the RGB channels by multiplying by zero (makes the image black)
    tinted_icon.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGB_MULT)

    # Add the desired color to the image
    tinted_icon.fill(color + [0], special_flags=pygame.BLEND_RGB_ADD)

    return tinted_icon

def draw_tracks():
    """Function to draw icon boxes for each track."""
    num_tracks = len(tracks)
    if num_tracks == 0:
        return

    box_width = 150
    box_height = 150
    padding = 20
    start_x = padding
    # Adjust y_offset based on whether the title is shown
    y_offset = MENU_BAR_HEIGHT + 70 if show_title else MENU_BAR_HEIGHT + 20  # Start below the menu bar and artist name
    max_font_size = 24
    min_font_size = 12
    columns = max(1, (SCREEN_WIDTH - padding * 2) // (box_width + padding))
    rows = (num_tracks + columns - 1) // columns

    for idx, track in enumerate(tracks):
        row = idx // columns
        col = idx % columns
        x = start_x + col * (box_width + padding)
        current_y = y_offset + row * (box_height + padding)
        rect = pygame.Rect(x, current_y, box_width, box_height)
        track['rect'] = rect  # Store rect in track dict

        # Get color from track data
        color = track['color']
        if mute_flags[idx]:
            color = [max(0, c - 50) for c in color]  # Darken color if muted

        # Draw background
        pygame.draw.rect(screen, color, rect)

        # If this track is soloed, draw a thick white outline
        if rmb_pressed and idx == soloed_track_idx:
            pygame.draw.rect(screen, (255, 255, 255), rect, 7)  # 7 pixels thick

        # Draw icon
        icon_image = track['icon']
        icon_rect = icon_image.get_rect(center=(x + box_width // 2, current_y + 40))

        # Tint the icon based on whether the track is active or inactive
        if not mute_flags[idx]:
            # Active track: recolor the icon to white
            tinted_icon = recolor_icon(icon_image, [255, 255, 255])
        else:
            # Inactive track: recolor the icon to black
            tinted_icon = recolor_icon(icon_image, [0, 0, 0])

        screen.blit(tinted_icon, icon_rect)

        # Select label based on settings
        label = track['full_label'] if show_full_labels else track['label_without_common']
        label = (label.replace('-', ' ').replace('_', ' ').title() if use_title_case_labels
                 else label.replace('-', ' ').replace('_', ' '))

        # Determine text color based on whether the track is active or inactive
        text_color = (255, 255, 255) if not mute_flags[idx] else (0, 0, 0)

        # Wrap text to fit within the box width
        font_size = max_font_size
        font = pygame.font.SysFont(None, font_size)
        words = label.split()
        lines = []
        current_line = ''
        for word in words:
            test_line = f"{current_line} {word}".strip()
            test_surface = font.render(test_line, True, text_color)
            if test_surface.get_width() <= box_width - 10:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        # Adjust font size if text is too tall
        while True:
            font = pygame.font.SysFont(None, font_size)
            text_surfaces = [font.render(line, True, text_color) for line in lines]
            total_text_height = sum(text.get_height() for text in text_surfaces)
            total_height = total_text_height + icon_rect.height + 20  # Include icon height
            if total_height > box_height - 10 and font_size > min_font_size:
                font_size -= 1
            else:
                break

        # Re-render text surfaces with the adjusted font size
        font = pygame.font.SysFont(None, font_size)
        text_surfaces = [font.render(line, True, text_color) for line in lines]

        # Calculate starting y-coordinate to place the label below the icon
        label_y = icon_rect.bottom + 5
        for text in text_surfaces:
            text_rect = text.get_rect(centerx=x + box_width // 2, y=label_y)
            screen.blit(text, text_rect)
            label_y += text.get_height()

        # Draw volume overlay
        volume = track['volume']
        overlay_height = box_height * (1 - volume)
        if overlay_height > 0:
            overlay = pygame.Surface((box_width, overlay_height), pygame.SRCALPHA)
            overlay.fill((128, 128, 128, 128))  # Gray with 50% opacity
            overlay_y = current_y  # Start from the top
            screen.blit(overlay, (x, overlay_y))


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
    ui_elements['slider_rect'] = pygame.Rect(x, y, slider_width, slider_height)

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
            # Apply volume control
            track_samples = track_samples * track['volume']
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
    global tracks, playing
    samplerate = tracks[0]['samplerate']
    blocksize = 1024
    with sd.OutputStream(channels=tracks[0]['data'].shape[1],
                         samplerate=samplerate,
                         blocksize=blocksize,
                         callback=audio_callback):
        while not stop_event.is_set():
            threading.Event().wait(0.1)

    playing = False

running = True

while running:
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
            elif event.key == K_q:
                # Prompt user to confirm exit
                root = Tk()
                root.withdraw()  # Hide the root window
                result = messagebox.askyesno("Exit", "Are you sure you want to exit?")
                root.destroy()
                if result:
                    stop_event.set()
                    if audio_thread and audio_thread.is_alive():
                        audio_thread.join()
                    running = False
        elif event.type == MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if event.button == 1:  # Left mouse button
                if ui_elements.get('load_button_rect') and ui_elements['load_button_rect'].collidepoint(pos):
                    # Load tracks
                    stop_event.set()
                    if audio_thread and audio_thread.is_alive():
                        audio_thread.join()
                    load_sound_files()
                elif ui_elements.get('settings_button_rect') and ui_elements['settings_button_rect'].collidepoint(pos):
                    # Toggle settings menu
                    settings_menu_open = not settings_menu_open
                elif ui_elements.get('play_button_rect') and ui_elements['play_button_rect'].collidepoint(pos):
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
                elif ui_elements.get('slider_rect') and ui_elements['slider_rect'].collidepoint(pos):
                    # Calculate new playback position
                    x = pos[0] - ui_elements['slider_rect'].x
                    ratio = x / ui_elements['slider_rect'].width
                    seek_position = total_duration * ratio
                    seek_event.set()
                    playback_position = seek_position
                elif settings_menu_open:
                    # Handle clicks inside the settings menu
                    if ui_elements.get('title_checkbox_rect') and ui_elements['title_checkbox_rect'].collidepoint(pos):
                        show_title = not show_title
                    elif ui_elements.get('full_label_checkbox_rect') and ui_elements['full_label_checkbox_rect'].collidepoint(pos):
                        show_full_labels = not show_full_labels
                    elif ui_elements.get('label_case_checkbox_rect') and ui_elements['label_case_checkbox_rect'].collidepoint(pos):
                        use_title_case_labels = not use_title_case_labels
                else:
                    # Only interact with tracks if not in solo mode
                    if not rmb_pressed:
                        for i, track in enumerate(tracks):
                            if 'rect' in track and track['rect'].collidepoint(pos):
                                # Start adjusting volume
                                adjusting_volume = True
                                volume_adjust_track_idx = i
                                initial_mouse_y = pos[1]
                                click_detected = True
                                break
            elif event.button == 3:  # Right mouse button
                # Check if mouse is over a track
                pos = pygame.mouse.get_pos()
                track_hovered = None
                for idx, track in enumerate(tracks):
                    if 'rect' in track and track['rect'].collidepoint(pos):
                        track_hovered = idx
                        break
                if track_hovered is not None:
                    rmb_pressed = True
                    prev_mute_flags = mute_flags.copy()
                    soloed_track_idx = track_hovered
                    # Mute all tracks except the soloed one
                    mute_flags = [True] * len(tracks)
                    mute_flags[soloed_track_idx] = False
                else:
                    # Do not enter solo mode if not over a track
                    rmb_pressed = False
        elif event.type == MOUSEBUTTONUP:
            if event.button == 1:  # Left mouse button
                if adjusting_volume:
                    if click_detected:
                        # Toggle mute if click detected
                        mute_flags[volume_adjust_track_idx] = not mute_flags[volume_adjust_track_idx]
                    adjusting_volume = False
                    volume_adjust_track_idx = None
                    initial_mouse_y = None
                    click_detected = False
            elif event.button == 3:  # Right mouse button
                rmb_pressed = False
                mute_flags = prev_mute_flags.copy()
                soloed_track_idx = None
        elif event.type == MOUSEMOTION:
            if adjusting_volume:
                current_mouse_y = event.pos[1]
                delta_y = initial_mouse_y - current_mouse_y  # Inverted to make up positive
                # If mouse has moved more than a threshold, consider it a drag
                if abs(delta_y) > 5:
                    click_detected = False
                # Update volume based on delta_y
                sensitivity = 0.005  # Adjust sensitivity as needed
                volume_change = delta_y * sensitivity  # Now positive when moving up
                new_volume = tracks[volume_adjust_track_idx]['volume'] + volume_change
                # Clamp volume between 0.0 and 1.0
                new_volume = max(0.0, min(1.0, new_volume))
                tracks[volume_adjust_track_idx]['volume'] = new_volume
                # Update initial_mouse_y to current position for smooth adjustment
                initial_mouse_y = current_mouse_y
            elif pygame.mouse.get_pressed()[2]:  # Right mouse button is held down
                rmb_pressed = True
                pos = pygame.mouse.get_pos()
                track_hovered = None
                for idx, track in enumerate(tracks):
                    if 'rect' in track and track['rect'].collidepoint(pos):
                        track_hovered = idx
                        break
                if track_hovered is not None:
                    if soloed_track_idx != track_hovered:
                        soloed_track_idx = track_hovered
                        # Mute all tracks except the soloed one
                        mute_flags = [True] * len(tracks)
                        mute_flags[soloed_track_idx] = False
                else:
                    soloed_track_idx = None
                    # Mute all tracks if not hovering over any
                    mute_flags = [True] * len(tracks)
            else:
                if rmb_pressed:
                    # Right mouse button released outside of MOUSEBUTTONUP event
                    rmb_pressed = False
                    mute_flags = prev_mute_flags.copy()
                    soloed_track_idx = None

    screen.fill((50, 50, 50))
    draw_menu_bar()
    if show_title:
        draw_artist_track_name()
    draw_tracks()
    draw_play_pause_button()
    draw_playback_slider()
    draw_timecode()
    if settings_menu_open:
        draw_settings_menu()
    pygame.display.flip()

pygame.quit()
sys.exit()
