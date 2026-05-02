from django.urls import path
from . import views
app_name = "assessments"
urlpatterns = [
    # path('', views.assessment_page_view, name='assessment_page_view'),
    # path('create/', views.assessment_create_view, name='assessment_create_view'),
    # path('update/<int:pk>/', views.assessment_update_view, name='assessment_update_view'),
    # path('delete/<int:pk>/', views.assessment_delete_view, name='assessment_delete_view'),
    # path('questions/update/<int:pk>/', views.question_update_view, name='question_update_view'),
    # path('<int:pk>/questions/create/', views.question_create_view, name='question_create_view'),
    # path('questions/delete/<int:pk>/', views.question_delete_view, name='question_delete_view'),
    # path('<int:pk>/', views.assessment_detail_view, name='assessment_detail_view'),
    # path("question/<int:question_id>/choices/create/", views.choice_create_view, name="choice_create_view"),
    # path("assessment/<int:pk>/take/", views.take_assessment_view, name="take_assessment_view"),
    # path("submission/<int:submission_id>/result/", views.submission_result_view, name="submission_result_view"),
    # path("choice/<int:choice_id>/update/", views.choice_update_view, name="choice_update_view"),
    path('nests/<int:nest_id>/', views.assessment_page_view, name='assessment_page_view'),
    path('nests/<int:nest_id>/create/', views.assessment_create_view, name='assessment_create_view'),
    path('nests/<int:nest_id>/update/<int:pk>/', views.assessment_update_view, name='assessment_update_view'),
    path('nests/<int:nest_id>/delete/<int:pk>/', views.assessment_delete_view, name='assessment_delete_view'),

    path('nests/<int:nest_id>/<int:pk>/', views.assessment_detail_view, name='assessment_detail_view'),

    path('nests/<int:nest_id>/<int:pk>/questions/create/', views.question_create_view, name='question_create_view'),
    path('nests/<int:nest_id>/questions/update/<int:pk>/', views.question_update_view, name='question_update_view'),
    path('nests/<int:nest_id>/questions/delete/<int:pk>/', views.question_delete_view, name='question_delete_view'),

    path('nests/<int:nest_id>/question/<int:question_id>/choices/create/', views.choice_create_view, name="choice_create_view"),
    path('nests/<int:nest_id>/choice/<int:choice_id>/update/', views.choice_update_view, name="choice_update_view"),
    path('nests/<int:nest_id>/choice/<int:choice_id>/delete/', views.choice_delete_view, name="choice_delete_view"),

    path('nests/<int:nest_id>/assessment/<int:pk>/take/', views.take_assessment_view, name="take_assessment_view"),
    path('nests/<int:nest_id>/submission/<int:submission_id>/result/', views.submission_result_view, name="submission_result_view"),
]

