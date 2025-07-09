"""Minimal OpenGL visualizer for audio amplitude from a PulseAudio pipe."""

import os
import sys
import pygame
from pygame.locals import OPENGL, FULLSCREEN, DOUBLEBUF, QUIT, KEYDOWN, K_ESCAPE
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np

VERT_SRC = """
#version 120
attribute vec2 position;
varying vec2 v_texcoord;
void main() {
    v_texcoord = position * 0.5 + 0.5;
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

FRAG_SRC = """
#version 120
uniform float amplitude;
varying vec2 v_texcoord;
void main() {
    vec3 color = vec3(v_texcoord, 0.5) * amplitude;
    gl_FragColor = vec4(color, 1.0);
}
"""

# Number of 16-bit stereo frames to read from the pipe on each iteration
CHUNK = 1024

def open_pipe(path):
    """Return a non-blocking file object for the FIFO at *path*."""
    # Open the FIFO in non-blocking mode so reads don't stall the loop
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    return os.fdopen(fd, 'rb', buffering=0)

def read_amplitude(pipe):
    """Read a chunk of audio and return its RMS amplitude (0..1)."""
    try:
        # Each frame has two 16-bit samples (stereo)
        data = pipe.read(CHUNK * 4)
    except BlockingIOError:
        return 0.0
    if not data:
        return 0.0

    # Convert bytes to floating point samples
    samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
    if samples.size == 0:
        return 0.0

    # Mix stereo down to mono and compute root mean square
    mono = samples.reshape(-1, 2).mean(axis=1)
    rms = np.sqrt(np.mean(mono ** 2))
    return float(rms / 32768.0)

def main(pipe_path):
    """Initialize the window and run the render loop."""

    pygame.init()
    info = pygame.display.Info()
    width, height = info.current_w, info.current_h

    # Create a fullscreen OpenGL context
    pygame.display.set_mode((width, height), OPENGL | DOUBLEBUF | FULLSCREEN)

    # Compile the vertex and fragment shaders
    program = compileProgram(
        compileShader(VERT_SRC, GL_VERTEX_SHADER),
        compileShader(FRAG_SRC, GL_FRAGMENT_SHADER)
    )

    # Look up shader variable locations
    pos_loc = glGetAttribLocation(program, 'position')
    amp_loc = glGetUniformLocation(program, 'amplitude')

    # Vertex positions for a fullscreen quad
    vertices = np.array([
        -1.0, -1.0,
         1.0, -1.0,
         1.0,  1.0,
        -1.0,  1.0,
    ], dtype=np.float32)

    # Upload vertex data to the GPU
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    # Open the audio pipe and set up a frame timer
    pipe = open_pipe(pipe_path)
    clock = pygame.time.Clock()

    amplitude = 0.0
    running = True
    while running:
        # Handle window close or Esc key
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False

        # Read the latest audio level
        amplitude = read_amplitude(pipe)

        # Draw a quad tinted by the current amplitude
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(program)
        glUniform1f(amp_loc, amplitude)
        glEnableVertexAttribArray(pos_loc)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glVertexAttribPointer(pos_loc, 2, GL_FLOAT, False, 0, None)
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
        glDisableVertexAttribArray(pos_loc)

        pygame.display.flip()
        clock.tick(60)  # Aim for 60 FPS

    pygame.quit()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python3 visualizer.py <pipe_path>')
        sys.exit(1)

    # Path to the PulseAudio pipe-sink FIFO
    main(sys.argv[1])
