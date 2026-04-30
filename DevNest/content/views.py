from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

# Create your views here.

def content_view(request: HttpRequest):
    return render(request, 'content/content.html')