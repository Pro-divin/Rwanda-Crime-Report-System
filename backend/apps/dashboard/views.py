from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from apps.reports.models import Report, ReportUpdate
import json

def is_admin(user):
    return user.is_authenticated and user.is_staff

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
    # Calculate analytics data
    total_reports = Report.objects.count()
    reports_today = Report.objects.filter(created_at__date=timezone.now().date()).count()
    
    # Simulated average response time
    avg_response_time = 2  # hours
    
    # Calculate resolution rate
    total_resolved = Report.objects.filter(status__in=['actioned', 'closed']).count()
    resolution_rate = round((total_resolved / total_reports * 100) if total_reports > 0 else 0, 1)
    
    # Category statistics for charts
    category_stats = []
    for category in Report._meta.get_field('category').choices:
        count = Report.objects.filter(category=category[0]).count()
        category_stats.append({
            'name': category[1],
            'total': count,
            'avg_response': 2,  # simulated
            'resolution_rate': 75,  # simulated
            'priority': 'High' if category[0] in ['kidnapping', 'house_fire'] else 'Medium'
        })
    
    # Status distribution
    status_distribution = {}
    for status in Report._meta.get_field('status').choices:
        count = Report.objects.filter(status=status[0]).count()
        status_distribution[status[1]] = count
    
    context = {
        'total_reports': total_reports,
        'reports_today': reports_today,
        'avg_response_time': avg_response_time,
        'resolution_rate': resolution_rate,
        'category_stats': category_stats,
        'status_distribution': json.dumps(status_distribution),
        'category_data': json.dumps({cat['name']: cat['total'] for cat in category_stats}),
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
