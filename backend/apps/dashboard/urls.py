from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('reports/', views.reports_list, name='reports_list'),
    path('reports/<uuid:report_id>/', views.report_detail, name='report_detail'),
    path('reports/<uuid:report_id>/verify/', views.verify_integrity, name='verify_integrity_report'),
    path('reports/<uuid:report_id>/update-status/', views.update_report_status, name='update_report_status'),
    path('reports/api/all/', views.reports_api_all, name='reports_api_all'),
    path('analytics/', views.analytics, name='analytics'),
    path('verify-integrity/', views.integrity_verification_dashboard, name='verify_integrity'),
    path('map/', views.map_view, name='map_view'),
]