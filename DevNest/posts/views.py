from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
# Create your views here.
def post_list_view(request: HttpRequest):
    
    return render(request, 'posts/Q&A_Form.html')
