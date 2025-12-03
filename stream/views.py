from django.shortcuts import render

def arpi_stream(request):
    return render(request, "stream/arpi.html", {})

def phone_stream(request):
    return render(request, "stream/phone.html", {})