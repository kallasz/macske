#!/usr/bin/python3

"""
Record H264 video to file while optionally streaming MJPEG to browser
Based on picamera2 examples
"""

import io
import logging
import socketserver
from http import server
from threading import Condition
from datetime import datetime

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, MJPEGEncoder
from picamera2.outputs import FileOutput

# Configuration
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
VIDEO_FPS = 30

PAGE = f"""
<html>
<head>
<title>Recording Camera Stream</title>
</head>
<body>
<h1>Camera Recording (Preview)</h1>
<img src="stream.mjpg" width="{VIDEO_WIDTH}" height="{VIDEO_HEIGHT}" />
<p>Recording to video file...</p>
</body>
</html>
"""

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

# Initialize camera
picam2 = Picamera2()

# Configure for both main stream (H264) and lores stream (MJPEG for preview)
video_config = picam2.create_video_configuration(
    main={"size": (VIDEO_WIDTH, VIDEO_HEIGHT), "format": "RGB888"},
    lores={"size": (VIDEO_WIDTH, VIDEO_HEIGHT), "format": "YUV420"},
    controls={"FrameRate": VIDEO_FPS}
)
picam2.configure(video_config)

# Setup H264 encoder for file recording
h264_encoder = H264Encoder(bitrate=10000000)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
h264_output = FileOutput(f"recording_{timestamp}.h264")

# Setup MJPEG encoder for web streaming (from lores stream)
mjpeg_encoder = MJPEGEncoder()
output = StreamingOutput()

# Start recording to file
picam2.start_recording(h264_encoder, h264_output)
print(f"Recording to: recording_{timestamp}.h264")

# Start MJPEG stream for preview (separate encoder on lores stream)
picam2.start_encoder(mjpeg_encoder, FileOutput(output), name="lores")

# Start web server
try:
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    print("Server started at http://0.0.0.0:8000")
    print("Press Ctrl+C to stop recording")
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    picam2.stop_recording()
    picam2.stop_encoder()
    print(f"\nRecording saved to: recording_{timestamp}.h264")
    print("\nTo convert to MP4, run:")
    print(f"ffmpeg -i recording_{timestamp}.h264 -c:v copy recording_{timestamp}.mp4")