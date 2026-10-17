## DISCLAIMER
i made this project just for fun and as a "cool" technical showcase. im not responsible for what anyone else decides to use this for.

# roblox wav player

a cool project i made for fun that lets you play custom audio directly in roblox. instead of using sound ids, it uses a python script to convert audio files (even from youtube) into a mono wav, and a clientsided module that reconstructs the sound using an fft synthesizer.

## whats in this repo
- `audioconverter.py` - the python script to convert audio into the binary data
- `WavPlayer` - the roblox module that actually synthesizes and plays the audio
- `WavExampleWithATool.rbxl` - a roblox place file with the auto-play setup and a tool so you can see how it works

## features
- plays any audio file or youtube link
- uses additive fft synthesis to draw the sound waves
- stops automatically when the data is deleted
- packs data into chunks so it bypasses roblox string limits

## requirements
- python 3.8+
- `pydub` and `yt-dlp` libraries for python
- ffmpeg installed on your system
- roblox studio

install the python libs:
```bash
pip install pydub yt-dlp
```

install ffmpeg (required for audio conversion):
- on windows (using winget):
```bash
winget install ffmpeg
```
*(note: you might need to restart your terminal/command prompt after installing ffmpeg for it to work properly)*

## how to use
1. run the python script (`converter.py`)
2. select an audio file from your computer (or paste a youtube url for example "https://www.youtube.com/watch?v=dQw4w9WgXcQ" c: )
3. click "Export as .rbxmx", name it whatever you want and then save it
4. insert that .rbxmx file into roblox studio
5. put the WavData folder inside a Part
6. if youre using the example place, just tag the Part with "AudioTarget" and the auto player will handle the rest. if youre using your own setup, you can just require the module and call `WavPlayer.Play(Part, WavDataFolder)` from a LocalScript. since it uses sound instances, it works on any part as long as it's visible to the client.

## audio disclaimer
the audio will sound a bit glitchy. this is expected since it's reconstructing the audio using hundreds of individual sound instances and an fft synthesizer instead of just playing a normal sound file, i dont think its possible to make it sound 100% crisp. but hopefully you can still recognize the song perfectly.
