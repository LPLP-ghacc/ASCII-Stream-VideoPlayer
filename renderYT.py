import cv2
import numpy as np
import pygame
from moviepy.editor import *
from pytube import YouTube
import os
import time
import tempfile
import random

ASCII_CHARS = "░@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/|()1{}[]?-_+~<>i!lI;:,^`'. "
ASCII_CHARS = ASCII_CHARS[::-1]  # Invert for better visual result

COLORS = {
    '#': (245, 5, 183),
}

def grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def resize(image, new_width, new_height):
    return cv2.resize(image, (new_width, new_height))

def to_ascii(image):
    pixels = image.flatten()
    num_chars = len(ASCII_CHARS)
    scale = 256 // num_chars if num_chars else 1
    ascii_str = "".join([ASCII_CHARS[min(pixel // scale, num_chars - 1)] for pixel in pixels])
    return ascii_str

def render_ascii(ascii_image, width):
    return [ascii_image[i:i + width] for i in range(0, len(ascii_image), width)]

# Загрузка видео с YouTube:
def download_video_from_youtube(youtube_url):
    yt = YouTube(youtube_url)
    stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
    video_path = stream.download()
    return video_path

def matrix_effect(screen, ascii_image_lines, char_width, char_height):
    for i, line in enumerate(ascii_image_lines):
        for j, char in enumerate(line):
            if random.random() < 0.1:  # Add randomness for dripping effect
                y_offset = min(len(ascii_image_lines) - 1, i + 1)
                ascii_image_lines[y_offset] = ascii_image_lines[y_offset][:j] + char + ascii_image_lines[y_offset][j + 1:]
                ascii_image_lines[i] = ascii_image_lines[i][:j] + ' ' + ascii_image_lines[i][j + 1:]

# Инициализация Pygame
pygame.init()
screen_width = 1920
screen_height = 1080
screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME)
pygame.display.set_caption('ASCII Video Renderer')
font = pygame.font.SysFont('Courier', 12)

youtube_url = "https://youtu.be/coRWtkRpNhw"  # Замените на ссылку на ваше видео

# Скачивание видео
video_path = download_video_from_youtube(youtube_url)

paused = False
started = False

def play_video(video_path):
    global started, paused, running, audio_path, video_fps, video_duration, start_time
    global screen_width, screen_height, screen

    cap = cv2.VideoCapture(video_path)

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    video_duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / video_fps

    video_clip = VideoFileClip(video_path)
    audio = video_clip.audio

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
        audio_path = temp_audio_file.name
        audio.write_audiofile(audio_path)

    pygame.mixer.init()
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.play()

    clock = pygame.time.Clock()

    start_time = time.time()
    running = True
    started = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.mixer.music.stop()
                time.sleep(1)
                pygame.quit()
                exit()
            elif event.type == pygame.VIDEORESIZE:
                screen_width, screen_height = event.w, event.h
                screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop()
                    time.sleep(1)
                    os.remove(audio_path)
                    pygame.quit()
                    exit()
                elif event.key == pygame.K_SPACE:
                    if paused:
                        pygame.mixer.music.unpause()
                        start_time = time.time() - pauses_duration
                    else:
                        pygame.mixer.music.pause()
                        pauses_duration = time.time() - start_time
                    paused = not paused

        elapsed_time = time.time() - start_time

        if not paused:
            ret, frame = cap.read()
            if not ret:
                break

            frame = grayscale(frame)

            char_width, char_height = font.size('P')

            new_width = screen_width // char_width
            new_height = screen_height // char_height - 1  # Оставляем место для прогресс-бара

            frame = resize(frame, new_width=new_width, new_height=new_height)

            ascii_image = to_ascii(frame)
            ascii_image_lines = render_ascii(ascii_image, new_width)

            screen.fill((0, 0, 0))

            for i, line in enumerate(ascii_image_lines):
                for j, char in enumerate(line):
                    color = COLORS.get(char, (255, 255, 255))
                    text_surface = font.render(char, True, color)
                    screen.blit(text_surface, (j * char_width, i * char_height))

            # Рендер прогресс-бара снизу
            progress = min(int((elapsed_time / video_duration) * new_width), new_width)
            progress_line = '*' * progress + ' ' * (new_width - progress)
            progress_surface = font.render(progress_line, True, (6, 66, 66))
            screen.blit(progress_surface, (0, screen_height - char_height))

            pygame.display.flip()
        else:
            # Apply matrix effect while paused
            matrix_effect(screen, ascii_image_lines, char_width, char_height)
            screen.fill((0, 0, 0))
            for i, line in enumerate(ascii_image_lines):
                for j, char in enumerate(line):
                    color = COLORS.get(char, (255, 255, 255))
                    text_surface = font.render(char, True, color)
                    screen.blit(text_surface, (j * char_width, i * char_height))
            
            pygame.display.flip()

        if not paused and elapsed_time >= video_duration:
            running = False

        clock.tick(video_fps)

    cap.release()
    pygame.mixer.music.stop()
    time.sleep(1) 
    try:
        os.remove(audio_path)  
    except PermissionError:
        pass 
    started = False

play_video(video_path)

pygame.quit()