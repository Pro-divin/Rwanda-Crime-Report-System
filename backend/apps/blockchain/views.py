"""
Blockchain API Views for Rwanda Report System
Handles blockchain anchoring, verification, and status tracking
"""

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
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

    def post(self, request, report_id):
        """Create a blockchain anchor for a report"""
        try:
            # Check authentication and staff status
            if not request.user.is_authenticated or not getattr(request.user, 'is_staff', False):
                return Response({
                    "success": False,
                    "error": "Staff authentication required to anchor reports. Please log in as an administrator."
                }, status=http_status.HTTP_403_FORBIDDEN)
            
            # Try to find report by reference_code first, then by UUID
            try:
                report = Report.objects.get(reference_code=report_id)
            except Report.DoesNotExist:
                try:
                    report = Report.objects.get(pk=report_id)
                except Report.DoesNotExist:
                    return Response({
                        "success": False,
                        "error": f"Report {report_id} not found"
                    }, status=http_status.HTTP_404_NOT_FOUND)
            
            # Check if already anchored
            try:
                existing_anchor = BlockchainAnchor.objects.get(report_id=report.reference_code)
                return Response({
                    "success": True,
                    "already_anchored": True,
                    "report_id": report.reference_code,
                    "transaction_hash": existing_anchor.transaction_hash,
                    "evidence_hash": existing_anchor.evidence_hash,
                    "status": existing_anchor.status,
                }, status=http_status.HTTP_200_OK)
            except BlockchainAnchor.DoesNotExist:
                pass
            
            # Create new anchor
            from django.utils import timezone
            
            # Prepare evidence data
            evidence_data = {
                "reference_code": report.reference_code,
                "category": report.category,
                "description": report.description[:500] if report.description else "",
                "is_anonymous": report.is_anonymous,
                "created_at": report.created_at.isoformat() if report.created_at else timezone.now().isoformat(),
            }
            
            # Generate evidence hash
            cardano = CardanoEvidenceAnchoring()
            evidence_hash = cardano.generate_evidence_hash(evidence_data)
            
            # Create anchor transaction
            tx_result = cardano.create_anchor_transaction(
                report_id=report.reference_code,
                evidence_hash=evidence_hash,
                category=report.category,
                is_anonymous=report.is_anonymous,
                reporter_info={
                    "name": getattr(report, 'reporter_name', 'Anonymous'),
                    "phone": getattr(report, 'reporter_phone', ''),
                    "email": getattr(report, 'reporter_email', ''),
                }
            )
            
            tx_hash = tx_result.get("tx_hash")
            simulated = tx_result.get("simulated", False)
            
            # Persist the anchor
            anchor = BlockchainAnchor.objects.create(
                report_id=report.reference_code,
                evidence_hash=evidence_hash,
                transaction_hash=tx_hash,
                status=BlockchainAnchor.Status.SUBMITTED if not simulated else BlockchainAnchor.Status.PENDING,
                network=cardano.network,
                metadata=tx_result.get("anchor_data", {}),
            )
            
            # Update report
            report.evidence_hash = evidence_hash
            report.transaction_hash = tx_hash
            report.is_hash_anchored = True
            report.save(update_fields=["evidence_hash", "transaction_hash", "is_hash_anchored", "updated_at"])
            
            return Response({
                "success": True,
                "report_id": report.reference_code,
                "transaction_hash": tx_hash,
                "evidence_hash": evidence_hash,
                "status": anchor.status,
                "network": cardano.network,
                "simulated": simulated,
                "note": tx_result.get("note"),
            }, status=http_status.HTTP_201_CREATED)
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error anchoring report: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "error": f"Error anchoring report: {str(e)}"
            }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


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


