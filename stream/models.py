from django.db import models
import os
from django.db.models.signals import pre_delete

from django.dispatch import receiver

import re

# Create your models here.
class VideoStream(models.Model):
    started = models.DateTimeField(auto_now=True)
    stopped = models.DateTimeField(null=True)
    class SOURCE_CHOICES(models.IntegerChoices):
        SOURCE_ARPI = 0
        SOURCE_PHONE = 1
    source = models.IntegerField(choices=SOURCE_CHOICES)
    

def video_upload_path(instance, filename):
    return f'streams/{instance.video_stream.started.strftime("%Y_%m_%d_%H_%M_%S")}/{filename}'


class Chunk(models.Model):
    video_stream = models.ForeignKey(VideoStream, on_delete=models.CASCADE, related_name='chunks')
    video_file = models.FileField(upload_to=video_upload_path)
    chunk_number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def meta_fps_dur(self):
        pass

@receiver(pre_delete, sender=Chunk)
def delete_chunk_file(sender, **kwargs):
    if kwargs['instance'].video_file:
        if os.path.isfile(kwargs['instance'].video_file.path):
            print(kwargs['instance'].video_file.path)
            os.remove(kwargs['instance'].video_file.path)
            try:
                print(re.search(r'(.*\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})', kwargs['instance'].video_file.path).group(0))
                os.rmdir(re.search(r'(.*\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})', kwargs['instance'].video_file.path).group(0))
            except Exception as e:
                print('Tried deleting directory too, not empty...')

def frame_upload_path(instance, filename):
    return f'cats/{instance.video_stream.started.strftime("%Y_%m_%d_%H_%M_%S")}/{filename}'
    
class CatDetection(models.Model):
    video_stream = models.ForeignKey(VideoStream, on_delete=models.CASCADE, related_name='catdetections_on_vs', null=True)
    chunk = models.ForeignKey(Chunk, on_delete=models.CASCADE, related_name='catdetections_on_chunk', null=True)
    frame_num = models.IntegerField()
    frame_file = models.FileField(upload_to=frame_upload_path)
    created_at = models.DateTimeField(auto_now_add=True)
    