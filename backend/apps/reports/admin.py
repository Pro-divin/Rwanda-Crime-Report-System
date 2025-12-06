from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Report, ReportUpdate, AuditLog

# -------------------------------
# REPORT ADMIN
# -------------------------------
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'reference_code', 'status_badge', 'category', 'priority', 'anonymous_badge',
        'reporter_display', 'reporter_phone',
        'created_at', 'updated_at_short'
    )
    list_filter = ('category', 'status', 'priority', 'is_anonymous', 'created_at')
    search_fields = ('reference_code', 'description', 'reporter_name', 'reporter_email')
    readonly_fields = (
        'reference_code', 'ipfs_cid', 'evidence_json_cid', 'ipfs_report_cid', 'evidence_hash',
        'transaction_hash', 'is_hash_anchored', 'verified_on_chain',
        'media_file_preview', 'evidence_json_preview', 'ipfs_report_preview',
        'created_at', 'updated_at'
    )
    fieldsets = (
        ('Report Info', {
            'fields': ('reference_code', 'category', 'description', 'location_description',
                       'latitude', 'longitude', 'status', 'priority')
        }),
        ('Reporter Info', {
            'fields': ('is_anonymous', 'reporter_name', 'reporter_phone', 'reporter_email', 'user'),
            'description': 'Check "Is anonymous" to hide reporter identity. Reporter fields will be ignored if anonymous.'
        }),
        ('Media & IPFS', {
            'fields': ('media_file', 'media_file_preview', 'ipfs_cid', 
                       'evidence_json_preview', 'evidence_json_cid',
                       'ipfs_report_preview', 'ipfs_report_cid',
                       'evidence_hash', 'transaction_hash', 'is_hash_anchored', 'verified_on_chain')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
        ('Blockchain Metadata', {
            'fields': ('blockchain_metadata',)
        }),
    )

    def status_badge(self, obj):
        """Display status with color-coded badge"""
        colors = {
            'new': '#0088ce',
            'in_review': '#ffc107',
            'forwarded': '#17a2b8',
            'actioned': '#28a745',
            'closed': '#6c757d',
        }
        color = colors.get(obj.status, '#999999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold; white-space: nowrap;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def updated_at_short(self, obj):
        """Display updated_at in compact format"""
        if obj.updated_at:
            return obj.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        return "—"
    updated_at_short.short_description = 'Last Updated'

    def anonymous_badge(self, obj):
        """Display anonymous status with badge"""
        if obj.is_anonymous:
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">🔒 Anonymous</span>'
            )
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">👤 Public</span>'
        )
    anonymous_badge.short_description = 'Reporter Type'

    def reporter_display(self, obj):
        """Display reporter name or 'Anonymous' if anonymous"""
        if obj.is_anonymous:
            return format_html('<em style="color: #999;">Anonymous</em>')
        return obj.reporter_name or format_html('<em style="color: #999;">Not provided</em>')
    reporter_display.short_description = 'Reporter Name'

    # ========== DYNAMIC FORM BEHAVIOR ==========
    class Media:
        js = ('admin/js/report_admin.js',)
        css = {
            'all': ('admin/css/report_admin.css',)
        }

    # ========== DELETION PROTECTION ==========
    def has_delete_permission(self, request, obj=None):
        """
        Prevent deletion of reports anchored to blockchain/IPFS
        Evidence on distributed network cannot be deleted!
        """
        if obj:
            # Check if report is anchored to blockchain
            if obj.evidence_hash:
                from apps.blockchain.models import BlockchainAnchor
                try:
                    anchor = BlockchainAnchor.objects.get(report_id=obj.reference_code)
                    if anchor.transaction_hash:
                        messages.error(
                            request,
                            format_html(
                                '🔒 <strong>Cannot delete {}</strong>: '
                                'Report is permanently anchored to blockchain (TX: {}...). '
                                'Evidence is immutable and preserved on 4000+ nodes globally. '
                                '<br><br>'
                                '📦 <strong>IPFS:</strong> {} nodes have full report<br>'
                                '⛓️ <strong>Cardano:</strong> {} validator nodes have hash<br><br>'
                                '💡 To hide from view, archive the report instead of deleting.',
                                obj.reference_code,
                                anchor.transaction_hash[:16],
                                "1000+",
                                "3000+"
                            )
                        )
                        return False
                except BlockchainAnchor.DoesNotExist:
                    pass
            
            # Check if report is on IPFS
            if obj.ipfs_report_cid:
                messages.error(
                    request,
                    format_html(
                        '🔒 <strong>Cannot delete {}</strong>: '
                        'Report is distributed on IPFS network (CID: {}...). '
                        'Content is replicated across 1000+ nodes globally and cannot be deleted. '
                        '<br><br>'
                        '🌐 Report is accessible via public gateways:<br>'
                        '• https://ipfs.io/ipfs/{}<br>'
                        '• https://gateway.pinata.cloud/ipfs/{}<br><br>'
                        '💡 Deleting from database won\'t remove from IPFS. Archive instead.',
                        obj.reference_code,
                        obj.ipfs_report_cid[:16],
                        obj.ipfs_report_cid,
                        obj.ipfs_report_cid
                    )
                )
                return False
        
        # Allow deletion of non-anchored reports (only by superusers)
        return request.user.is_superuser
    
    def delete_model(self, request, obj):
        """
        Log deletion attempts and prevent deletion of anchored reports
        """
        # Create audit log for deletion attempt
        AuditLog.objects.create(
            user=request.user,
            action='delete_attempt',
            resource=f'Report {obj.reference_code}',
            details={
                'reference_code': obj.reference_code,
                'ipfs_cid': obj.ipfs_report_cid,
                'evidence_hash': obj.evidence_hash,
                'category': obj.category,
                'status': 'PREVENTED' if (obj.evidence_hash or obj.ipfs_report_cid) else 'ALLOWED',
                'reason': 'Report anchored to blockchain/IPFS' if (obj.evidence_hash or obj.ipfs_report_cid) else 'Not anchored'
            }
        )
        
        # Double-check: Prevent deletion if anchored
        if obj.evidence_hash or obj.ipfs_report_cid:
            messages.error(
                request,
                f'🚫 Deletion prevented: {obj.reference_code} is immutably stored on distributed network!'
            )
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied(
                "Cannot delete anchored report. Evidence is permanently preserved on 4000+ nodes."
            )
        
        # Log successful deletion (only for non-anchored reports)
        AuditLog.objects.create(
            user=request.user,
            action='delete_report',
            resource=f'Report {obj.reference_code}',
            details={
                'reference_code': obj.reference_code,
                'category': obj.category,
                'status': 'DELETED',
                'note': 'Non-anchored report deleted by superuser'
            }
        )
        
        super().delete_model(request, obj)

    # ========== STATUS CHANGE TRACKING ==========
    def save_model(self, request, obj, form, change):
        """Track status changes and create ReportUpdate entries"""
        
        # ========== ANONYMOUS REPORTER PROTECTION ==========
        # If report is anonymous, clear reporter information
        if obj.is_anonymous:
            obj.reporter_name = ""
            obj.reporter_phone = ""
            obj.reporter_email = ""
            obj.user = None
            
            if not change:  # Only show message for new reports
                messages.info(
                    request,
                    f"ℹ️ Report {obj.reference_code or 'new'} marked as anonymous. Reporter identity will be hidden."
                )
        
        if change:  # Only for updates, not new records
            try:
                # Get the original object from database
                original = Report.objects.get(id=obj.id)
                
                # Check if status field changed
                if original.status != obj.status:
                    # Create ReportUpdate history entry
                    update_entry = ReportUpdate.objects.create(
                        report=obj,
                        user=request.user,
                        old_status=original.status,
                        new_status=obj.status,
                        notes=f"Status changed by {request.user.get_full_name() or request.user.username} via admin panel"
                    )
                    
                    # Show success message to admin
                    messages.success(
                        request,
                        f"✓ Report {obj.reference_code} status updated: {original.get_status_display()} → {obj.get_status_display()}"
                    )
                
                # Check if anonymous status changed
                if original.is_anonymous != obj.is_anonymous:
                    if obj.is_anonymous:
                        messages.warning(
                            request,
                            f"⚠️ Report {obj.reference_code} changed to ANONYMOUS. Reporter information cleared."
                        )
                    else:
                        messages.info(
                            request,
                            f"ℹ️ Report {obj.reference_code} changed to PUBLIC. You can now add reporter information."
                        )
            except Report.DoesNotExist:
                pass
        
        # Always save the object
        super().save_model(request, obj, form, change)

    # ========== MEDIA PREVIEW ==========
    def media_file_preview(self, obj):
        if obj.media_file:
            file_url = obj.media_file.url
            file_name = obj.media_file.name.split('/')[-1]
            # Check if it's an image
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            is_image = any(file_name.lower().endswith(ext) for ext in image_extensions)
            
            if is_image:
                return format_html(
                    '<div style="max-width: 300px;"><img src="{}" style="max-width: 100%; height: auto; border-radius: 5px; border: 1px solid #ddd;"/><br><br>'
                    '<a href="{}" target="_blank" style="color: #0066cc; text-decoration: none; font-weight: bold;">View Full Size</a></div>',
                    file_url, file_url
                )
            else:
                return format_html(
                    '<div style="padding: 10px; background: #f0f0f0; border-radius: 5px;">'
                    '<strong>📁 File:</strong> {}<br>'
                    '<a href="{}" target="_blank" style="color: #0066cc; text-decoration: none; font-weight: bold;">Download File</a>'
                    '</div>',
                    file_name, file_url
                )
        elif obj.ipfs_cid:
            return format_html(
                '<div style="padding: 10px; background: #e8f4f8; border-radius: 5px; border: 1px solid #0ea5e9;">'
                '<strong>🌐 IPFS:</strong> {}<br>'
                '<a href="https://ipfs.io/ipfs/{}" target="_blank" style="color: #0066cc; text-decoration: none; font-weight: bold;">View via IPFS</a>'
                '</div>',
                obj.ipfs_cid[:20] + '...', obj.ipfs_cid
            )
        return format_html('<em style="color: #999;">No media file uploaded</em>')
    media_file_preview.short_description = "Evidence Media"
    # -------------------------------
    # JSON EVIDENCE PREVIEW
    # -------------------------------
    def evidence_json_preview(self, obj):
        if obj.evidence_json_cid:
            return format_html('<a href="https://ipfs.io/ipfs/{}" target="_blank">View JSON Evidence</a>', obj.evidence_json_cid)
        return "No Evidence JSON"
    evidence_json_preview.short_description = "Evidence JSON Preview"
    
    # -------------------------------
    # IPFS DISTRIBUTED REPORT PREVIEW
    # -------------------------------
    def ipfs_report_preview(self, obj):
        if obj.ipfs_report_cid:
            return format_html(
                '<div style="background: #f0f9ff; padding: 10px; border-radius: 5px; border: 1px solid #0ea5e9;">'
                '<strong style="color: #0369a1;">🌐 Distributed Storage (1000+ Nodes)</strong><br><br>'
                '<strong>IPFS CID:</strong> <code>{}</code><br><br>'
                '<strong>Gateway URLs:</strong><br>'
                '• <a href="https://ipfs.io/ipfs/{}" target="_blank">ipfs.io Gateway</a><br>'
                '• <a href="https://gateway.pinata.cloud/ipfs/{}" target="_blank">Pinata Gateway</a><br>'
                '• <a href="https://cloudflare-ipfs.com/ipfs/{}" target="_blank">Cloudflare Gateway</a><br><br>'
                '<em style="color: #64748b;">✓ Distributed across 1000+ IPFS nodes globally</em><br>'
                '<em style="color: #64748b;">✓ Content-addressed, immutable storage</em>'
                '</div>',
                obj.ipfs_report_cid, obj.ipfs_report_cid, obj.ipfs_report_cid, obj.ipfs_report_cid
            )
        return format_html(
            '<div style="background: #fef3c7; padding: 10px; border-radius: 5px; border: 1px solid #f59e0b;">'
            '<em>⚠️ Not uploaded to IPFS (created before distributed storage integration)</em>'
            '</div>'
        )
    ipfs_report_preview.short_description = "IPFS Distributed Report"
    evidence_json_preview.short_description = "Evidence JSON Preview"

# ========== REPORT UPDATE HISTORY ADMIN ==========
@admin.register(ReportUpdate)
class ReportUpdateAdmin(admin.ModelAdmin):
    list_display = ('report_ref', 'user', 'status_change', 'created_at')
    list_filter = ('old_status', 'new_status', 'created_at', 'user')
    search_fields = ('report__reference_code', 'notes', 'user__username')
    readonly_fields = ('report', 'user', 'old_status', 'new_status', 'notes', 'created_at')

    def report_ref(self, obj):
        """Show report reference code"""
        return format_html(
            '<a href="/admin/reports/report/{}/change/">{}</a>',
            obj.report.id,
            obj.report.reference_code
        )
    report_ref.short_description = 'Report'

    def status_change(self, obj):
        """Show status change with arrow"""
        old_color = {
            'new': '#0088ce',
            'in_review': '#ffc107',
            'forwarded': '#17a2b8',
            'actioned': '#28a745',
            'closed': '#6c757d',
        }.get(obj.old_status, '#999999')
        
        new_color = {
            'new': '#0088ce',
            'in_review': '#ffc107',
            'forwarded': '#17a2b8',
            'actioned': '#28a745',
            'closed': '#6c757d',
        }.get(obj.new_status, '#999999')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 2px;">{}</span> '
            '→ '
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 2px;">{}</span>',
            old_color, obj.get_old_status_display(),
            new_color, obj.get_new_status_display()
        )
    status_change.short_description = 'Status Change'