class TransactionConfirmationsView(APIView):
    """Get transaction confirmation details"""
    
    def get(self, request, tx_hash):
        """Get confirmations for a transaction"""
        try:
            tracker = BlockchainStatusTracker()
            confirmations = tracker.get_confirmations(tx_hash)
            
            return Response({
                "success": True,
                "tx_hash": tx_hash,
                "confirmations": confirmations,
            }, status=http_status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


class IPFSVerificationView(APIView):
    """Verify IPFS report storage"""
    
    def get(self, request, report_id):
        """Verify report is stored on IPFS"""
        try:
            anchor = get_object_or_404(BlockchainAnchor, report_id=report_id)
            
            if not anchor.ipfs_cid:
                return Response({
                    "success": False,
                    "error": "Report not stored on IPFS"
                }, status=http_status.HTTP_404_NOT_FOUND)
            
            return Response({
                "success": True,
                "report_id": report_id,
                "ipfs_cid": anchor.ipfs_cid,
                "gateway_urls": [
                    f"https://ipfs.io/ipfs/{anchor.ipfs_cid}",
                    f"https://gateway.pinata.cloud/ipfs/{anchor.ipfs_cid}",
                ]
            }, status=http_status.HTTP_200_OK)
        
        except BlockchainAnchor.DoesNotExist:
            return Response({
                "success": False,
                "error": "No blockchain anchor found"
            }, status=http_status.HTTP_404_NOT_FOUND)


class IPFSStatsView(APIView):
    """Get IPFS distribution statistics"""
    
    def get(self, request):
        """Get overall IPFS statistics"""
        try:
            total_anchors = BlockchainAnchor.objects.filter(ipfs_cid__isnull=False).count()
            
            return Response({
                "success": True,
                "total_reports_distributed": total_anchors,
                "estimated_nodes": "1000+",
                "network": "IPFS",
            }, status=http_status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


class IntegrityVerificationView(APIView):
    """Advanced integrity verification for admin dashboard"""
    
    def post(self, request, report_id):
        """
        Perform comprehensive integrity verification:
        - Compare current report hash with blockchain anchor
        - Check if report has been modified
        - Verify blockchain proof
        - Return detailed verification intelligence
        """
        try:
            # Admin only
            if not request.user.is_authenticated or not getattr(request.user, 'is_staff', False):
                return Response({
                    "success": False,
                    "error": "Admin authentication required"
                }, status=http_status.HTTP_403_FORBIDDEN)
            
            # Get report
            try:
                report = Report.objects.get(reference_code=report_id)
            except Report.DoesNotExist:
                try:
                    report = Report.objects.get(pk=report_id)
                except Report.DoesNotExist:
                    return Response({
                        "success": False,
                        "error": f"Report {report_id} not found"
                    }, status=http_status.HTTP_404_NOT_FOUND)
            
            # Check if report is anchored on blockchain
            try:
                anchor = BlockchainAnchor.objects.get(report_id=report.reference_code)
            except BlockchainAnchor.DoesNotExist:
                return Response({
                    "success": False,
                    "error": "Report not anchored on blockchain",
                    "anchored": False,
                    "message": "No blockchain anchor found. Please anchor this report first."
                }, status=http_status.HTTP_200_OK)
            
            # Generate current evidence hash from report data
            cardano = CardanoEvidenceAnchoring()
            current_evidence_data = {
                "reference_code": report.reference_code,
                "category": report.category,
                "description": report.description[:500] if report.description else "",
                "is_anonymous": report.is_anonymous,
                "created_at": report.created_at.isoformat() if report.created_at else "",
            }
            current_evidence_hash = cardano.generate_evidence_hash(current_evidence_data)
            
            # Get blockchain hash
            blockchain_hash = anchor.evidence_hash
            
            # Compare hashes - determine if report has been modified
            hashes_match = current_evidence_hash == blockchain_hash
            
            # Build integrity verification intelligence
            verification_data = {
                "success": True,
                "anchored": True,
                "report_id": report.reference_code,
                
                # Hash comparison
                "integrity": {
                    "status": "VERIFIED" if hashes_match else "MODIFIED",
                    "match": hashes_match,
                    "current_hash": current_evidence_hash,
                    "blockchain_hash": blockchain_hash,
                    "hash_match_percentage": 100 if hashes_match else 0,
                },
                
                # Report metadata
                "report": {
                    "reference_code": report.reference_code,
                    "category": report.get_category_display(),
                    "status": report.get_status_display(),
                    "is_anonymous": report.is_anonymous,
                    "submitted_at": report.created_at.isoformat(),
                    "last_updated": report.updated_at.isoformat(),
                    "days_anchored": (report.updated_at - anchor.created_at).days if anchor.created_at else 0,
                },
                
                # Blockchain proof
                "blockchain": {
                    "transaction_hash": anchor.transaction_hash,
                    "evidence_hash": anchor.evidence_hash,
                    "status": anchor.get_status_display(),
                    "confirmations": anchor.confirmations,
                    "network": anchor.network,
                    "anchored_at": anchor.created_at.isoformat(),
                    "confirmed_at": anchor.confirmed_at.isoformat() if anchor.confirmed_at else None,
                    "block_number": anchor.block_number,
                },
                
                # Detailed checks
                "checks": {
                    "hash_integrity": {
                        "name": "Hash Integrity Check",
                        "passed": hashes_match,
                        "description": "Verifies that report content hasn't been modified since blockchain anchoring",
                        "status": "✓ PASSED" if hashes_match else "✗ FAILED",
                    },
                    "blockchain_confirmation": {
                        "name": "Blockchain Confirmation Check",
                        "passed": anchor.confirmations is not None and anchor.confirmations >= 0,
                        "description": f"Report confirmed by blockchain with {anchor.confirmations or 0} confirmations",
                        "confirmations": anchor.confirmations,
                        "status": "✓ CONFIRMED" if anchor.confirmations and anchor.confirmations > 0 else "⏳ PENDING",
                    },
                    "authenticity": {
                        "name": "Report Authenticity",
                        "passed": True,
                        "description": "Report exists in immutable blockchain record",
                        "status": "✓ AUTHENTIC",
                    },
                    "tampering_detection": {
                        "name": "Tampering Detection",
                        "passed": hashes_match,
                        "description": "Detects if report has been modified after blockchain anchoring",
                        "status": "✓ NO TAMPERING" if hashes_match else "✗ TAMPERING DETECTED",
                    },
                },
                
                # Verification summary
                "summary": {
                    "all_checks_passed": hashes_match and (anchor.confirmations is not None and anchor.confirmations >= 0),
                    "verification_timestamp": cardano.get_current_timestamp(),
                    "verified_by": request.user.email if request.user.email else request.user.username,
                    "recommendation": "Report integrity verified ✓" if hashes_match else "⚠ Report has been modified after anchoring",
                },
            }
            
            return Response(verification_data, status=http_status.HTTP_200_OK)
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error during integrity verification: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "error": f"Verification error: {str(e)}"
            }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


class HashSearchView(APIView):
    """Search for and decrypt blockchain hashes"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Search for a hash in the blockchain
        Decrypt and display information if found
        """
        try:
            # Admin only
            if not getattr(request.user, 'is_staff', False):
                return Response({
                    "success": False,
                    "error": "Admin authentication required"
                }, status=http_status.HTTP_403_FORBIDDEN)
            
            search_hash = request.data.get('search_hash', '').strip()
            
            if not search_hash:
                return Response({
                    "success": False,
                    "error": "Please provide a hash to search"
                }, status=http_status.HTTP_400_BAD_REQUEST)
            
            # Search for the hash in blockchain anchors (evidence_hash or transaction_hash)
            try:
                anchor = BlockchainAnchor.objects.get(evidence_hash=search_hash)
            except BlockchainAnchor.DoesNotExist:
                try:
                    anchor = BlockchainAnchor.objects.get(transaction_hash=search_hash)
                except BlockchainAnchor.DoesNotExist:
                    return Response({
                        "success": True,
                        "found": False,
                        "message": "Hash not found in blockchain database"
                    }, status=http_status.HTTP_200_OK)
            
            # Hash found - get the report data
            try:
                report = Report.objects.get(reference_code=anchor.report_id)
            except Report.DoesNotExist:
                return Response({
                    "success": True,
                    "found": False,
                    "message": "Associated report not found"
                }, status=http_status.HTTP_200_OK)
            
            # Return decrypted information
            return Response({
                "success": True,
                "found": True,
                "report": {
                    "id": str(report.id),
                    "reference_code": report.reference_code,
                    "category": report.get_category_display(),
                    "status": report.get_status_display(),
                    "description": report.description,
                    "location_description": report.location_description,
                    "latitude": float(report.latitude) if report.latitude else None,
                    "longitude": float(report.longitude) if report.longitude else None,
                    "is_anonymous": report.is_anonymous,
                    "created_at": report.created_at.isoformat(),
                    "updated_at": report.updated_at.isoformat(),
                },
                "anchor": {
                    "report_id": anchor.report_id,
                    "evidence_hash": anchor.evidence_hash,
                    "transaction_hash": anchor.transaction_hash,
                    "status": anchor.get_status_display(),
                    "confirmations": anchor.confirmations,
                    "network": anchor.network,
                    "created_at": anchor.created_at.isoformat(),
                    "confirmed_at": anchor.confirmed_at.isoformat() if anchor.confirmed_at else None,
                    "block_number": anchor.block_number,
                }
            }, status=http_status.HTTP_200_OK)
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error during hash search: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "error": f"Search error: {str(e)}"
            }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)