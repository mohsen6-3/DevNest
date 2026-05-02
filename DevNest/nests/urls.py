from django.urls import path

from posts import views as post_views

from . import views


app_name = 'nests'

urlpatterns = [
    path('',                      views.nest_dashboard,         name='nest_dashboard'),
    path('browse/',               views.nest_list_view,         name='nest_list_view'),
    path('browse/',               views.nest_list_view,         name='nest_list'),
    path('request/',              views.request_nest_view,      name='request_nest_view'),
    path('staff/review/',         views.staff_nest_review_view, name='staff_nest_review'),
    path('<int:nest_id>/',        views.nest_detail_view,       name='nest_detail'),
    path('<int:nest_id>/posts/',  post_views.nest_posts_view,   name='nest_posts'),
    path('<int:nest_id>/posts/<int:post_id>/',                          post_views.nest_post_detail_view, name='nest_post_detail'),
    path('<int:nest_id>/posts/<int:post_id>/comment/',                  post_views.add_comment_view,      name='nest_add_comment'),
    path('<int:nest_id>/posts/<int:post_id>/comment/<int:comment_id>/verify/', post_views.verify_comment_view, name='nest_verify_comment'),
    path('<int:nest_id>/join/',   views.join_nest_view,         name='join_nest'),
    path('<int:nest_id>/manage/', views.manage_nest_view,       name='manage_nest'),
]