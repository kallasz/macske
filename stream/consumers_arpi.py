import asyncio
import json
from datetime import datetime
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput
from django.core.files.base import ContentFile
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async as database_sync_to_async
from stream.models import Chunk, VideoStream
import io
import threading
from stream.ffmpeg import frames_to_webm_buffer


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


_recording_state = None
_recording_lock = asyncio.Lock()

class ArpiStreamConsumer(AsyncWebsocketConsumer):
    # Class-level shared recording state
    stream_group_name = 'camera_stream'
    
    async def connect(self):

        # Join the camera stream group
        await self.channel_layer.group_add(
            self.stream_group_name,
            self.channel_name
        )
        await self.accept()
        
        # If recording is active, notify client
        async with _recording_lock:
            global _recording_state
            if _recording_state is not None:
                await self.send(text_data=json.dumps({
                    "status": "recording_active",
                    "message": "Recording already in progress"
                }))
        
    async def disconnect(self, code):
        # Leave the camera stream group
        await self.channel_layer.group_discard(
            self.stream_group_name,
            self.channel_name
        )
        print(f"Client disconnected, but recording continues...")

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            data = json.loads(text_data)
            print(data)
            
            if data["_meta_action"] == "START":
                async with _recording_lock:
                    global _recording_state
                    if _recording_state is not None:
                        await self.send(text_data=json.dumps({
                            "error": "Recording already in progress"
                        }))
                        return
                    
                    # Initialize shared recording state
                    _recording_state = {
                        'chunk_frame_limit': 900,
                        'current_chunk_number': 0,
                        'queue': asyncio.Queue(),
                        'frames': [],
                        'signal_to_stop': 0,
                        'picam2': Picamera2(),
                        'fullres_output': StreamingOutput(),
                        'lores_output': StreamingOutput(),
                        'fullres_encoder': MJPEGEncoder(),
                        'lores_encoder': MJPEGEncoder(),
                    }
                    
                    state = _recording_state
                    
                    # Configure camera
                    picam2_config = state['picam2'].create_video_configuration(
                        main={"size": (1920, 1080), "format": "RGB888"},
                        lores={"size": (640, 480), "format": "YUV420"},
                        controls={"FrameRate": 30}
                    )
                    state['picam2'].configure(picam2_config)
                    
                    # Create video stream record
                    state['vs'] = await database_sync_to_async(VideoStream.objects.create)(source=0)
                    
                    # Start recording
                    state['picam2'].start_recording(
                        state['fullres_encoder'], 
                        FileOutput(state['fullres_output'])
                    )
                    
                    state['picam2'].start_encoder(
                        state['lores_encoder'], 
                        FileOutput(state['lores_output']),
                        name="lores"
                    )
                    
                    # Start worker tasks
                    state['worker_task'] = asyncio.create_task(self._worker_save_chunk())
                    state['camera_task'] = asyncio.create_task(self._use_camera())
                    
                    print(f'Started recording: {state["vs"].started.strftime("%Y_%m_%d_%H_%M_%S")}')
                
            elif data["_meta_action"] == "STOP":
                async with _recording_lock:
                    if _recording_state is None:
                        await self.send(text_data=json.dumps({
                            "error": "No recording in progress"
                        }))
                        return
                    
                    state = _recording_state
                    state['signal_to_stop'] = 1
                    await asyncio.sleep(0.5)
                    
                    # Stop encoders
                    try:
                        state['picam2'].stop_recording()
                        state['picam2'].stop_encoder()
                        state['picam2'].close()
                    except:
                        pass
                    
                    # Save remaining frames
                    if len(state['frames']) > 0:
                        await state['queue'].put((state['frames'].copy(), state['current_chunk_number']))
                    
                    await state['queue'].put((None, None))
                    await state['worker_task']
                    
                    # Update database
                    state['vs'].stopped = datetime.now()
                    await database_sync_to_async(state['vs'].save)()
                    
                    print(f"Recording stopped: {state['vs'].id}")
                    _recording_state = None

    async def _use_camera(self):
        """Collect full-res frames and stream low-res to websocket"""
        state = _recording_state
        if not state:
            return
            
        while True:
            if state['signal_to_stop'] == 1:
                break
                
            # Check if we need to save a chunk
            if len(state['frames']) >= state['chunk_frame_limit']:
                await state['queue'].put((state['frames'].copy(), state['current_chunk_number']))
                state['current_chunk_number'] += 1
                state['frames'] = []
            
            # Collect full resolution frame for recording
            with state['fullres_output'].condition:
                state['fullres_output'].condition.wait()
                fullres_frame = state['fullres_output'].frame
                if fullres_frame:
                    state['frames'].append(fullres_frame)
            
            # Broadcast low resolution frame to all connected clients
            try:
                with state['lores_output'].condition:
                    state['lores_output'].condition.wait()
                    lores_frame = state['lores_output'].frame
                    if lores_frame:
                        # Send to all clients in the group
                        await self.channel_layer.group_send(
                            self.stream_group_name,
                            {
                                'type': 'stream_frame',
                                'frame': lores_frame
                            }
                        )
            except Exception as e:
                print(f"Error broadcasting frame: {e}")
            
            await asyncio.sleep(0.033)  # ~30fps
    
    async def stream_frame(self, event):
        """Handler for receiving frames from group_send"""
        try:
            await self.send(bytes_data=event['frame'])
        except:
            # Client disconnected
            pass

    async def _worker_save_chunk(self):
        """Convert frames to WebM and save to database"""
        state = _recording_state
        if not state:
            return
            
        while True:
            frames, current_chunk_number = await state['queue'].get()

            if frames is None:
                break

            print(f"Converting chunk {current_chunk_number} with {len(frames)} frames...")
            
            try:
                buffer = await asyncio.to_thread(
                    frames_to_webm_buffer, 
                    frames, 
                    framerate=30,
                    width=1920,
                    height=1080
                )
                
                chunk = await database_sync_to_async(Chunk.objects.create)(
                    video_stream=state['vs'], 
                    chunk_number=current_chunk_number
                )
                await database_sync_to_async(chunk.video_file.save)(
                    f'CHUNK_{current_chunk_number:04d}.webm', 
                    ContentFile(buffer.getvalue()), 
                    save=True
                )
                
                print(f"Saved chunk {current_chunk_number}")
                
            except Exception as e:
                print(f"Error saving chunk {current_chunk_number}: {e}")