from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from stream.models import CatDetection, VideoStream, Chunk
from django.views.decorators.http import require_http_methods
from django.http import FileResponse
import os
import random


def index(request):
    return render(request, "index.html", {})

@login_required
def stream(request):
    return render(request, "stream.html", {})

@login_required
def dash(request):
    return render(request, "dash/index.html", {})

@login_required
def dash_cat_detections(request):
    cds = [ x for x in CatDetection.objects.all() ]
    cds.reverse()
    return render(request, "dash/catdetections.html", {'kepek': cds})

@login_required
def dash_cat_detection(request, id):
    cd = CatDetection.objects.get(id=id)
    return render(request, "dash/catdetection.html", {'cd': cd})

@login_required
def dash_streams(request):
    streams = [ {'stream': x, 'chunks': Chunk.objects.filter(video_stream=x).all()} for x in VideoStream.objects.all() ]
    streams.reverse()
    return render(request, "dash/streams.html", {'streamek': streams})

@login_required
def dash_stream(request, id):
    stream = VideoStream.objects.get(id=id)
    chunks = Chunk.objects.filter(video_stream=stream).all()
    print(stream)
    return render(request, "dash/stream.html", {'stream': stream, 'chunks': chunks})

@login_required
def dash_stream_chunk(request, sid, cid):
    stream = VideoStream.objects.get(id=sid)
    chunk = Chunk.objects.filter(video_stream=stream, chunk_number=cid).first()
    return render(request, "dash/chunk.html", {'stream': stream, 'chunk': chunk})

def arpi_stream(request):
    return render(request, "stream/arpi.html", {})

def phone_stream(request):
    return render(request, "stream/phone.html", {})

@login_required
def randomcat(request):
    ri = random.randint(0, CatDetection.objects.all().__len__() - 1)
    cd = CatDetection.objects.get(id=ri)
    return render(request, "dash/catdetection.html", {'cd': cd})