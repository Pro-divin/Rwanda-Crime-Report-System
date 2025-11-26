from django.contrib import admin
from django.utils.html import format_html
import json
from .models import BlockchainAnchor


@admin.register(BlockchainAnchor)
class BlockchainAnchorAdmin(admin.ModelAdmin):
    """
    Admin interface for BlockchainAnchor model.
    Displays blockchain anchoring records with metadata visibility.
    """
    
    list_display = [
        'report_id',
        'status_badge',
        'network',
        'confirmations',
        'evidence_hash_short',
        'tx_hash_short',
        'created_at_short',
        'has_metadata'
    ]
    
    list_filter = ['status', 'network', 'created_at', 'confirmations']
    
    search_fields = ['report_id', 'evidence_hash', 'transaction_hash']
    
    readonly_fields = [
        'report_id',
        'evidence_hash',
        'transaction_hash',
        'created_at',
        'confirmed_at',
        'metadata_display'
    ]
    
    fieldsets = (
        ('Report Information', {
            'fields': ('report_id',)
        }),
        ('Blockchain Data', {
            'fields': (
                'evidence_hash',
                'transaction_hash',
                'status',
                'confirmations',
                'network'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'confirmed_at')
        }),
        ('Block Information', {
            'fields': ('block_number',)
        }),
        ('Metadata (Anchor Data & Timestamps)', {
            'fields': ('metadata_display',),
            'description': 'This section shows the metadata stored for this blockchain anchor, including the anchor data (report info, hashes, timestamps) and submission time.'
        }),
    )
    
    def status_badge(self, obj):
        """Display status with color-coded badge"""
        colors = {
            'pending': '#FFA500',
            'confirmed': '#00AA00',
            'failed': '#FF0000',
        }
        color = colors.get(obj.status, '#999999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def evidence_hash_short(self, obj):
        """Display truncated evidence hash"""
        if obj.evidence_hash:
            return f"{obj.evidence_hash[:16]}...{obj.evidence_hash[-8:]}"
        return "—"
    evidence_hash_short.short_description = 'Evidence Hash'
    
    def tx_hash_short(self, obj):
        """Display truncated transaction hash"""
        if obj.transaction_hash:
            return f"{obj.transaction_hash[:16]}...{obj.transaction_hash[-8:]}"
        return "—"
    tx_hash_short.short_description = 'TX Hash'
    
    def created_at_short(self, obj):
        """Display created_at in a compact format"""
        if obj.created_at:
            return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return "—"
    created_at_short.short_description = 'Created'
    
    def has_metadata(self, obj):
        """Display whether metadata is present"""
        if obj.metadata and obj.metadata != {}:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Yes</span>'
            )
        return format_html(
            '<span style="color: red;">✗ No</span>'
        )
    has_metadata.short_description = 'Has Metadata'
    
    def metadata_display(self, obj):
        """Display metadata as formatted JSON"""
        if obj.metadata:
            json_str = json.dumps(obj.metadata, indent=2)
            # Escape for HTML and wrap in <pre> tag
            return format_html(
                '<pre style="background-color: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; max-height: 400px; max-width: 600px;">{}</pre>',
                json_str
            )
        return format_html(
            '<span style="color: #999;">No metadata (empty dict)</span>'
        )
    metadata_display.short_description = 'Metadata JSON'
