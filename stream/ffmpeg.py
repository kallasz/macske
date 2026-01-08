import subprocess
import threading
import io
def frames_to_webm_buffer(frames, framerate=30, width=None, height=None):
    """Convert list of JPEG frames to WebM buffer"""
    
    print(f"Starting conversion of {len(frames)} frames...")
    
    # Auto-detect resolution from first frame if not provided
    if width is None or height is None:
        from PIL import Image
        first_frame = Image.open(io.BytesIO(frames[0]))
        width, height = first_frame.size
        print(f"Detected resolution: {width}x{height}")
    
    print(f"Output resolution: {width}x{height}")
    
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-f', 'image2pipe',
        '-codec:v', 'mjpeg',
        '-framerate', str(framerate),
        '-i', '-',
        '-c:v', 'libvpx',  # VP8
        '-b:v', '5M',  # 5 Mbps bitrate for better quality
        '-quality', 'good',  # Better quality than realtime
        '-cpu-used', '2',  # Slower but better quality (0-5, lower is better)
        '-s', f'{width}x{height}',  # Force output resolution
        '-aspect', f'{width}:{height}',  # Set aspect ratio
        '-auto-alt-ref', '1',  # Enable alternate reference frames
        '-lag-in-frames', '25',  # Look ahead frames
        '-f', 'webm',
        'pipe:1'
    ]
    
    print(f"Running: {' '.join(ffmpeg_cmd)}")
    
    process = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Read stdout in a separate thread to prevent buffer deadlock
    output_data = []
    
    def read_output():
        while True:
            chunk = process.stdout.read(4096)
            if not chunk:
                break
            output_data.append(chunk)
    
    reader_thread = threading.Thread(target=read_output)
    reader_thread.start()
    
    # Write frames to stdin
    try:
        for i, frame in enumerate(frames):
            process.stdin.write(frame)
            if i % 50 == 0:
                print(f"Wrote frame {i}/{len(frames)}")
        
        process.stdin.close()
        print("Closed stdin, waiting for output...")
        
    except BrokenPipeError:
        print("Broken pipe - FFmpeg crashed")
        process.kill()
        raise
    
    # Wait for reader thread and process
    reader_thread.join()
    stderr_data = process.stderr.read()
    process.wait()
    
    print(f"FFmpeg finished with return code: {process.returncode}")
    
    if process.returncode != 0:
        error_msg = stderr_data.decode() if stderr_data else "Unknown error"
        print(f"FFmpeg stderr: {error_msg}")
        raise Exception(f"FFmpeg error: {error_msg}")
    
    # Combine output chunks
    webm_data = b''.join(output_data)
    print(f"Output size: {len(webm_data)} bytes")
    
    buffer = io.BytesIO(webm_data)
    buffer.seek(0)
    
    return buffer

def concatenate_webm_chunks(webm_chunk_paths):
    """
    Concatenate multiple WebM files into a single buffer.
    
    Args:
        webm_chunk_paths: List of file paths (strings) to WebM files
    
    Returns:
        BytesIO buffer containing concatenated WebM
    """
    print(f"\nConcatenating {len(webm_chunk_paths)} WebM chunks...")
    
    combined_data = b''
    
    for i, file_path in enumerate(webm_chunk_paths):
        # Open the file and read its contents
        with open(file_path, 'rb') as f:
            chunk_data = f.read()
            combined_data += chunk_data
            print(f"  Added chunk {i + 1}: {len(chunk_data)} bytes")
    
    print(f"Total concatenated size: {len(combined_data)} bytes")
    
    result_buffer = io.BytesIO(combined_data)
    result_buffer.seek(0)
    return result_buffer
