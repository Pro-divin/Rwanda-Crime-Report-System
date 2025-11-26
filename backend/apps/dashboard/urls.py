from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('reports/', views.reports_list, name='reports_list'),
    path('reports/<uuid:report_id>/', views.report_detail, name='report_detail'),
    path('analytics/', views.analytics, name='analytics'),
    path('map/', views.map_view, name='map_view'),
]