from django.urls import path
from . import views

urlpatterns = [
    # Blockchain anchor endpoints
    path('anchor/<str:report_id>/', views.BlockchainAnchorStatusView.as_view(), name='anchor_status'),  # GET status / POST create
    path('verify/<str:report_id>/', views.VerifyEvidenceView.as_view(), name='verify_evidence'),
    path('status/<str:report_id>/', views.BlockchainTransactionStatusView.as_view(), name='tx_status'),
    path('confirmations/<str:tx_hash>/', views.TransactionConfirmationsView.as_view(), name='tx_confirmations'),
    
    # IPFS distributed storage endpoints
    path('ipfs/verify/<str:report_id>/', views.IPFSVerificationView.as_view(), name='ipfs_verify'),
    path('ipfs/stats/', views.IPFSStatsView.as_view(), name='ipfs_stats'),
    
    # Advanced integrity verification for admin
    # Hash search endpoint MUST come before parameterized route to match first
    path('integrity/verify/', views.HashSearchView.as_view(), name='hash_search'),
    path('integrity/verify/<str:report_id>/', views.IntegrityVerificationView.as_view(), name='integrity_verify'),
]