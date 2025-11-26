from django.db import models
from django.utils import timezone
import uuid


class BlockchainAnchor(models.Model):
    """
    Records evidence hash anchoring on Cardano blockchain
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUBMITTED = 'submitted', 'Submitted'
        CONFIRMED = 'confirmed', 'Confirmed'
        FAILED = 'failed', 'Failed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_id = models.CharField(max_length=20, unique=True, db_index=True)
    
    evidence_hash = models.CharField(max_length=64, db_index=True)
    ipfs_cid = models.CharField(max_length=100, blank=True, null=True)
    
    transaction_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    block_number = models.IntegerField(blank=True, null=True)
    confirmations = models.IntegerField(default=0)
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    
    network = models.CharField(max_length=20, default='preview')
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['report_id']),
            models.Index(fields=['evidence_hash']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_hash']),
        ]
    
    def __str__(self):
        return f"{self.report_id} - {self.status}"
    
    def mark_confirmed(self, tx_hash: str, block_number: int = None):
        """Mark this anchor as confirmed on blockchain"""
        self.transaction_hash = tx_hash
        self.block_number = block_number
        self.confirmations = 1
        self.status = self.Status.CONFIRMED
        self.confirmed_at = timezone.now()
        self.save()

