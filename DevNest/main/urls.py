from django.urls import path
from . import views

app_name = "main"
urlpatterns = [
    path('',                    views.home_view,           name='home_view'),
    path('contact/',            views.contact_us_view,     name='contact_us'),
    path('report/',             views.report_view,         name='report'),
    path('staff/messages/',     views.staff_messages_view, name='staff_messages'),
    path('staff/reports/',      views.staff_reports_view,  name='staff_reports'),
]
