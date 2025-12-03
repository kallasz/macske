from channels.generic.websocket import AsyncWebsocketConsumer
import json
from datetime import datetime
import os
from stream.models import VideoStream, Chunk
from django.core.files.base import ContentFile
import asyncio
from channels.db import database_sync_to_async
import io

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput, FfmpegOutput, PyavOutput



class PhoneStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.chunk_limit_size = 50 * 1024 * 1024
        self.current_chunk_number = 0
        self.buffer = b''
        self.vs = None 
        self.queue = asyncio.Queue()
        self.worker_task = asyncio.create_task(self._worker_save_chunk())

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            data = json.loads(text_data)
            print(data)
            if data["_meta_action"] == "START":
                self.vs = await database_sync_to_async(VideoStream.objects.create)(source=1)
                print(f'Created VideoStream {self.vs.started.strftime("%Y_%m_%d_%H_%M_%S")}')
            elif data["_meta_action"] == "STOP":
                await self.stop_recording()
        
        # Video data comes as bytes
        if bytes_data:
            self.buffer += bytes_data
            
            if len(self.buffer) >= self.chunk_limit_size:
                await self.queue.put((self.buffer, self.current_chunk_number))

                self.current_chunk_number += 1
                self.buffer = b''

    async def disconnect(self, close_code):
        await self.stop_recording()
    
    async def stop_recording(self):
        if len(self.buffer) > 0:
            await self.queue.put((self.buffer, self.current_chunk_number))
        await self.queue.put((None,None))
        await self.worker_task
        if self.vs is not None:
            self.vs.stopped = datetime.now()
        await database_sync_to_async(self.vs.save)()

    async def _worker_save_chunk(self):
        while True:
            buffer, current_chunk_number = await self.queue.get()

            if buffer is None:
                break

            chunk = await database_sync_to_async(Chunk.objects.create)(video_stream=self.vs, chunk_number=current_chunk_number)
            await database_sync_to_async(chunk.video_file.save)(f'CHUNK_{current_chunk_number:04d}.webm', ContentFile(buffer), save=True)