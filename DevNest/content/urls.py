from django.urls import path
from . import views

app_name = "content"

urlpatterns = [
    # Title  (specific paths BEFORE parametric to avoid conflict)
    path("", views.all_titles_view, name="all_titles_view"),
    path("title/create/", views.create_title_view, name="create_title_view"),
    path("title/<title_id>/", views.title_detail_view, name="title_detail_view"),
    path("title/update/<title_id>/", views.update_title_view, name="update_title_view"),
    path("title/delete/<title_id>/", views.delete_title_view, name="delete_title_view"),

    # Unit  (specific paths BEFORE parametric)
    path("unit/create/<title_id>/", views.create_unit_view, name="create_unit_view"),
    path("unit/<unit_id>/", views.unit_detail_view, name="unit_detail_view"),
    path("unit/update/<unit_id>/", views.update_unit_view, name="update_unit_view"),
    path("unit/delete/<unit_id>/", views.delete_unit_view, name="delete_unit_view"),

    # Topic  (specific paths BEFORE parametric)
    path("topic/create/<unit_id>/", views.create_topic_view, name="create_topic_view"),
    path("topic/<topic_id>/", views.topic_detail_view, name="topic_detail_view"),
    path("topic/update/<topic_id>/", views.update_topic_view, name="update_topic_view"),
    path("topic/delete/<topic_id>/", views.delete_topic_view, name="delete_topic_view"),

    # Video
    path("video/add/<topic_id>/", views.add_video_view, name="add_video_view"),
    path("video/delete/<video_id>/", views.delete_video_view, name="delete_video_view"),

    # File
    path("file/add/<topic_id>/", views.add_file_view, name="add_file_view"),
    path("file/delete/<file_id>/", views.delete_file_view, name="delete_file_view"),
    path("file/download/<file_id>/", views.download_file_view, name="download_file_view"),

    # Image
    path("image/add/<topic_id>/", views.add_image_view, name="add_image_view"),
    path("image/delete/<image_id>/", views.delete_image_view, name="delete_image_view"),

    # Text
    path("text/add/<topic_id>/", views.add_text_view, name="add_text_view"),
    path("text/delete/<text_id>/", views.delete_text_view, name="delete_text_view"),

    # Link
    path("link/add/<topic_id>/", views.add_link_view, name="add_link_view"),
    path("link/delete/<link_id>/", views.delete_link_view, name="delete_link_view"),
]