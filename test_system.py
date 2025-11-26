#!/usr/bin/env python
"""
Rwanda Report System - Complete System Test
Tests all components: Django, Blockchain, IPFS, API endpoints
"""

import os
import sys
import json
import django
import hashlib
from pathlib import Path
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from apps.reports.models import Report
from apps.blockchain.models import BlockchainAnchor
from apps.blockchain.cardano_utils import CardanoEvidenceAnchoring


class RRSSystemTest:
    """Complete system test suite"""
    
    def __init__(self):
        self.client = Client()
        self.results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "tests": []
        }
    
    def test_django_setup(self):
        """Test Django is properly configured"""
        print("\n" + "="*60)
        print("🧪 TEST 1: Django Setup")
        print("="*60)
        
        try:
            # Check database connection
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            print("✅ Database connection OK")
            
            # Check admin site
            response = self.client.get('/admin/login/')
            assert response.status_code == 200
            print("✅ Admin site accessible")
            
            # Check installed apps
            from django.conf import settings
            required_apps = [
                'apps.reports',
                'apps.blockchain',
                'apps.users',
                'rest_framework',
            ]
            # allow flexible matching (e.g. 'apps.users.apps.UsersConfig')
            for app in required_apps:
                found = any(app in installed for installed in settings.INSTALLED_APPS)
                assert found, f"Required app {app} not found in INSTALLED_APPS"
            print(f"✅ All required apps installed")
            
            self.results["passed"] += 1
            
        except Exception as e:
            print(f"❌ Django setup failed: {e}")
            self.results["failed"] += 1
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n" + "="*60)
        print("🧪 TEST 2: API Endpoints")
        print("="*60)
        
        try:
            # Test homepage
            response = self.client.get('/')
            assert response.status_code == 200
            print("✅ Homepage accessible")
            
            # Test submit page
            response = self.client.get('/report/submit/')
            assert response.status_code == 200
            print("✅ Submit page accessible")
            
            # Test status page
            response = self.client.get('/report/status/')
            assert response.status_code == 200
            print("✅ Status page accessible")
            
            self.results["passed"] += 1
            
        except Exception as e:
            print(f"❌ API endpoints failed: {e}")
            self.results["failed"] += 1
    
    def test_report_submission(self):
        """Test report submission and blockchain anchoring"""
        print("\n" + "="*60)
        print("🧪 TEST 3: Report Submission & Blockchain Anchoring")
        print("="*60)
        
        try:
            # Create test data
            test_report = {
                'category': 'theft',
                'description': 'Test incident - Security verification',
                'location_description': 'Downtown Kigali',
                'latitude': '-1.943419',
                'longitude': '29.873888',
                'is_anonymous': True,
            }
            
            # Submit report via API
            response = self.client.post(
                '/api/report/submit/',
                data=test_report,
                content_type='application/x-www-form-urlencoded'
            )
            
            print(f"Response status: {response.status_code}")
            if response.status_code == 201:
                data = response.json()
                reference_code = data.get('reference_code')
                print(f"✅ Report submitted: {reference_code}")
                
                # Verify report in database
                report = Report.objects.get(reference_code=reference_code)
                print(f"✅ Report saved in database")
                
                # Check blockchain anchor
                import time
                time.sleep(1)  # Wait for async processing
                
                try:
                    anchor = BlockchainAnchor.objects.get(report_id=reference_code)
                    print(f"✅ Blockchain anchor created")
                    print(f"   - Evidence hash: {anchor.evidence_hash[:16]}...")
                    print(f"   - Status: {anchor.status}")
                except BlockchainAnchor.DoesNotExist:
                    print(f"⚠️  Blockchain anchor not yet created (async processing)")
                
                self.results["passed"] += 1
            else:
                print(f"❌ Report submission failed: {response.content}")
                self.results["failed"] += 1
                
        except Exception as e:
            print(f"❌ Report submission test failed: {e}")
            self.results["failed"] += 1
    
    def test_blockchain_utils(self):
        """Test blockchain utility functions"""
        print("\n" + "="*60)
        print("🧪 TEST 4: Blockchain Utilities")
        print("="*60)
        
        try:
            cardano = CardanoEvidenceAnchoring(network="preview")
            
            # Test evidence hash generation
            test_data = {
                "report_id": "RRS-2025-00001",
                "category": "theft",
                "description": "Test"
            }
            
            evidence_hash = cardano.generate_evidence_hash(test_data)
            assert len(evidence_hash) == 64  # SHA-256 hex is 64 chars
            assert all(c in '0123456789abcdef' for c in evidence_hash)
            print(f"✅ Evidence hash generation works")
            print(f"   Hash: {evidence_hash}")
            
            # Test anchor transaction creation
            result = cardano.create_anchor_transaction(
                report_id="RRS-2025-00001",
                evidence_hash=evidence_hash,
                category="theft",
                is_anonymous=True
            )
            
            assert result["success"]
            assert result["tx_hash"]
            assert result["status"] == "pending"
            print(f"✅ Anchor transaction creation works")
            print(f"   TX Hash: {result['tx_hash'][:16]}...")
            
            # Test evidence verification
            verify_result = cardano.verify_evidence_on_chain(
                report_id="RRS-2025-00001",
                evidence_hash=evidence_hash
            )
            
            assert verify_result["verified"]
            print(f"✅ Evidence verification works")
            
            # Test IPFS submission
            ipfs_cid = cardano.submit_to_ipfs(test_data)
            assert ipfs_cid.startswith("Qm")
            print(f"✅ IPFS submission works")
            print(f"   CID: {ipfs_cid}")
            
            self.results["passed"] += 1
            
        except Exception as e:
            print(f"❌ Blockchain utilities test failed: {e}")
            self.results["failed"] += 1
    
    def test_models(self):
        """Test database models"""
        print("\n" + "="*60)
        print("🧪 TEST 5: Database Models")
        print("="*60)
        
        try:
            # Test Report model
            report = Report(
                category='kidnapping',
                description='Test kidnapping report',
                is_anonymous=False,
                reporter_name='Test User'
            )
            report.save()
            
            # Check reference code generation
            assert report.reference_code
            assert report.reference_code.startswith('RRS-')
            print(f"✅ Report model works")
            print(f"   Reference: {report.reference_code}")
            
            # Test BlockchainAnchor model
            anchor = BlockchainAnchor(
                report_id=report.reference_code,
                evidence_hash='a' * 64,
                network='preview'
            )
            anchor.save()
            
            assert anchor.id
            assert anchor.status == BlockchainAnchor.Status.PENDING
            print(f"✅ BlockchainAnchor model works")
            
            # Test mark_confirmed
            anchor.mark_confirmed('tx_hash_123', block_number=1000)
            assert anchor.confirmations == 1
            assert anchor.status == BlockchainAnchor.Status.CONFIRMED
            print(f"✅ Mark confirmed works")
            
            # Cleanup
            anchor.delete()
            report.delete()
            
            self.results["passed"] += 1
            
        except Exception as e:
            print(f"❌ Models test failed: {e}")
            self.results["failed"] += 1
    
    def test_serializers(self):
        """Test DRF serializers"""
        print("\n" + "="*60)
        print("🧪 TEST 6: REST Serializers")
        print("="*60)
        
        try:
            from apps.reports.serializers import ReportSerializer
            
            # Create test report
            test_data = {
                'category': 'corruption',
                'description': 'Test corruption case',
                'location_description': 'Kigali City',
                'is_anonymous': True,
            }
            
            serializer = ReportSerializer(data=test_data)
            assert serializer.is_valid()
            report = serializer.save()
            
            print(f"✅ ReportSerializer validation works")
            
            # Test serializing
            serialized_data = ReportSerializer(report).data
            assert serialized_data['reference_code']
            assert serialized_data['category'] == 'corruption'
            print(f"✅ ReportSerializer serialization works")
            
            # Cleanup
            report.delete()
            
            self.results["passed"] += 1
            
        except Exception as e:
            print(f"❌ Serializers test failed: {e}")
            self.results["failed"] += 1
    
    def test_aiken_contract(self):
        """Test Aiken smart contract"""
        print("\n" + "="*60)
        print("🧪 TEST 7: Aiken Smart Contract")
        print("="*60)
        
        try:
            contract_dir = Path(__file__).parent / 'blockchain' / 'rrs-contract'
            plutus_file = contract_dir / 'build' / 'plutus.json'
            
            if plutus_file.exists():
                with open(plutus_file) as f:
                    plutus = json.load(f)
                print(f"✅ Plutus contract file exists")
                print(f"   Validators: {len(plutus.get('validators', []))}")
            else:
                print(f"⚠️  Plutus contract not compiled. Run 'aiken build'")
                self.results["warnings"] += 1
            
            # Check contract source
            lib_ak = contract_dir / 'lib' / 'lib.ak'
            if lib_ak.exists():
                with open(lib_ak) as f:
                    content = f.read()
                required_functions = [
                    'validate_sha256_hash',
                    'validate_report_id',
                    'validate_category',
                    'validate_anchor_params'
                ]
                
                for func in required_functions:
                    if func in content:
                        print(f"✅ Function '{func}' found in contract")
                    else:
                        print(f"❌ Function '{func}' missing")
                        self.results["failed"] += 1
            
            self.results["passed"] += 1
            
        except Exception as e:
            print(f"❌ Contract test failed: {e}")
            self.results["failed"] += 1
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*80)
        print("🚀 RWANDA REPORT SYSTEM - COMPLETE SYSTEM TEST")
        print("="*80)
        
        self.test_django_setup()
        self.test_api_endpoints()
        self.test_blockchain_utils()
        self.test_models()
        self.test_serializers()
        self.test_aiken_contract()
        self.test_report_submission()
        
        # Print summary
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"⚠️  Warnings: {self.results['warnings']}")
        print("="*80)
        
        if self.results['failed'] == 0:
            print("\n🎉 ALL TESTS PASSED! System is ready for deployment.")
            return 0
        else:
            print(f"\n⚠️  {self.results['failed']} tests failed. Review above for details.")
            return 1


if __name__ == '__main__':
    tester = RRSSystemTest()
    sys.exit(tester.run_all_tests())
