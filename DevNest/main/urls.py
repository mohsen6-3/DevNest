from django.urls import path
from . import views

app_name = "main"
urlpatterns = [
    path('',                    views.home_view,           name='home_view'),
    path('contact/',            views.contact_us_view,     name='contact_us'),
    path('report/',             views.report_view,         name='report'),
    path('notifications/read/<int:notification_id>/', views.read_notification_view, name='read_notification'),
    path('notifications/read-all/', views.read_all_notifications_view, name='read_all_notifications'),
    path('staff/messages/',     views.staff_messages_view, name='staff_messages'),
    path('staff/reports/',      views.staff_reports_view,  name='staff_reports'),
]
