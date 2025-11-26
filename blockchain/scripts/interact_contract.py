#!/usr/bin/env python3
"""
Script to interact with deployed RRS smart contract
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path

class RRSContractClient:
    def __init__(self, deployment_info_file=None):
        if deployment_info_file is None:
            deployment_info_file = Path(__file__).parent / "deployment_info.json"
        
        self.deployment_info = self.load_deployment_info(deployment_info_file)
        self.contract_address = self.deployment_info.get("address", "")
        self.network = self.deployment_info.get("network", "preview")
    
    def load_deployment_info(self, file_path):
        """Load deployment information"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Deployment info not found. Run deploy_contract.py first.")
            return {}
    
    def create_evidence_hash(self, report_data):
        """Create SHA-256 hash of evidence JSON"""
        evidence_json = json.dumps(report_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(evidence_json.encode()).hexdigest()
    
    def anchor_report(self, report_id, evidence_hash, category, is_anonymous):
        """Anchor a report on the blockchain"""
        print(f"Anchoring report {report_id} on blockchain...")
        
        # Simulate blockchain transaction
        # In production, this would build and submit an actual Cardano transaction
        
        timestamp = int(datetime.now().timestamp() * 1000)  # milliseconds
        
        transaction_data = {
            "report_id": report_id,
            "evidence_hash": evidence_hash,
            "category": category,
            "is_anonymous": is_anonymous,
            "timestamp": timestamp,
            "contract_address": self.contract_address,
            "action": "anchor"
        }
        
        # Simulate transaction hash
        tx_hash = hashlib.sha256(
            f"{report_id}{evidence_hash}{timestamp}".encode()
        ).hexdigest()
        
        print(f"✅ Report anchored successfully!")
        print(f"   Transaction: {tx_hash}")
        print(f"   Contract: {self.contract_address}")
        
        return {
            "success": True,
            "transaction_hash": tx_hash,
            "timestamp": timestamp,
            "contract_address": self.contract_address
        }
    
    def verify_report(self, report_id, evidence_hash):
        """Verify a report on the blockchain"""
        print(f"Verifying report {report_id}...")
        
        # Simulate blockchain query
        # In production, this would query the blockchain for the report
        
        # For demo purposes, we'll assume verification succeeds
        # In real implementation, this would check the actual blockchain state
        
        verification_result = {
            "verified": True,
            "report_id": report_id,
            "evidence_hash": evidence_hash,
            "on_chain_hash": evidence_hash,  # Would be fetched from chain
            "matches": True,
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
        
        if verification_result["matches"]:
            print("✅ Report verified successfully - evidence hash matches!")
        else:
            print("❌ Report verification failed - evidence hash mismatch!")
        
        return verification_result
    
    def get_report_status(self, report_id):
        """Get report status from blockchain"""
        print(f"Fetching status for report {report_id}...")
        
        # Simulate blockchain query
        status_data = {
            "report_id": report_id,
            "anchored": True,
            "transaction_count": 1,
            "first_seen": "2024-01-01T12:00:00Z",
            "last_verified": "2024-01-01T12:05:00Z"
        }
        
        return status_data

def main():
    client = RRSContractClient()
    
    print("🔗 RRS Contract Interaction Demo")
    print("=" * 40)
    
    # Demo data
    report_data = {
        "report_id": "RRS-2024-00123",
        "category": "theft",
        "description": "Stolen vehicle from parking lot",
        "location": {
            "latitude": -1.9403,
            "longitude": 29.8739
        },
        "timestamp": "2024-01-01T12:00:00Z",
        "media_cid": "QmXyz...",
        "anonymity_flag": True
    }
    
    # Create evidence hash
    evidence_hash = client.create_evidence_hash(report_data)
    print(f"Evidence Hash: {evidence_hash}")
    
    # Anchor report
    result = client.anchor_report(
        report_id=report_data["report_id"],
        evidence_hash=evidence_hash,
        category=report_data["category"],
        is_anonymous=report_data["anonymity_flag"]
    )
    
    print("\n" + "=" * 40)
    
    # Verify report
    verification = client.verify_report(
        report_id=report_data["report_id"],
        evidence_hash=evidence_hash
    )
    
    print("\n" + "=" * 40)
    
    # Get status
    status = client.get_report_status(report_data["report_id"])
    print(f"Status: {json.dumps(status, indent=2)}")

if __name__ == "__main__":
    main()