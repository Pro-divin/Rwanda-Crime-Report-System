"""
Middleware for automatic audit logging of admin actions
"""
from django.utils.deprecation import MiddlewareMixin
from .models import AuditLog


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log admin actions to AuditLog
    Tracks view actions, form submissions, and model changes
    """
    
    def process_request(self, request):
        """Store request in thread-local for signal handlers"""
        # Store the request object for use in signals
        request._audit_logged = False
        return None
    
    def process_response(self, request, response):
        """Log admin panel actions after response is ready"""
        
        # Only log for authenticated users
        if not request.user or not request.user.is_authenticated:
            return response
        
        # Only log admin panel actions (and API endpoints if needed)
        path = request.path
        if not (path.startswith('/admin/') or path.startswith('/api/')):
            return response
        
        # Skip if already logged by signals
        if getattr(request, '_audit_logged', False):
            return response
        
        # Determine action type
        action = None
        resource = None
        details = {}
        
        if request.method == 'GET':
            if '/change/' in path or '/add/' in path:
                # Viewing/editing a specific object
                action = 'view_form'
                resource = self._extract_resource(path)
            elif '/changelist/' in path or path.count('/') == 3:
                # Viewing list page
                action = 'view_list'
                resource = self._extract_resource(path)
        
        elif request.method == 'POST':
            # POST actions are typically logged by signals, but catch any missed
            if '_save' in request.POST or '_continue' in request.POST:
                action = 'save'
                resource = self._extract_resource(path)
            elif '_delete' in request.POST:
                action = 'delete'
                resource = self._extract_resource(path)
        
        # Create audit log if action detected
        if action and resource and not getattr(request, '_audit_logged', False):
            self._create_audit_log(request, action, resource, details)
            request._audit_logged = True
        
        return response
    
    def _extract_resource(self, path):
        """Extract resource name from admin URL path"""
        # Example: /admin/reports/report/123/change/ -> reports.report
        parts = [p for p in path.split('/') if p and p != 'admin']
        if len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"
        elif len(parts) == 1:
            return parts[0]
        return 'admin'
    
    def _create_audit_log(self, request, action, resource, details=None):
        """Create an audit log entry"""
        try:
            # Get client IP
            ip_address = self._get_client_ip(request)
            
            # Get device info from User-Agent
            device_info = request.META.get('HTTP_USER_AGENT', '')[:255]
            
            # Create log entry
            AuditLog.objects.create(
                user=request.user,
                action=action,
                resource=resource,
                details=details or {},
                ip_address=ip_address,
                device_info=device_info
            )
        except Exception as e:
            # Don't break the request if audit logging fails
            print(f"Failed to create audit log: {e}")
    
    def _get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
