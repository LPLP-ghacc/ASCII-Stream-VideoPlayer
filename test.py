import cv2
import numpy as np
import pygame
from moviepy.editor import VideoFileClip
import os
import time
import tempfile
import random
import wave
import pyaudio
import threading

ASCII_CHARS = "░@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/|()1{}[]?-_+~<>i!lI;:,^`'. "
ASCII_CHARS = ASCII_CHARS[::-1]  # Invert for better visual result

MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
    'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
    'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....',
    '6': '-....', '7': '--...', '8': '---..', '9': '----.', '0': '-----'
}

COLORS = {'#': (245, 5, 183)}

def text_to_morse(text):
    text = text.upper()
    morse_text = ' '.join([MORSE_CODE_DICT.get(char, char) for char in text])
    return morse_text

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

def get_video_files(directory):
    video_extensions = ['mp4', 'avi', 'mov', 'mkv']
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.split('.')[-1] in video_extensions]
    return files

def matrix_effect(screen, ascii_image_lines, char_width, char_height):
    for i, line in enumerate(ascii_image_lines):
        for j, char in enumerate(line):
            if random.random() < 0.1:
                y_offset = min(len(ascii_image_lines) - 1, i + 1)
                ascii_image_lines[y_offset] = ascii_image_lines[y_offset][:j] + char + ascii_image_lines[y_offset][j + 1:]
                ascii_image_lines[i] = ascii_image_lines[i][:j] + ' ' + ascii_image_lines[i][j + 1:]

def play_audio(audio_path):
    p = pyaudio.PyAudio()

    try:
        wf = wave.open(audio_path, 'rb')
    except FileNotFoundError:
        print(f"Audio file not found: {audio_path}")
        return
    except wave.Error as e:
        print(f"Error opening audio file: {e}")
        return

    virtual_device_index = None
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if "CABLE Input" in device_info.get('name'):
            virtual_device_index = i
            break

    if virtual_device_index is None:
        print("Virtual audio device not found.")
        return

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    output_device_index=virtual_device_index)

    data = wf.readframes(1024)
    while len(data) > 0:
        stream.write(data)
        data = wf.readframes(1024)

    stream.stop_stream()
    stream.close()
    p.terminate()

pygame.init()
screen_width = 1024
screen_height = 768
screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME)
pygame.display.set_caption('ASCII Video Renderer')
font = pygame.font.SysFont('Courier', 12)

video_directory = 'stream'
if not os.path.exists(video_directory):
    os.makedirs(video_directory)

current_video_index = 0
video_files = get_video_files(video_directory)
paused = False
started = False

def play_video():
    global current_video_index, video_files, started, paused, running, video_fps, video_duration, start_time
    global screen_width, screen_height, screen

    video_path = video_files[current_video_index]
    cap = cv2.VideoCapture(video_path)

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    video_duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / video_fps

    video_clip = VideoFileClip(video_path)
    audio = video_clip.audio

    video_title = os.path.basename(video_path)
    video_title_morse = text_to_morse(video_title)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file: 
        audio_path = temp_audio_file.name
        audio.write_audiofile(audio_path, codec='pcm_s16le')  

    if not os.path.exists(audio_path):
        print(f"Failed to create audio file: {audio_path}")
        return

    audio_thread = threading.Thread(target=play_audio, args=(audio_path,))
    audio_thread.start()

    clock = pygame.time.Clock()

    start_time = time.time()
    running = True
    started = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.VIDEORESIZE:
                screen_width, screen_height = event.w, event.h
                screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_RIGHT:
                    current_video_index = (current_video_index + 1) % len(video_files)
                    running = False
                elif event.key == pygame.K_LEFT:
                    current_video_index = (current_video_index - 1) % len(video_files)
                    running = False

        elapsed_time = time.time() - start_time

        if not paused:
            ret, frame = cap.read()
            if not ret:
                break

            frame = grayscale(frame)

            char_width, char_height = font.size('P')

            new_width = screen_width // char_width
            new_height = screen_height // char_height - 2

            frame = resize(frame, new_width=new_width, new_height=new_height)

            ascii_image = to_ascii(frame)
            ascii_image_lines = render_ascii(ascii_image, new_width)

            screen.fill((0, 0, 0))

            title_surface = font.render(video_title_morse, True, (245, 5, 183))
            screen.blit(title_surface, (0, 0))

            for i, line in enumerate(ascii_image_lines):
                for j, char in enumerate(line):
                    color = COLORS.get(char, (255, 255, 255))
                    text_surface = font.render(char, True, color)
                    screen.blit(text_surface, (j * char_width, (i + 1) * char_height))

            progress = min(int((elapsed_time / video_duration) * new_width), new_width)
            progress_line = '-' * progress + ' ' * (new_width - progress)
            progress_surface = font.render(progress_line, True, (245, 5, 183))
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
                    screen.blit(text_surface, (j * char_width, (i + 1) * char_height))

            pygame.display.flip()

        if not paused and elapsed_time >= video_duration:
            running = False

        clock.tick(video_fps)

    cap.release()
    time.sleep(1)
    started = False

while True:
    if not video_files:
        print("No video files found. Waiting for files...")
        while not video_files:
            time.sleep(5)
            video_files = get_video_files(video_directory)

    play_video()
    current_video_index = (current_video_index + 1) % len(video_files)
    video_files = get_video_files(video_directory)

pygame.quit()
