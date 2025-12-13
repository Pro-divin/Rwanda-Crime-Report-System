from django.urls import path
from django.views.generic import RedirectView
from . import views
from .legal_views import (
    TermsConditionsView, PrivacyPolicyView,
    LegalDisclaimerView, UserConsentView
)

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('home/', RedirectView.as_view(pattern_name='homepage', permanent=True), name='home_redirect'),
    path('report/submit/', views.submit_report, name='submit_report'),
    path('report/status/', views.report_status_lookup, name='report_status_main'),
    path('report/status/<str:reference_code>/', views.report_status, name='report_status'),
    path('report/certificate/<str:reference_code>/', views.verification_certificate, name='view_verification_certificate'),
    path('report/verify/<str:reference_code>/', views.verify_report_integrity, name='verify_report_integrity'),
    path('report/list/', views.report_list, name='report_list'),
    path('api/report/submit/', views.AsyncReportSubmitAPI.as_view(), name='api_submit_report'),
    path('api/report/status/<str:reference_code>/', views.ReportStatusAPI.as_view(), name='api_report_status'),
    path('api/reports/list/', views.ReportListAPI.as_view(), name='api_reports_list'),
    path('api/ipfs/upload/', views.AsyncIPFSUploadAPI.as_view(), name='api_ipfs_upload'),
    path('legal/terms/', TermsConditionsView.as_view(), name='legal_terms'),
    path('legal/privacy/', PrivacyPolicyView.as_view(), name='legal_privacy'),
    path('legal/disclaimer/', LegalDisclaimerView.as_view(), name='legal_disclaimer'),
    path('legal/consent/', UserConsentView.as_view(), name='legal_consent'),
]
