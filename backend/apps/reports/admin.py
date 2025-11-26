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
        'reference_code', 'status_badge', 'category', 'priority', 'is_anonymous',
        'reporter_name', 'reporter_phone',
        'created_at', 'updated_at_short'
    )
    list_filter = ('category', 'status', 'priority', 'is_anonymous', 'created_at')
    search_fields = ('reference_code', 'description', 'reporter_name', 'reporter_email')
    readonly_fields = (
        'reference_code', 'ipfs_cid', 'evidence_json_cid', 'evidence_hash',
        'transaction_hash', 'is_hash_anchored', 'verified_on_chain',
        'media_file_preview', 'evidence_json_preview',
        'created_at', 'updated_at'
    )
    fieldsets = (
        ('Report Info', {
            'fields': ('reference_code', 'category', 'description', 'location_description',
                       'latitude', 'longitude', 'status', 'priority')
        }),
        ('Reporter Info', {
            'fields': ('is_anonymous', 'reporter_name', 'reporter_phone', 'reporter_email', 'user')
        }),
        ('Media & IPFS', {
            'fields': ('media_file', 'media_file_preview', 'ipfs_cid', 
                       'evidence_json_preview', 'evidence_json_cid',
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

    # ========== STATUS CHANGE TRACKING ==========
    def save_model(self, request, obj, form, change):
        """Track status changes and create ReportUpdate entries"""
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
            except Report.DoesNotExist:
                pass
        
        # Always save the object
        super().save_model(request, obj, form, change)

    # ========== MEDIA PREVIEW ==========
    def media_file_preview(self, obj):
        if obj.media_file:
            return format_html('<a href="{}" target="_blank">View File</a>', obj.media_file.url)
        elif obj.ipfs_cid:
            return format_html('<a href="https://ipfs.io/ipfs/{}" target="_blank">View IPFS File</a>', obj.ipfs_cid)
        return "No File"
    media_file_preview.short_description = "Media Preview"

    # -------------------------------
    # JSON EVIDENCE PREVIEW
    # -------------------------------
    def evidence_json_preview(self, obj):
        if obj.evidence_json_cid:
            return format_html('<a href="https://ipfs.io/ipfs/{}" target="_blank">View JSON Evidence</a>', obj.evidence_json_cid)
        return "No Evidence JSON"
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
    list_display = ('user', 'action', 'resource', 'ip_address', 'device_info', 'created_at')
    list_filter = ('action', 'resource', 'created_at', 'user')
    search_fields = ('user__username', 'resource', 'details')
    readonly_fields = ('user', 'action', 'resource', 'details', 'ip_address', 'device_info', 'created_at')
