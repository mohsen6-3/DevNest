from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from .models import Post
# Create your views here.
def post_create_view(request: HttpRequest):

    if request.method == 'POST':
        title = request.POST.get('title')
        detail = request.POST.get('detail')
        posts = Post(title=title, detail=detail)
        posts.save()
    
    return render(request, 'posts/posts_page.html')

def post_list_view(request: HttpRequest):
    posts = Post.objects.all()
    return render(request, 'posts/posts_page.html', {'posts': posts})