# ========== AUDIT LOG ADMIN ==========
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at_short', 'user_display', 'action_badge', 'resource_display', 'ip_address', 'device_short')
    list_filter = ('action', 'created_at', 'user')
    search_fields = ('user__username', 'resource', 'details', 'ip_address')
    readonly_fields = ('user', 'action', 'resource', 'details_display', 'ip_address', 'device_info', 'created_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Action Info', {
            'fields': ('user', 'action', 'resource', 'created_at')
        }),
        ('Details', {
            'fields': ('details_display',)
        }),
        ('Request Info', {
            'fields': ('ip_address', 'device_info')
        }),
    )
    
    def has_add_permission(self, request):
        """Disable manual creation of audit logs"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make audit logs read-only"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs from admin"""
        return request.user.is_superuser  # Only superusers can delete
    
    def created_at_short(self, obj):
        """Compact timestamp"""
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_short.short_description = 'Timestamp'
    created_at_short.admin_order_field = 'created_at'
    
    def user_display(self, obj):
        """Display username or 'System' for null users"""
        if obj.user:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.user.username,
                obj.user.get_full_name() or obj.user.email
            )
        return format_html('<em style="color: #999;">System</em>')
    user_display.short_description = 'User'
    
    def action_badge(self, obj):
        """Color-coded action badge"""
        action_colors = {
            'create_report': '#28a745',
            'update_report': '#ffc107',
            'delete_report': '#dc3545',
            'status_change': '#17a2b8',
            'user_login': '#007bff',
            'user_logout': '#6c757d',
            'user_login_failed': '#dc3545',
            'view_list': '#e0e0e0',
            'view_form': '#f0f0f0',
            'save': '#28a745',
        }
        color = action_colors.get(obj.action, '#999999')
        text_color = 'white' if color not in ['#e0e0e0', '#f0f0f0', '#ffc107'] else '#333'
        
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 4px 8px; border-radius: 3px; font-weight: bold; white-space: nowrap; display: inline-block;">{}</span>',
            color,
            text_color,
            obj.action.replace('_', ' ').title()
        )
    action_badge.short_description = 'Action'
    action_badge.admin_order_field = 'action'
    
    def resource_display(self, obj):
        """Display resource with icon"""
        if 'report' in obj.resource:
            icon = '📄'
        elif 'auth' in obj.resource or 'user' in obj.resource:
            icon = '👤'
        else:
            icon = '📦'
        
        return format_html('{} <code>{}</code>', icon, obj.resource)
    resource_display.short_description = 'Resource'
    
    def device_short(self, obj):
        """Truncated device info"""
        if not obj.device_info:
            return '—'
        
        # Extract browser info
        device = obj.device_info
        if 'Chrome' in device:
            return '🌐 Chrome'
        elif 'Firefox' in device:
            return '🦊 Firefox'
        elif 'Safari' in device:
            return '🧭 Safari'
        elif 'Edge' in device:
            return '🌊 Edge'
        else:
            return '🖥️ ' + device[:20] + '...' if len(device) > 20 else device
    device_short.short_description = 'Device'
    
    def details_display(self, obj):
        """Pretty-print JSON details"""
        import json
        if obj.details:
            formatted = json.dumps(obj.details, indent=2)
            return format_html('<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{}</pre>', formatted)
        return '—'
    details_display.short_description = 'Details'
