#!/usr/bin/env python
import os
import sys
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reports.models import Report
from apps.blockchain.models import BlockchainAnchor

# Wait another 2 seconds
print("Checking database status...")
time.sleep(2)

# Check RRS-2025-00062
try:
    report = Report.objects.get(reference_code='RRS-2025-00062')
    
    print(f"\n=== RRS-2025-00062 Status ===")
    print(f"IPFS CID: {report.ipfs_cid}")
    print(f"JSON CID: {report.evidence_json_cid}")
    print(f"Evidence Hash: {report.evidence_hash}")
    print(f"TX Hash: {report.transaction_hash}")
    print(f"Is Anchored: {report.is_hash_anchored}")
    print(f"Status: {report.status}")
    
    # Check blockchain anchor
    anchor = BlockchainAnchor.objects.filter(report_id='RRS-2025-00062').first()
    if anchor:
        print(f"\n=== Blockchain Anchor ===")
        print(f"ID: {anchor.id}")
        print(f"TX Hash: {anchor.transaction_hash}")
        print(f"Status: {anchor.status}")
    else:
        print(f"\nNo blockchain anchor found")
    
    # Overall status
    if all([report.ipfs_cid, report.evidence_json_cid, report.evidence_hash, report.transaction_hash]):
        print(f"\n=== SUCCESS: All hashes populated! ===")
    else:
        print(f"\n=== INCOMPLETE: Some hashes missing ===")
        
except Report.DoesNotExist:
    print("Report RRS-2025-00062 not found")
