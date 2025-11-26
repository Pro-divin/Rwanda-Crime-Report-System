from django.urls import path
from . import views

urlpatterns = [
    # Blockchain anchor endpoints
    path('anchor/<str:report_id>/', views.BlockchainAnchorStatusView.as_view(), name='anchor_status'),
    path('verify/<str:report_id>/', views.VerifyEvidenceView.as_view(), name='verify_evidence'),
    path('status/<str:report_id>/', views.BlockchainTransactionStatusView.as_view(), name='tx_status'),
]