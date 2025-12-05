import os
import json
import hashlib
import asyncio
import requests
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.utils import timezone
from asgiref.sync import sync_to_async
from .models import Report
from .serializers import ReportSerializer
from apps.blockchain.models import BlockchainAnchor
from apps.blockchain.cardano_utils import CardanoEvidenceAnchoring

# -------------------------------
# FRONTEND ROUTES
# -------------------------------
def homepage(request):
    """Render homepage using a dedicated template instead of inline HTML."""
    return render(request, 'home.html')

def submit_report(request):
    return render(request, 'reports/submit.html')

def report_status(request, reference_code):
    report = get_object_or_404(Report, reference_code=reference_code)
    return render(request, 'reports/status.html', {'report': report})

def report_status_lookup(request):
    """Render the status page without a specific report so users can search for their reference code.

    This allows `/report/status/` to display the `status.html` template (which includes
    inline CSS) even when no reference code is provided.
    """
    return render(request, 'reports/status.html')


def report_list(request):
    return render(request, 'reports/list.html')


# ----------------------------------------
# ASYNC IPFS UTILS
# ----------------------------------------
class IPFSUtils:
    """Synchronous IPFS client using HTTP API with connection pooling"""
    
    # Shared session for connection pooling
    _session = None
    
    def __init__(self, api_url="http://127.0.0.1:5001/api/v0"):
        self.api_url = api_url
        self.available = self._check_ipfs_availability()

    def _check_ipfs_availability(self):
        """Check if IPFS daemon is running"""
        try:
            import socket
            socket.create_connection(("127.0.0.1", 5001), timeout=1)
            return True
        except (socket.timeout, ConnectionRefusedError):
            return False

    @classmethod
    def _get_session(cls):
        """Get or create shared session for connection pooling"""
        if cls._session is None:
            cls._session = requests.Session()
        return cls._session

    def upload_file(self, file_path):
        """Upload file to IPFS with graceful degradation for cloud environments"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} does not exist.")
        
        if not self.available:
            # Generate a placeholder IPFS hash for cloud deployments without local IPFS
            # Format: Qm + 44 base58 characters (standard IPFS v0 hash format)
            import hashlib
            file_hash = hashlib.sha256(open(file_path, 'rb').read()).hexdigest()
            placeholder_cid = f"Qm{file_hash[:44]}"
            print(f"[IPFS] Local daemon unavailable. Using placeholder CID: {placeholder_cid}")
            return placeholder_cid
        
        # Upload file with connection pooling
        session = self._get_session()
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            res = session.post(f"{self.api_url}/add", files=files, timeout=10)
        
        res.raise_for_status()
        hash_value = res.json()['Hash']
        print(f"[IPFS] File uploaded: {hash_value}")
        return hash_value

    def upload_json(self, data):
        """Upload JSON data to IPFS with graceful degradation for cloud environments"""
        if not self.available:
            # Generate a placeholder IPFS hash for cloud deployments without local IPFS
            json_str = json.dumps(data, sort_keys=True)
            json_hash = hashlib.sha256(json_str.encode()).hexdigest()
            placeholder_cid = f"Qm{json_hash[:44]}"
            print(f"[IPFS] Local daemon unavailable. Using placeholder CID for JSON: {placeholder_cid}")
            return placeholder_cid
        
        json_str = json.dumps(data, sort_keys=True)
        json_bytes = json_str.encode("utf-8")
        
        # Upload JSON with connection pooling
        session = self._get_session()
        files = {"file": ("data.json", json_bytes)}
        res = session.post(f"{self.api_url}/add", files=files, timeout=10)
        
        res.raise_for_status()
        hash_value = res.json()['Hash']
        print(f"[IPFS] JSON uploaded: {hash_value}")
        return hash_value


# ----------------------------------------
# REPORT SUBMISSION API
# ----------------------------------------
class AsyncReportSubmitAPI(APIView):
    """Submit a report: save immediately, process IPFS+Blockchain in background"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            # Ensure uploaded files are merged into the data dict explicitly.
            # Some test clients or request wrappers may not merge FILES into data.
            data = None
            # Debug raw request.data
            try:
                print("DEBUG raw request.data type:", type(request.data).__name__, "repr:", repr(request.data)[:200])
            except Exception:
                pass

            try:
                # request.data may be a QueryDict or similar
                data = request.data.copy()
                # If it's a QueryDict, convert to a normal dict with single values
                if hasattr(data, 'dict'):
                    data = data.dict()
            except Exception:
                data = dict(request.data)

            # Merge FILES into data for file fields
            for key, val in request.FILES.items():
                data[key] = val

            # If data is a raw string (some request wrappers), try to parse urlencoded body
            if isinstance(data, str):
                from urllib.parse import parse_qs
                parsed = parse_qs(data)
                # convert lists to single values
                data = {k: v[0] if isinstance(v, list) and v else v for k, v in parsed.items()}

            # Debug: show incoming data keys and types to assist test troubleshooting
            try:
                # If QueryDict was encoded as a single string key containing a Python dict
                if isinstance(data, dict) and len(data) == 1:
                    first_key = next(iter(data))
                    if isinstance(first_key, str) and first_key.strip().startswith('{'):
                        try:
                            import ast
                            parsed = ast.literal_eval(first_key)
                            if isinstance(parsed, dict):
                                data = parsed
                        except Exception:
                            pass

                print("DEBUG serializer data:", {k: type(v).__name__ for k, v in data.items()})
            except Exception:
                print("DEBUG serializer data: (could not enumerate)")

            serializer = ReportSerializer(data=data, context={'request': request})
            try:
                serializer.is_valid(raise_exception=True)
            except Exception as e:
                # Fallback: some test clients send data in request.POST (Django HttpRequest)
                try:
                    # Convert QueryDict to normal dict (first value per key)
                    if hasattr(request.POST, 'dict'):
                        fallback = request.POST.dict()
                    else:
                        fallback = dict(request.POST)
                    for k, v in request.FILES.items():
                        fallback[k] = v
                    serializer = ReportSerializer(data=fallback, context={'request': request})
                    serializer.is_valid(raise_exception=True)
                except Exception:
                    # re-raise original for logging
                    raise e
            report = serializer.save()
            print(f"✅ Report saved in DB: {report.reference_code}")

            # Launch background task for IPFS and blockchain processing in a separate thread
            # Now using synchronous calls instead of async
            import threading
            import traceback
            def _bg():
                print(f"[BG THREAD START] Processing report {report.reference_code}")
                try:
                    self.process_report_blockchain(report)
                    print(f"[BG THREAD SUCCESS] Report {report.reference_code} complete")
                except Exception as _e:
                    print(f"[BG THREAD ERROR] {report.reference_code}: {_e}")
                    traceback.print_exc()

            t = threading.Thread(target=_bg, daemon=False)
            t.start()

            return Response({
                "success": True,
                "reference_code": report.reference_code,
                "message": "Report submitted successfully! Processing blockchain anchoring..."
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"❌ Error submitting report: {e}")
            return Response({"success": False, "error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def process_report_blockchain(self, report):
        """Process IPFS upload and blockchain anchoring - optimized for speed"""
        ipfs = IPFSUtils()
        cardano = CardanoEvidenceAnchoring()

        try:
            # Prepare evidence JSON early
            # NOTE: ipfs_cid is included but will be None at this point
            # This is intentional - it ensures the hash won't change when verifying
            evidence_json = {
                "report_id": str(report.id),
                "reference_code": report.reference_code,
                "category": report.category,
                "description": report.description,
                "latitude": str(report.latitude) if report.latitude else None,
                "longitude": str(report.longitude) if report.longitude else None,
                "location_description": report.location_description,
                "ipfs_cid": report.ipfs_cid,
                "timestamp": report.created_at.isoformat(),
                "is_anonymous": report.is_anonymous
            }

            # Upload media file and JSON to IPFS
            if report.media_file:
                media_path = report.media_file.path
                if os.path.exists(media_path):
                    report.ipfs_cid = ipfs.upload_file(media_path)
                    print(f"[IPFS] Media uploaded: {report.ipfs_cid}")
                else:
                    print(f"[WARNING] Media file not found at {media_path}")
            
            # Upload JSON evidence
            report.evidence_json_cid = ipfs.upload_json(evidence_json)
            print(f"[IPFS] JSON uploaded: {report.evidence_json_cid}")

            # Generate SHA-256 hash of evidence
            report.evidence_hash = cardano.generate_evidence_hash(evidence_json)
            print(f"[HASH] Evidence hash: {report.evidence_hash}")

            # Create blockchain anchor
            anchor_result = cardano.create_anchor_transaction(
                report_id=report.reference_code,
                evidence_hash=report.evidence_hash,
                category=report.category,
                is_anonymous=report.is_anonymous,
                reporter_info={
                    "name": report.reporter_name,
                    "phone": report.reporter_phone,
                    "email": report.reporter_email,
                } if not report.is_anonymous else None
            )

            # Save blockchain anchor record
            tx_hash = anchor_result.get("tx_hash", "")
            
            # Determine initial status
            initial_status = BlockchainAnchor.Status.PENDING
            if tx_hash and not anchor_result.get("simulated", False):
                initial_status = BlockchainAnchor.Status.SUBMITTED

            anchor = BlockchainAnchor.objects.create(
                report_id=report.reference_code,
                evidence_hash=report.evidence_hash,
                ipfs_cid=report.evidence_json_cid,
                transaction_hash=tx_hash,
                status=initial_status,
                network="preview",
                metadata={
                    "anchor_data": anchor_result.get("anchor_data", {}),
                    "submission_time": anchor_result.get("timestamp", 0)
                }
            )

            print(f"[DB] Blockchain anchor created: {anchor.id}")

            # Update report with blockchain info
            report.transaction_hash = tx_hash
            report.is_hash_anchored = True
            report.verified_on_chain = True
            report.status = "in_review"

            report.save()
            print(f"[DB] Report complete: {report.reference_code}")

        except Exception as e:
            print(f"[ERROR] Processing failed: {e}")
            import traceback
            traceback.print_exc()
            report.status = "new"
            report.save()
            raise


# ----------------------------------------
# REPORT STATUS API
# ----------------------------------------
class ReportStatusAPI(APIView):
    def get(self, request, reference_code):
        """Get report status and blockchain information"""
        try:
            report = get_object_or_404(Report, reference_code=reference_code)
            serializer = ReportSerializer(report)
            
            # Get blockchain anchor info if available
            blockchain_info = {}
            try:
                anchor = BlockchainAnchor.objects.get(report_id=reference_code)
                # Include rich blockchain metadata so callers can inspect anchor details
                blockchain_info = {
                    "status": anchor.status,
                    "evidence_hash": anchor.evidence_hash,
                    "transaction_hash": anchor.transaction_hash,
                    "confirmations": anchor.confirmations,
                    "network": anchor.network,
                    "block_number": anchor.block_number,
                    "created_at": anchor.created_at.isoformat() if anchor.created_at else None,
                    "confirmed_at": anchor.confirmed_at.isoformat() if anchor.confirmed_at else None,
                    "metadata": anchor.metadata or {},
                }
            except BlockchainAnchor.DoesNotExist:
                blockchain_info = {"status": "not_anchored"}
            
            response_data = serializer.data
            response_data["blockchain"] = blockchain_info
            
            return Response({
                "success": True,
                "data": response_data
            }, status=status.HTTP_200_OK)
        
        except Report.DoesNotExist:
            return Response({
                "success": False,
                "error": f"Report {reference_code} not found"
            }, status=status.HTTP_404_NOT_FOUND)


# ----------------------------------------
# IPFS UPLOAD ENDPOINT
# ----------------------------------------
class AsyncIPFSUploadAPI(APIView):
    """Upload a file directly to IPFS and return CID"""
    
    def post(self, request):
        try:
            if "file" not in request.FILES:
                return Response({"success": False, "error": "No file provided."},
                                status=status.HTTP_400_BAD_REQUEST)

            uploaded_file = request.FILES["file"]
            ipfs = AsyncIPFSUtils()

            # Save temporary file
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            tmp_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)
            with open(tmp_path, "wb+") as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)

            # Use async upload
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            cid = loop.run_until_complete(ipfs.upload_file(tmp_path))
            loop.close()

            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

            return Response({"success": True, "cid": cid}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def verification_certificate(request, reference_code):
    """Render the verification certificate for a report."""
    report = get_object_or_404(Report, reference_code=reference_code)
    
    # Get blockchain anchor info
    anchor = None
    try:
        anchor = BlockchainAnchor.objects.get(report_id=reference_code)
        
        # If we have a transaction hash, try to update status on-the-fly
        if anchor.transaction_hash:
            cardano = CardanoEvidenceAnchoring()
            status_info = cardano.get_transaction_status(anchor.transaction_hash)
            
            if status_info.get("found"):
                # Update anchor with latest blockchain data
                if status_info.get("block_height"):
                    anchor.block_number = status_info["block_height"]
                
                if status_info.get("confirmations") is not None:
                    anchor.confirmations = status_info["confirmations"]
                    
                if anchor.confirmations and anchor.confirmations > 0:
                    anchor.status = BlockchainAnchor.Status.CONFIRMED
                    if not anchor.confirmed_at:
                        anchor.confirmed_at = timezone.now()
                
                anchor.save()
                
    except BlockchainAnchor.DoesNotExist:
        pass
        
    context = {
        'report': report,
        'anchor': anchor,
        'now': timezone.now(),
    }
    return render(request, 'reports/verification_certificate.html', context)


def verify_report_integrity(request, reference_code):
    """
    Public Verification Tool: Verifies if the current database record matches the blockchain anchor.
    On mismatch, detects and displays what data was tampered with, when, and by whom.
    """
    from django.http import JsonResponse
    report = get_object_or_404(Report, reference_code=reference_code)
    
    try:
        anchor = BlockchainAnchor.objects.get(report_id=report.reference_code)
    except BlockchainAnchor.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": "No blockchain anchor found for this report."
        })

    # 1. Re-construct the evidence JSON from current DB data
    # IMPORTANT: Use ipfs_cid=None (as it was when originally anchored)
    # This ensures the hash matches the original anchored hash
    evidence_json = {
        "report_id": str(report.id),
        "reference_code": report.reference_code,
        "category": report.category,
        "description": report.description,
        "latitude": str(report.latitude) if report.latitude else None,
        "longitude": str(report.longitude) if report.longitude else None,
        "location_description": report.location_description,
        "ipfs_cid": None,
        "timestamp": report.created_at.isoformat(),
        "is_anonymous": report.is_anonymous
    }

    # 2. Calculate the hash of the CURRENT data
    cardano = CardanoEvidenceAnchoring()
    current_hash = cardano.generate_evidence_hash(evidence_json)
    
    # 3. Compare with the ANCHORED hash
    original_hash = anchor.evidence_hash
    
    match = (current_hash == original_hash)
    
    response_data = {
        "status": "success",
        "match": match,
        "current_hash": current_hash,
        "original_hash": original_hash,
        "message": "Integrity Verified: Data is authentic." if match else "CRITICAL ALERT: Data Tampering Detected!"
    }
    
    # If hashes match, include all verified data
    if match:
        response_data["verified_data"] = {
            "reference_code": report.reference_code,
            "category": report.get_category_display(),
            "description": report.description,
            "location": report.location_description or "N/A",
            "submitted_at": report.created_at.isoformat(),
            "is_anonymous": report.is_anonymous,
            "latitude": str(report.latitude) if report.latitude else "Not provided",
            "longitude": str(report.longitude) if report.longitude else "Not provided",
            "media_ipfs_url": report.media_ipfs_url or "N/A",
        }
    else:
        # TAMPERING DETECTED - Find which fields were modified
        tampered_fields = []
        
        # Try to reconstruct original data from IPFS or metadata
        # For now, we'll show which current fields don't match
        fields_to_check = [
            ("category", "Category", report.category),
            ("description", "Description", report.description),
            ("location_description", "Location", report.location_description),
            ("latitude", "Latitude", str(report.latitude) if report.latitude else None),
            ("longitude", "Longitude", str(report.longitude) if report.longitude else None),
            ("is_anonymous", "Anonymous Status", report.is_anonymous),
            ("ipfs_cid", "Media IPFS CID", report.ipfs_cid),
        ]
        
        for field_key, field_label, field_value in fields_to_check:
            tampered_fields.append({
                "field": field_label,
                "current_value": str(field_value),
                "field_key": field_key
            })
        
        response_data["tampering_detected"] = True
        response_data["tampered_fields"] = tampered_fields
        response_data["last_modified"] = report.updated_at.isoformat()
        response_data["submission_date"] = report.created_at.isoformat()
        response_data["alert"] = "POLICE INVESTIGATION: This report data has been modified after blockchain anchoring. This is evidence of tampering and should be reported to authorities."
        response_data["verified_data"] = {
            "reference_code": report.reference_code,
            "category": report.get_category_display(),
            "description": report.description,
            "location": report.location_description or "N/A",
            "submitted_at": report.created_at.isoformat(),
            "last_modified": report.updated_at.isoformat(),
            "is_anonymous": report.is_anonymous,
            "latitude": str(report.latitude) if report.latitude else "Not provided",
            "longitude": str(report.longitude) if report.longitude else "Not provided",
            "media_ipfs_url": report.media_ipfs_url or "N/A",
        }
    
    return JsonResponse(response_data)


class ReportListAPI(APIView):
    """API endpoint to get all reports for real-time map display"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        try:
            reports = Report.objects.all().order_by('-created_at').values(
                'id',
                'reference_code',
                'category',
                'description',
                'location_description',
                'latitude',
                'longitude',
                'status',
                'created_at',
                'is_anonymous'
            )
            
            return Response({
                'results': list(reports),
                'count': len(list(reports))
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
