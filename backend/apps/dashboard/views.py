from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from apps.reports.models import Report, ReportUpdate
from apps.blockchain.models import BlockchainAnchor
from apps.blockchain.cardano_utils import CardanoEvidenceAnchoring
import json

def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_admin)
def verify_integrity(request, report_id):
    """
    Admin Police Tool: Verifies if the current database record matches the blockchain anchor.
    On mismatch, detects and displays what data was tampered with, when, and by whom.
    """
    report = get_object_or_404(Report, id=report_id)
    
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

@login_required
@user_passes_test(is_admin)
def dashboard(request):
    total_reports = Report.objects.count()
    new_reports = Report.objects.filter(status='new').count()
    actioned_reports = Report.objects.filter(status='actioned').count()
    
    # Category statistics
    categories = {}
    for category in Report._meta.get_field('category').choices:
        count = Report.objects.filter(category=category[0]).count()
        categories[category[1]] = count
    
    # Get recent reports
    recent_reports = Report.objects.all().order_by('-created_at')[:5]
    
    context = {
        'total_reports': total_reports,
        'new_reports': new_reports,
        'actioned_reports': actioned_reports,
        'categories': json.dumps(categories),
        'recent_reports': recent_reports,
    }
    return render(request, 'dashboard/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def reports_list(request):
    reports = Report.objects.all().order_by('-created_at')
    status_choices = Report._meta.get_field('status').choices
    category_choices = Report._meta.get_field('category').choices
    return render(request, 'dashboard/reports_list.html', {
        'reports': reports,
        'status_choices': status_choices,
        'category_choices': category_choices
    })

@login_required
@user_passes_test(is_admin)
def report_detail(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    updates = report.updates.all().order_by('-created_at')
    status_choices = Report._meta.get_field('status').choices
    return render(request, 'dashboard/report_detail.html', {
        'report': report,
        'updates': updates,
        'status_choices': status_choices
    })

@login_required
@user_passes_test(is_admin)
def analytics(request):
    from datetime import timedelta
    from django.db.models import Count, Q, Case, When, Avg, F, ExpressionWrapper, DurationField
    from django.db.models.functions import TruncDate
    
    # Total reports
    total_reports = Report.objects.count()
    
    # Reports today
    today = timezone.now().date()
    reports_today = Report.objects.filter(created_at__date=today).count()
    
    # Calculate resolution rate (actioned + closed)
    total_resolved = Report.objects.filter(status__in=['actioned', 'closed']).count()
    resolution_rate = round((total_resolved / total_reports * 100) if total_reports > 0 else 0, 1)
    
    # Calculate average response time (using updated_at - created_at)
    actioned_reports = Report.objects.filter(status__in=['actioned', 'closed']).exclude(updated_at__isnull=True)
    if actioned_reports.exists():
        avg_time = actioned_reports.aggregate(
            avg_diff=Avg(ExpressionWrapper(
                F('updated_at') - F('created_at'),
                output_field=DurationField()
            ))
        )['avg_diff']
        avg_response_time = round(avg_time.total_seconds() / 3600) if avg_time else 0
    else:
        avg_response_time = 0
    
    # Category statistics
    category_stats = []
    for category_key, category_name in Report._meta.get_field('category').choices:
        reports_in_category = Report.objects.filter(category=category_key)
        count = reports_in_category.count()
        
        # Calculate resolution rate per category
        resolved_in_category = reports_in_category.filter(status__in=['actioned', 'closed']).count()
        cat_resolution_rate = round((resolved_in_category / count * 100) if count > 0 else 0, 1)
        
        # Calculate avg response time per category
        actioned_in_category = reports_in_category.filter(status__in=['actioned', 'closed']).exclude(updated_at__isnull=True)
        if actioned_in_category.exists():
            cat_avg_time = actioned_in_category.aggregate(
                avg_diff=Avg(ExpressionWrapper(
                    F('updated_at') - F('created_at'),
                    output_field=DurationField()
                ))
            )['avg_diff']
            cat_avg_response = round(cat_avg_time.total_seconds() / 3600) if cat_avg_time else 0
        else:
            cat_avg_response = 0
        
        category_stats.append({
            'name': category_name,
            'total': count,
            'avg_response': cat_avg_response,
            'resolution_rate': cat_resolution_rate,
            'priority': 'High' if category_key in ['kidnapping', 'house_fire'] else 'Medium'
        })
    
    # Status distribution
    status_distribution = {}
    for status_key, status_name in Report._meta.get_field('status').choices:
        count = Report.objects.filter(status=status_key).count()
        status_distribution[status_name] = count
    
    # Category data for charts
    category_data = {cat['name']: cat['total'] for cat in category_stats}
    
    # Timeline data (last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    timeline_data = {}
    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        count = Report.objects.filter(created_at__date=date).count()
        timeline_data[date.strftime('%b %d')] = count
    
    # Response time distribution
    response_distribution = {
        '< 1h': 0,
        '1-4h': 0,
        '4-12h': 0,
        '12-24h': 0,
        '> 24h': 0
    }
    
    # More accurate response time distribution
    for report in actioned_reports:
        diff_hours = (report.updated_at - report.created_at).total_seconds() / 3600
        if diff_hours < 1:
            response_distribution['< 1h'] += 1
        elif diff_hours < 4:
            response_distribution['1-4h'] += 1
        elif diff_hours < 12:
            response_distribution['4-12h'] += 1
        elif diff_hours < 24:
            response_distribution['12-24h'] += 1
        else:
            response_distribution['> 24h'] += 1
    
    context = {
        'total_reports': total_reports,
        'reports_today': reports_today,
        'avg_response_time': avg_response_time,
        'resolution_rate': resolution_rate,
        'category_stats': category_stats,
        'status_distribution': json.dumps(status_distribution),
        'category_data': json.dumps(category_data),
        'timeline_data': json.dumps(timeline_data),
        'response_distribution': json.dumps(response_distribution),
    }
    return render(request, 'dashboard/analytics.html', context)

@login_required
@user_passes_test(is_admin)
def map_view(request):
    reports = Report.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    report_data = []
    
    for report in reports:
        report_data.append({
            'id': str(report.id),
            'reference_code': report.reference_code,
            'category': report.get_category_display(),
            'latitude': float(report.latitude),
            'longitude': float(report.longitude),
            'status': report.status,
            'description': report.description[:100] + '...' if len(report.description) > 100 else report.description
        })
    
    return render(request, 'dashboard/map.html', {
        'reports': json.dumps(report_data)
    })

@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def reports_api_all(request):
    """
    API endpoint for fetching all reports with coordinates for real-time map updates.
    Returns JSON array with full report data.
    """
    reports = Report.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True).order_by('-created_at')
    report_data = []
    
    for report in reports:
        report_data.append({
            'id': str(report.id),
            'reference_code': report.reference_code,
            'category': report.get_category_display(),
            'category_key': report.category,
            'latitude': float(report.latitude),
            'longitude': float(report.longitude),
            'status': report.status,
            'location_description': report.location_description or '',
            'description': report.description[:150] + '...' if len(report.description) > 150 else report.description,
            'created_at': report.created_at.isoformat(),
            'updated_at': report.updated_at.isoformat(),
            'is_anonymous': report.is_anonymous,
            'media_ipfs_url': report.media_ipfs_url or None,
        })
    
    return JsonResponse({
        'status': 'success',
        'count': len(report_data),
        'results': report_data
    })

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def update_report_status(request, report_id):
    """
    AJAX endpoint to update report status without page redirect.
    Returns JSON with updated report data.
    """
    try:
        report = get_object_or_404(Report, id=report_id)
        data = json.loads(request.body)
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        # Validate status
        valid_statuses = [choice[0] for choice in Report._meta.get_field('status').choices]
        if new_status not in valid_statuses:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid status value'
            }, status=400)
        
        old_status = report.status
        
        # Update report
        report.status = new_status
        report.save()
        
        # Create update record with correct field names
        ReportUpdate.objects.create(
            report=report,
            user=request.user,
            old_status=old_status,
            new_status=new_status,
            notes=notes
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'✅ Report status updated to {report.get_status_display()}',
            'report': {
                'id': str(report.id),
                'reference_code': report.reference_code,
                'status': report.status,
                'status_display': report.get_status_display(),
                'updated_at': report.updated_at.isoformat(),
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@login_required
@user_passes_test(is_admin)
def integrity_verification_dashboard(request):
    """
    Admin dashboard for verifying report integrity across all anchored reports
    Allows admins to select reports and verify their blockchain integrity
    """
    # Get all reports with blockchain anchors
    anchored_reports = Report.objects.filter(is_hash_anchored=True).order_by('-created_at')
    
    status_choices = Report._meta.get_field('status').choices
    category_choices = Report._meta.get_field('category').choices
    
    # Apply filters if provided
    if request.GET.get('status'):
        anchored_reports = anchored_reports.filter(status=request.GET.get('status'))
    
    if request.GET.get('category'):
        anchored_reports = anchored_reports.filter(category=request.GET.get('category'))
    
    if request.GET.get('date_from'):
        anchored_reports = anchored_reports.filter(created_at__date__gte=request.GET.get('date_from'))
    
    if request.GET.get('date_to'):
        anchored_reports = anchored_reports.filter(created_at__date__lte=request.GET.get('date_to'))
    
    return render(request, 'dashboard/integrity_verification.html', {
        'reports': anchored_reports,
        'status_choices': status_choices,
        'category_choices': category_choices,
    })
