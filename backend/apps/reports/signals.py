"""
Django signals for audit logging
Tracks model changes (create, update, delete) automatically
"""
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Report, ReportUpdate, AuditLog
import threading


# Thread-local storage for current request
_thread_locals = threading.local()


def get_current_request():
    """Get the current request from thread-local storage"""
    return getattr(_thread_locals, 'request', None)


def set_current_request(request):
    """Store the current request in thread-local storage"""
    _thread_locals.request = request


class AuditLogSignalMiddleware:
    """
    Middleware to store the current request in thread-local storage
    This allows signals to access request information
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        set_current_request(request)
        response = self.get_response(request)
        set_current_request(None)
        return response


def create_audit_log(user, action, resource, details=None, request=None):
    """
    Helper function to create audit log entries
    """
    if not request:
        request = get_current_request()
    
    # Get IP and device info from request if available
    ip_address = None
    device_info = ''
    
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        device_info = request.META.get('HTTP_USER_AGENT', '')[:255]
    
    try:
        AuditLog.objects.create(
            user=user,
            action=action,
            resource=resource,
            details=details or {},
            ip_address=ip_address,
            device_info=device_info
        )
    except Exception as e:
        print(f"Failed to create audit log: {e}")


# ========== REPORT SIGNALS ==========
@receiver(post_save, sender=Report)
def log_report_save(sender, instance, created, **kwargs):
    """Log when a Report is created or updated"""
    request = get_current_request()
    
    # Skip if no user (system action)
    if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
        return
    
    # Already logged by middleware
    if getattr(request, '_audit_logged', False):
        return
    
    action = 'create_report' if created else 'update_report'
    resource = f'reports.report.{instance.reference_code}'
    
    details = {
        'reference_code': instance.reference_code,
        'category': instance.category,
        'status': instance.status,
        'is_anonymous': instance.is_anonymous,
        'created': created
    }
    
    if not created:
        # Track what fields changed
        update_fields = kwargs.get('update_fields')
        if update_fields:
            details['fields_changed'] = list(update_fields)
        else:
            details['fields_changed'] = []
    
    create_audit_log(request.user, action, resource, details, request)
    request._audit_logged = True


@receiver(pre_delete, sender=Report)
def log_report_delete(sender, instance, **kwargs):
    """Log when a Report is deleted"""
    request = get_current_request()
    
    if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
        return
    
    action = 'delete_report'
    resource = f'reports.report.{instance.reference_code}'
    
    details = {
        'reference_code': instance.reference_code,
        'category': instance.category,
        'status': instance.status,
        'created_at': str(instance.created_at)
    }
    
    create_audit_log(request.user, action, resource, details, request)


# ========== REPORT UPDATE SIGNALS ==========
@receiver(post_save, sender=ReportUpdate)
def log_report_status_change(sender, instance, created, **kwargs):
    """Log when a ReportUpdate (status change) is created"""
    if not created:
        return
    
    request = get_current_request()
    
    # Use the user from ReportUpdate if no request
    user = instance.user
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        user = request.user
    
    if not user:
        return
    
    action = 'status_change'
    resource = f'reports.report.{instance.report.reference_code}'
    
    details = {
        'reference_code': instance.report.reference_code,
        'old_status': instance.old_status,
        'new_status': instance.new_status,
        'notes': instance.notes
    }
    
    create_audit_log(user, action, resource, details, request)


# ========== USER AUTHENTICATION SIGNALS ==========
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful user logins"""
    action = 'user_login'
    resource = 'auth.login'
    
    details = {
        'username': user.username,
        'success': True
    }
    
    create_audit_log(user, action, resource, details, request)


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logouts"""
    if not user:
        return
    
    action = 'user_logout'
    resource = 'auth.logout'
    
    details = {
        'username': user.username
    }
    
    create_audit_log(user, action, resource, details, request)


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Log failed login attempts"""
    action = 'user_login_failed'
    resource = 'auth.login'
    
    details = {
        'username': credentials.get('username', 'unknown'),
        'success': False
    }
    
    # No user for failed login
    create_audit_log(None, action, resource, details, request)
