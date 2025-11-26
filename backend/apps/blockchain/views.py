"""
Blockchain API Views for Rwanda Report System
Handles blockchain anchoring, verification, and status tracking
"""

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from apps.reports.models import Report
from .models import BlockchainAnchor
from .cardano_utils import CardanoEvidenceAnchoring, BlockchainStatusTracker
import json


class BlockchainAnchorStatusView(APIView):
    """Check blockchain anchoring status for a report"""
    
    def get(self, request, report_id):
        """Get anchoring status"""
        try:
            anchor = get_object_or_404(BlockchainAnchor, report_id=report_id)
            
            return Response({
                "success": True,
                "report_id": report_id,
                "status": anchor.status,
                "evidence_hash": anchor.evidence_hash,
                "transaction_hash": anchor.transaction_hash,
                "ipfs_cid": anchor.ipfs_cid,
                "confirmations": anchor.confirmations,
                "network": anchor.network,
                "created_at": anchor.created_at.isoformat(),
                "confirmed_at": anchor.confirmed_at.isoformat() if anchor.confirmed_at else None,
            }, status=http_status.HTTP_200_OK)
        
        except BlockchainAnchor.DoesNotExist:
            return Response({
                "success": False,
                "error": f"No blockchain anchor found for {report_id}"
            }, status=http_status.HTTP_404_NOT_FOUND)


class VerifyEvidenceView(APIView):
    """Verify evidence hash on blockchain"""
    
    def post(self, request, report_id):
        """Verify evidence against blockchain record"""
        try:
            report = get_object_or_404(Report, reference_code=report_id)
            anchor = get_object_or_404(BlockchainAnchor, report_id=report_id)
            
            # Verify the evidence hash matches
            evidence_match = anchor.evidence_hash == report.evidence_hash
            
            return Response({
                "success": True,
                "report_id": report_id,
                "evidence_verified": evidence_match,
                "expected_hash": report.evidence_hash,
                "blockchain_hash": anchor.evidence_hash,
                "blockchain_status": anchor.status,
                "confirmations": anchor.confirmations,
                "verification_timestamp": json.dumps({
                    "verified_at": str(anchor.confirmed_at or anchor.created_at),
                    "network": anchor.network,
                })
            }, status=http_status.HTTP_200_OK)
        
        except (Report.DoesNotExist, BlockchainAnchor.DoesNotExist) as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=http_status.HTTP_404_NOT_FOUND)


class BlockchainTransactionStatusView(APIView):
    """Get detailed transaction status"""
    
    def get(self, request, report_id):
        """Get transaction details"""
        try:
            anchor = get_object_or_404(BlockchainAnchor, report_id=report_id)
            tracker = BlockchainStatusTracker()
            
            status_info = tracker.get_report_blockchain_status(
                report_id=report_id,
                tx_hash=anchor.transaction_hash
            )
            
            return Response({
                "success": True,
                "report_id": report_id,
                "blockchain_status": status_info,
                "details": {
                    "status": anchor.get_status_display(),
                    "evidence_hash": anchor.evidence_hash,
                    "ipfs_cid": anchor.ipfs_cid,
                    "confirmations": anchor.confirmations,
                    "block_number": anchor.block_number,
                    "created_at": anchor.created_at.isoformat(),
                    "updated_at": anchor.updated_at.isoformat(),
                }
            }, status=http_status.HTTP_200_OK)
        
        except BlockchainAnchor.DoesNotExist:
            return Response({
                "success": False,
                "error": f"No blockchain transaction found for {report_id}"
            }, status=http_status.HTTP_404_NOT_FOUND)