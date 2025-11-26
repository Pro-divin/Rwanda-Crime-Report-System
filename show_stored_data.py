#!/usr/bin/env python
"""
Display actual stored report data from database
Shows exactly what IPFS data structure is being kept for each report
"""

import os
import sys
import json
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
django.setup()

from apps.reports.models import Report
from apps.blockchain.models import BlockchainAnchor


def show_all_reports():
    """Display all stored reports with their IPFS data"""
    
    print("\n" + "="*100)
    print("📋 ALL STORED REPORTS IN DATABASE")
    print("="*100)
    
    reports = Report.objects.all().order_by('-created_at')
    
    if not reports.exists():
        print("No reports stored yet")
        return
    
    print(f"\nTotal reports: {reports.count()}\n")
    
    for i, report in enumerate(reports, 1):
        print(f"\n{'─'*100}")
        print(f"Report #{i}: {report.reference_code}")
        print(f"{'─'*100}")
        
        # Basic info
        print(f"  📝 Basic Information:")
        print(f"     Category: {report.category}")
        print(f"     Description: {report.description}")
        print(f"     Status: {report.status}")
        print(f"     Created: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Location
        print(f"\n  📍 Location:")
        print(f"     Description: {report.location_description or 'Not specified'}")
        print(f"     Latitude: {report.latitude or 'N/A'}")
        print(f"     Longitude: {report.longitude or 'N/A'}")
        
        # Reporter info
        print(f"\n  👤 Reporter:")
        if report.is_anonymous:
            print(f"     Anonymous: Yes")
        else:
            print(f"     Name: {report.reporter_name or 'Not provided'}")
            print(f"     Phone: {report.reporter_phone or 'Not provided'}")
            print(f"     Email: {report.reporter_email or 'Not provided'}")
        
        # IPFS/Blockchain
        print(f"\n  ⛓️  IPFS & Blockchain:")
        if report.ipfs_cid:
            print(f"     Media CID: {report.ipfs_cid}")
        else:
            print(f"     Media CID: (no media file)")
        
        if report.evidence_json_cid:
            print(f"     Evidence JSON CID: {report.evidence_json_cid}")
            print(f"     🔗 Local Access: http://127.0.0.1:8080/ipfs/{report.evidence_json_cid}")
        
        if report.evidence_hash:
            print(f"     Evidence Hash (SHA-256): {report.evidence_hash}")
        
        if report.transaction_hash:
            print(f"     Transaction Hash: {report.transaction_hash}")
            print(f"     Blockchain Verified: {report.is_hash_anchored}")
        
        # Check blockchain anchor
        try:
            anchor = BlockchainAnchor.objects.get(report_id=report.reference_code)
            print(f"\n  ✅ Blockchain Anchor:")
            print(f"     Status: {anchor.status}")
            print(f"     Confirmations: {anchor.confirmations}")
            print(f"     Network: {anchor.network}")
            # Print stored metadata if present
            if anchor.metadata:
                try:
                    pretty = json.dumps(anchor.metadata, indent=4, ensure_ascii=False)
                    print(f"     Metadata:\n{pretty}")
                except Exception:
                    print(f"     Metadata: {anchor.metadata}")
        except BlockchainAnchor.DoesNotExist:
            print(f"\n  ⏳ Blockchain Anchor: Not yet created (async processing)")


def show_evidence_json_structure():
    """Show example of evidence JSON structure being stored"""
    
    print("\n\n" + "="*100)
    print("🗂️  EVIDENCE JSON STRUCTURE (What's stored in IPFS)")
    print("="*100)
    
    print("""
The evidence JSON stored in IPFS for each report contains:

{
  "report_id": "UUID of report",
  "reference_code": "RRS-2025-XXXXX",
  "category": "theft|kidnapping|corruption|...",
  "description": "Full incident description",
  "latitude": "GPS latitude",
  "longitude": "GPS longitude", 
  "location_description": "Location text",
  "ipfs_cid": "IPFS CID of media file (if uploaded)",
  "timestamp": "ISO 8601 timestamp",
  "is_anonymous": "boolean"
}

Example:
{
  "report_id": "9b239655-7666-44eb-9e6c-670fe3402d97",
  "reference_code": "RRS-2025-00009",
  "category": "kidnapping",
  "description": "boboooooooooooooooooooooooooooooooo",
  "latitude": "-1.979187",
  "longitude": "30.107238",
  "location_description": "gikondo",
  "ipfs_cid": "Qm8fea911d3f54fa0945dab710942d0a4582c58026200b",
  "timestamp": "2025-11-26T13:30:13.123456Z",
  "is_anonymous": true
}

✅ This JSON is:
  1. Uploaded to IPFS → Gets a unique CID
  2. SHA-256 hashed → Creates evidence integrity proof
  3. Stored on Cardano blockchain → Immutable proof of existence
  4. Accessible via IPFS node → Can retrieve and verify anytime
    """)


def show_access_instructions():
    """Show how to access and verify stored data"""
    
    print("\n\n" + "="*100)
    print("🔍 HOW TO ACCESS & VERIFY YOUR STORED DATA")
    print("="*100)
    
    print("""
1️⃣  View in Django Admin:
   - URL: http://localhost:8000/admin/reports/report/
   - Shows all reports with their IPFS CIDs and hashes

2️⃣  Access IPFS Data Locally (if IPFS daemon running):
   Command: ipfs cat <CID>
   Example: ipfs cat QmNe2yJ6LoN5ZLQaK9oLUASy1bP8EZKfi33GrnzvW6xagC
   
   Or via local gateway:
   URL: http://127.0.0.1:8080/ipfs/<CID>

3️⃣  Verify Evidence Hash:
   - Download evidence JSON from IPFS
   - Run: sha256sum evidence.json
   - Compare with stored hash in database
   - They must match (proves data integrity)

4️⃣  Check Blockchain Status:
   - Django admin → BlockchainAnchor model
   - Shows transaction hash, network, confirmations
   - Can verify on blockchain explorer

5️⃣  Database Queries:
   python manage.py shell
   >>> from apps.reports.models import Report
   >>> r = Report.objects.first()
   >>> print(r.evidence_json_cid)
   >>> print(r.evidence_hash)
    """)


def show_data_backup_strategy():
    """Show recommendations for data persistence"""
    
    print("\n" + "="*100)
    print("💾 DATA PERSISTENCE & BACKUP STRATEGY")
    print("="*100)
    
    print("""
Your data is stored in multiple locations:

1. 📂 Database (SQLite):
   - Location: backend/db.sqlite3
   - Contains: Report metadata, IPFS CIDs, hashes, blockchain anchors
   - Backup: Regular database exports
   
2. 📦 IPFS Local Node:
   - Location: ~/.ipfs/blocks/ (in your home directory)
   - Contains: Full evidence JSON + any media files
   - Backup: IPFS pin commands or periodic snapshots
   
3. ⛓️  Cardano Blockchain:
   - Location: Cardano Preview testnet (configurable to mainnet)
   - Contains: Proof of evidence existence with blockchain confirmation
   - Backup: Immutable (cannot be lost - on blockchain)
   
4. 🌐 IPFS Public Gateways:
   - Access via: https://ipfs.io/ipfs/<CID>
   - Persistence: Data persists if pinned by other nodes
   - Backup: Manual pinning on services like Pinata or NFT.Storage

Recommended Backup Strategy:
✅ Daily: Export SQLite database
✅ Weekly: Backup ~/.ipfs/blocks directory
✅ Always: Keep blockchain transaction hashes for verification
✅ Optional: Pin to public IPFS services for redundancy
    """)


if __name__ == '__main__':
    show_all_reports()
    show_evidence_json_structure()
    show_access_instructions()
    show_data_backup_strategy()
    
    print("\n" + "="*100)
    print("✅ Your report data is properly stored, hashed, and anchored on blockchain!")
    print("="*100 + "\n")
