# ASCII Video Renderer

ASCII Video Renderer is a Python application that renders videos in ASCII format and plays them in a separate window. The application supports dynamic loading of video files from a folder, playback of soundtracks, and pause and resume functionality.

## Features

- Real-time rendering of videos in ASCII format.
- Support for various video files (mp4, avi, mov, mkv).
- Playback of soundtracks from videos.
- Dynamic loading of new video files during runtime.
- Pause and resume button (`SPACE`).
- Automatic transition to the next video upon completion of the current one.
- Video looping.

## Requirements

1. Python 3.x
2. Libraries:
    - opencv-python
    - numpy
    - pygame
    - moviepy

You can install the required libraries using the following command:

```bash
pip install opencv-python numpy pygame moviepy
```
## Project Structure
-	app.py: The main script for running the program.
-	stream/: Folder containing the videos to be rendered.
## Usage
1.	Add your video files to the stream folder.
2.	Run the application.
3.	The program will automatically play all video files in the stream folder on repeat.
4.	To pause and resume playback, press the SPACE key.
5.	To exit the application, press ESC.
## Examples
https://youtu.be/3pCoqJDkelQ
## License
This project is licensed under the MIT License. See the LICENSE file for more details.
