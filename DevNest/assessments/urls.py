from django.urls import path
from . import views
app_name = "assessments"
urlpatterns = [
    path('', views.assessment_page_view, name='assessment_page_view'),
    path('create/', views.assessment_create_view, name='assessment_create_view'),
    path('update/<int:pk>/', views.assessment_update_view, name='assessment_update_view'),
    path('delete/<int:pk>/', views.assessment_delete_view, name='assessment_delete_view'),
]