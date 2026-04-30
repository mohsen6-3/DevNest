from django.urls import path
from . import views

app_name = "content"
urlpatterns = [
    path('', views.content_view, name='content_view'),
]