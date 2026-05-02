from django.urls import path
from . import views
from nests import views as nest_views
app_name = "posts"
urlpatterns = [
    path('', nest_views.nest_dashboard, name='nest_dashboard'),
    
]
