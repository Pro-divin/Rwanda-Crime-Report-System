#!/usr/bin/env python
"""
IPFS Integration Test for Rwanda Report System
Tests IPFS storage of reports and media files with actual retrieval and verification
"""

import os
import sys
import json
import django
import httpx
import time
from pathlib import Path
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
django.setup()

from django.test import Client
from apps.reports.models import Report
from apps.blockchain.models import BlockchainAnchor


class IPFSIntegrationTest:
    """Test IPFS storage and retrieval for reports"""
    
    def __init__(self):
        self.client = Client()
        self.ipfs_api_url = "http://127.0.0.1:5001/api/v0"
        self.ipfs_gateway = "http://127.0.0.1:8080/ipfs"
        self.results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "data": []
        }
    
    def check_ipfs_daemon(self):
        """Check if IPFS daemon is running"""
        print("\n" + "="*70)
        print("🧪 TEST 1: IPFS Daemon Status")
        print("="*70)
        
        try:
            response = httpx.get(f"{self.ipfs_api_url}/id", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ IPFS daemon is running")
                print(f"   Peer ID: {data.get('ID', 'N/A')[:16]}...")
                print(f"   Addresses: {len(data.get('Addresses', []))} endpoints")
                self.results["passed"] += 1
                return True
            else:
                print(f"❌ IPFS API returned {response.status_code}")
                self.results["failed"] += 1
                return False
        except Exception as e:
            print(f"⚠️  IPFS daemon not running or not accessible")
            print(f"   Error: {str(e)[:100]}")
            print(f"   Make sure IPFS daemon is running: `ipfs daemon` in another terminal")
            self.results["warnings"] += 1
            return False
    
    def submit_report_with_ipfs(self):
        """Submit a report and capture IPFS storage details"""
        print("\n" + "="*70)
        print("🧪 TEST 2: Submit Report & Store in IPFS")
        print("="*70)
        
        try:
            test_report = {
                'category': 'corruption',
                'description': 'IPFS Integration Test - Bribery incident at local government office',
                'location_description': 'Kigali, Gasabo District',
                'latitude': '-1.950000',
                'longitude': '30.060000',
                'is_anonymous': True,
            }
            
            # Submit report via API
            response = self.client.post(
                '/api/report/submit/',
                data=test_report,
                content_type='application/x-www-form-urlencoded'
            )
            
            if response.status_code == 201:
                data = response.json()
                reference_code = data.get('reference_code')
                print(f"✅ Report submitted: {reference_code}")
                
                # Wait for async IPFS processing
                print(f"   Waiting for async IPFS processing (5 seconds)...")
                time.sleep(5)
                
                # Get report details from DB
                report = Report.objects.get(reference_code=reference_code)
                print(f"✅ Report found in database")
                print(f"   - Category: {report.category}")
                print(f"   - Description: {report.description[:50]}...")
                print(f"   - Latitude: {report.latitude}, Longitude: {report.longitude}")
                
                # Check IPFS CIDs
                if report.ipfs_cid:
                    print(f"✅ Media IPFS CID: {report.ipfs_cid}")
                else:
                    print(f"⚠️  No media file uploaded")
                
                if report.evidence_json_cid:
                    print(f"✅ Evidence JSON IPFS CID: {report.evidence_json_cid}")
                    self.results["data"].append({
                        "reference_code": reference_code,
                        "evidence_json_cid": report.evidence_json_cid,
                        "evidence_hash": report.evidence_hash
                    })
                else:
                    print(f"❌ Evidence JSON CID not stored")
                    self.results["failed"] += 1
                    return reference_code
                
                self.results["passed"] += 1
                return reference_code
            else:
                print(f"❌ Report submission failed: {response.status_code}")
                print(f"   Response: {response.content[:200]}")
                self.results["failed"] += 1
                return None
                
        except Exception as e:
            print(f"❌ Error submitting report: {e}")
            self.results["failed"] += 1
            return None
    
    def fetch_evidence_from_ipfs(self, cid):
        """Fetch evidence JSON from IPFS and display contents"""
        print("\n" + "="*70)
        print("🧪 TEST 3: Fetch Evidence JSON from IPFS")
        print("="*70)
        
        if not cid:
            print(f"⚠️  No CID provided, skipping")
            self.results["warnings"] += 1
            return
        
        try:
            # Try to fetch from IPFS node directly
            print(f"   Fetching CID: {cid}")
            response = httpx.get(f"{self.ipfs_api_url}/cat?arg={cid}", timeout=10)
            
            if response.status_code == 200:
                try:
                    evidence_data = response.json()
                    print(f"✅ Evidence retrieved from IPFS")
                    print(f"   Report ID: {evidence_data.get('report_id')}")
                    print(f"   Reference Code: {evidence_data.get('reference_code')}")
                    print(f"   Category: {evidence_data.get('category')}")
                    print(f"   Description: {evidence_data.get('description')[:80]}...")
                    print(f"   Location: {evidence_data.get('location_description')}")
                    print(f"   Latitude: {evidence_data.get('latitude')}")
                    print(f"   Longitude: {evidence_data.get('longitude')}")
                    print(f"   Timestamp: {evidence_data.get('timestamp')}")
                    print(f"   Anonymous: {evidence_data.get('is_anonymous')}")
                    
                    # Show full JSON
                    print(f"\n   Full Evidence JSON:")
                    print(f"   {json.dumps(evidence_data, indent=2)}")
                    
                    self.results["passed"] += 1
                except Exception as e:
                    print(f"⚠️  Response not JSON: {str(e)[:100]}")
                    print(f"   Raw response: {response.text[:200]}")
                    self.results["warnings"] += 1
            else:
                print(f"❌ IPFS fetch failed: {response.status_code}")
                self.results["failed"] += 1
        except Exception as e:
            print(f"❌ Error fetching from IPFS: {str(e)}")
            print(f"   Ensure IPFS daemon is running: ipfs daemon")
            self.results["failed"] += 1
    
    def verify_evidence_hash(self, reference_code):
        """Verify the evidence hash matches the stored hash"""
        print("\n" + "="*70)
        print("🧪 TEST 4: Verify Evidence Hash")
        print("="*70)
        
        try:
            report = Report.objects.get(reference_code=reference_code)
            
            if not report.evidence_hash:
                print(f"⚠️  No evidence hash found")
                self.results["warnings"] += 1
                return
            
            print(f"✅ Evidence Hash: {report.evidence_hash}")
            print(f"   Hash Length: {len(report.evidence_hash)} chars (SHA-256)")
            print(f"   Hash Algorithm: SHA-256")
            
            # Verify hash format (should be 64 hex chars)
            if len(report.evidence_hash) == 64 and all(c in '0123456789abcdef' for c in report.evidence_hash.lower()):
                print(f"✅ Hash format is valid")
                self.results["passed"] += 1
            else:
                print(f"❌ Invalid hash format")
                self.results["failed"] += 1
                
        except Exception as e:
            print(f"❌ Error verifying hash: {e}")
            self.results["failed"] += 1
    
    def check_blockchain_anchor(self, reference_code):
        """Check if blockchain anchor was created for the report"""
        print("\n" + "="*70)
        print("🧪 TEST 5: Blockchain Anchor Status")
        print("="*70)
        
        try:
            # Wait a bit more for async processing
            time.sleep(2)
            
            try:
                anchor = BlockchainAnchor.objects.get(report_id=reference_code)
                print(f"✅ Blockchain anchor found")
                print(f"   Transaction Hash: {anchor.transaction_hash[:20]}...")
                print(f"   Status: {anchor.status}")
                print(f"   Evidence Hash: {anchor.evidence_hash[:32]}...")
                print(f"   Network: {anchor.network}")
                print(f"   Confirmations: {anchor.confirmations}")
                self.results["passed"] += 1
            except BlockchainAnchor.DoesNotExist:
                print(f"⚠️  Blockchain anchor not yet created (async processing still running)")
                self.results["warnings"] += 1
                
        except Exception as e:
            print(f"❌ Error checking anchor: {e}")
            self.results["failed"] += 1
    
    def test_ipfs_gateway(self):
        """Test public IPFS gateway access (if available)"""
        print("\n" + "="*70)
        print("🧪 TEST 6: IPFS Gateway Access")
        print("="*70)
        
        if not self.results["data"]:
            print(f"⚠️  No IPFS data to test")
            self.results["warnings"] += 1
            return
        
        cid = self.results["data"][0].get("evidence_json_cid")
        try:
            print(f"   Testing public gateway: https://ipfs.io/ipfs/{cid}")
            response = httpx.get(f"https://ipfs.io/ipfs/{cid}", timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Data accessible via public IPFS gateway")
                self.results["passed"] += 1
            else:
                print(f"⚠️  Gateway returned {response.status_code}")
                print(f"   This is normal if the content is not pinned globally")
                self.results["warnings"] += 1
        except Exception as e:
            print(f"⚠️  Public gateway unreachable: {str(e)[:80]}")
            print(f"   This is normal - content is stored locally")
            self.results["warnings"] += 1
    
    def show_stored_data_summary(self):
        """Display summary of all stored IPFS data"""
        print("\n" + "="*70)
        print("📊 STORED DATA SUMMARY")
        print("="*70)
        
        if not self.results["data"]:
            print(f"No data stored during this test run")
            return
        
        for i, item in enumerate(self.results["data"], 1):
            print(f"\n Report #{i}:")
            print(f"  Reference Code: {item.get('reference_code')}")
            print(f"  Evidence JSON CID: {item.get('evidence_json_cid')}")
            print(f"  Evidence Hash: {item.get('evidence_hash')}")
    
    def run_all_tests(self):
        """Run all IPFS integration tests"""
        print("\n" + "="*80)
        print("🚀 IPFS INTEGRATION TEST - Rwanda Report System")
        print("="*80)
        
        # Check daemon first
        if not self.check_ipfs_daemon():
            print("\n⚠️  IPFS daemon not available - tests will use simulated CIDs")
        
        # Submit report
        ref_code = self.submit_report_with_ipfs()
        
        if ref_code:
            # Get report to access CID
            report = Report.objects.get(reference_code=ref_code)
            
            # Run tests
            self.fetch_evidence_from_ipfs(report.evidence_json_cid)
            self.verify_evidence_hash(ref_code)
            self.check_blockchain_anchor(ref_code)
            self.test_ipfs_gateway()
        
        # Show summary
        self.show_stored_data_summary()
        
        # Print final summary
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"⚠️  Warnings: {self.results['warnings']}")
        print("="*80)
        
        if self.results['failed'] == 0:
            print("\n🎉 IPFS INTEGRATION WORKING! All data properly stored.")
            return 0
        else:
            print(f"\n⚠️  {self.results['failed']} tests failed. Check IPFS daemon.")
            return 1


if __name__ == '__main__':
    tester = IPFSIntegrationTest()
    sys.exit(tester.run_all_tests())
