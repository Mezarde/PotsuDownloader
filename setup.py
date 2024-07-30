from cx_Freeze import setup, Executable
import os


icon_path = os.path.abspath('icon.ico')

executables = [
    Executable('potsuyt.py', base='Win32GUI', icon=icon_path)
]

setup(
    name='YouTube Downloader',
    version='1.0',
    description='YouTube Downloader Application',
    executables=executables
)
