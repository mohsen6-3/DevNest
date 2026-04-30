from django.urls import path
from . import views


app_name = "nests"

urlpatterns = [
    path("", views.nest_dashboard, name="nest_dashboard"),
    path("add/", views.add_nest_view, name="add_nest_view"),
]