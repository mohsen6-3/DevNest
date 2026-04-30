from django.urls import path
from . import views
app_name = "posts"
urlpatterns = [
    path('',views.post_create_view, name='post_create_view'),
    
]