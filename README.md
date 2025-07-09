# Vizualizer

This repository provides a minimal Python demo showing how to:

1. Open a fullscreen window using PyGame and PyOpenGL.
2. Read audio samples from a PulseAudio pipe (for example, fed by `snapclient`).
3. Display a simple shader visualization that reacts to the audio level.

The demo is meant for devices like the Raspberry Pi Zero running Linux.

## Requirements

- Python 3.11+
- `pip` for installing Python packages
- An active PulseAudio stream that you can route to a named pipe

Install the Python dependencies:

```bash
pip install pygame PyOpenGL numpy
```

## Usage

1. **Create a pipe** for audio data (only once):
   ```bash
   mkfifo /tmp/audio_pipe
   ```

2. **Send audio to the pipe** by using PulseAudio's `module-pipe-sink`.
   Load the module and route your audio source (for example, `snapclient`) to
   the new *Pipe sink*:
   ```bash
   pactl load-module module-pipe-sink \
       file=/tmp/audio_pipe format=s16le rate=44100 channels=2
   ```
   Use `pavucontrol` or another mixer to select "Pipe sink" as the output for
   your application. If you want to hear the audio as well, combine this sink
   with your normal output using `module-combine-sink` or a similar approach.

3. **Run the visualizer**:
   ```bash
   python3 visualizer.py /tmp/audio_pipe
   ```

Press <kbd>Esc</kbd> to exit the demo window.

## Notes

This is a minimal example intended only as a starting point. The shader uses the
average audio level to tint the screen. You can extend it by computing an FFT in
`visualizer.py` and passing the spectrum to more complex shaders.
