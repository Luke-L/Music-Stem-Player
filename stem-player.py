import pygame
import sys
import os
from pygame.locals import *
from tkinter import Tk
from tkinter import filedialog

# v0.1

# Initialize Pygame and the mixer
pygame.init()
pygame.mixer.init()

# Set up the screen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Music Stem Player and Visualizer")

# List to hold the tracks
tracks = []

def load_sound_files():
    """Function to load sound files using a file dialog."""
    root = Tk()
    root.withdraw()  # Hide the root window
    file_paths = filedialog.askopenfilenames(filetypes=[("Audio Files", "*.wav")])
    root.destroy()
    for file_path in file_paths:
        try:
            sound = pygame.mixer.Sound(file_path)
            label = os.path.basename(file_path)
            tracks.append({'sound': sound, 'label': label, 'icon': None, 'muted': False})
        except pygame.error as e:
            print(f"Could not load sound file {file_path}: {e}")

def draw_tracks():
    """Function to draw icon boxes for each track."""
    num_tracks = len(tracks)
    if num_tracks == 0:
        return
    box_width = 100
    box_height = 100
    padding = 20
    total_width = num_tracks * (box_width + padding) - padding
    start_x = (SCREEN_WIDTH - total_width) // 2
    y = (SCREEN_HEIGHT - box_height) // 2

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
        # Draw label
        text = font.render(track['label'], True, (0, 0, 0))
        text_rect = text.get_rect(center=(x + box_width // 2, y + box_height + 15))
        screen.blit(text, text_rect)

running = True
playing = False

while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
            elif event.key == K_l:
                load_sound_files()
            elif event.key == K_SPACE:
                if not playing:
                    # Play all tracks
                    for track in tracks:
                        track['sound'].play(-1)  # Loop indefinitely
                    playing = True
                else:
                    # Stop all tracks
                    for track in tracks:
                        track['sound'].stop()
                    playing = False
        elif event.type == MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            for track in tracks:
                if 'rect' in track and track['rect'].collidepoint(pos):
                    # Toggle mute
                    if track.get('muted', False):
                        # Unmute
                        track['sound'].set_volume(1.0)
                        track['muted'] = False
                    else:
                        # Mute
                        track['sound'].set_volume(0.0)
                        track['muted'] = True

    screen.fill((50, 50, 50))
    draw_tracks()
    pygame.display.flip()

pygame.quit()
sys.exit()
