from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from stream.models import CatDetection
from django.views.decorators.http import require_http_methods
from django.http import FileResponse
import os


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
    cds = [ x.frame_file for x in CatDetection.objects.all() ]
    return render(request, "dash/catdetections.html", {'kepek': cds})

@login_required
def dash_streams(request):
    cds = [ x.frame_file for x in CatDetection.objects.all() ]
    return render(request, "dash/streams.html", {'kepek': cds})

def arpi_stream(request):
    return render(request, "stream/arpi.html", {})

def phone_stream(request):
    return render(request, "stream/phone.html", {})