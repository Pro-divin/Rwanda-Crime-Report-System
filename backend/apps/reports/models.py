from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

# ---------------------------------------------------------
# CHOICE ENUMS
# ---------------------------------------------------------
class ReportCategory(models.TextChoices):
    THEFT = 'theft', 'Theft'
    KIDNAPPING = 'kidnapping', 'Kidnapping'
    CORRUPTION = 'corruption', 'Corruption'
    HOUSE_FIRE = 'house_fire', 'House Fire'
    ROAD_ACCIDENT = 'road_accident', 'Road Accident'
    OTHER = 'other', 'Other'

class ReportStatus(models.TextChoices):
    NEW = 'new', 'New'
    IN_REVIEW = 'in_review', 'In Review'
    FORWARDED = 'forwarded', 'Forwarded'
    ACTIONED = 'actioned', 'Actioned'
    CLOSED = 'closed', 'Closed'

# ---------------------------------------------------------
# MAIN REPORT MODEL
# ---------------------------------------------------------
class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_code = models.CharField(max_length=20, unique=True, editable=False)

    category = models.CharField(max_length=20, choices=ReportCategory.choices)
    description = models.TextField()
    location_description = models.CharField(max_length=255, blank=True, default="")

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_anonymous = models.BooleanField(default=False)
    reporter_name = models.CharField(max_length=100, blank=True, default="")
    reporter_phone = models.CharField(max_length=15, blank=True, default="")
    reporter_email = models.EmailField(blank=True, default="")

    media_file = models.FileField(upload_to='reports/media/', blank=True, null=True)
    media_thumbnail = models.ImageField(upload_to='reports/thumbnails/', blank=True, null=True)

    ipfs_cid = models.CharField(max_length=100, blank=True, null=True)
    evidence_json_cid = models.CharField(max_length=100, blank=True, null=True)

    evidence_hash = models.CharField(max_length=64, blank=True, null=True)
    transaction_hash = models.CharField(max_length=64, blank=True, null=True)
    is_hash_anchored = models.BooleanField(default=False)
    verified_on_chain = models.BooleanField(default=False)

    blockchain_metadata = models.JSONField(default=dict, blank=True)

    status = models.CharField(max_length=20, choices=ReportStatus.choices, default=ReportStatus.NEW)
    priority = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference_code']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def save(self, *args, **kwargs):
        """Generate reference code automatically."""
        if not self.reference_code:
            self.reference_code = self.generate_reference_code()
        super().save(*args, **kwargs)

    def generate_reference_code(self):
        """Generate unique sequential code: RRS-2025-00001"""
        year = timezone.now().year
        prefix = f"RRS-{year}-"
        last = Report.objects.filter(reference_code__startswith=prefix).order_by("-created_at").first()
        sequence = 1
        if last:
            try:
                sequence = int(last.reference_code.split('-')[-1]) + 1
            except ValueError:
                sequence = Report.objects.filter(created_at__year=year).count() + 1
        return f"{prefix}{sequence:05d}"

    def __str__(self):
        return f"{self.reference_code} - {self.get_category_display()}"

    @property
    def media_ipfs_url(self):
        """Public IPFS gateway link for media."""
        if self.ipfs_cid:
            return f"https://ipfs.io/ipfs/{self.ipfs_cid}"
        return None

    @property
    def evidence_ipfs_url(self):
        """Public IPFS gateway link for JSON evidence."""
        if self.evidence_json_cid:
            return f"https://ipfs.io/ipfs/{self.evidence_json_cid}"
        return None

# ---------------------------------------------------------
# REPORT UPDATE HISTORY
# ---------------------------------------------------------
class ReportUpdate(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='updates')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    old_status = models.CharField(max_length=20, choices=ReportStatus.choices)
    new_status = models.CharField(max_length=20, choices=ReportStatus.choices)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

# ---------------------------------------------------------
# AUDIT LOG
# ---------------------------------------------------------
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    resource = models.CharField(max_length=100)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
