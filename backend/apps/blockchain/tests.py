from django.test import TestCase
from apps.blockchain.models import BlockchainAnchor
from apps.blockchain.cardano_utils import CardanoEvidenceAnchoring
from apps.reports.models import Report
import json


class BlockchainMetadataPersistenceTest(TestCase):
    """
    Integration test to verify that BlockchainAnchor.metadata is properly
    stored and persisted in the database.
    """

    def setUp(self):
        """Set up test data"""
        self.cardano = CardanoEvidenceAnchoring(network="preview")

    def test_blockchain_anchor_metadata_persists(self):
        """
        Test that when creating a BlockchainAnchor, the metadata field
        is properly saved and retrieved from the database.
        """
        # Create test evidence data
        evidence_data = {
            "report_id": "RRS-2025-00999",
            "reference_code": "RRS-2025-00999",
            "category": "corruption",
            "description": "Test corruption incident",
            "latitude": "-1.950000",
            "longitude": "30.060000",
            "location_description": "Kigali",
            "ipfs_cid": "QmTestCID123456",
            "timestamp": "2025-11-26T14:00:00Z",
            "is_anonymous": True
        }

        # Generate evidence hash
        evidence_hash = self.cardano.generate_evidence_hash(evidence_data)

        # Create anchor transaction (simulated)
        anchor_result = self.cardano.create_anchor_transaction(
            report_id="RRS-2025-00999",
            evidence_hash=evidence_hash,
            category="corruption",
            is_anonymous=True,
            reporter_info=None
        )

        # Verify the anchor_result contains expected keys
        self.assertIn("tx_hash", anchor_result)
        self.assertIn("anchor_data", anchor_result)
        self.assertIn("timestamp", anchor_result)

        # Create BlockchainAnchor with metadata
        metadata = {
            "anchor_data": anchor_result.get("anchor_data", {}),
            "submission_time": anchor_result.get("timestamp", 0)
        }

        anchor = BlockchainAnchor.objects.create(
            report_id="RRS-2025-00999",
            evidence_hash=evidence_hash,
            ipfs_cid="QmTestCID123456",
            transaction_hash=anchor_result.get("tx_hash", ""),
            status=BlockchainAnchor.Status.PENDING,
            network="preview",
            metadata=metadata
        )

        # Verify the anchor was created
        self.assertIsNotNone(anchor.id)
        self.assertEqual(anchor.report_id, "RRS-2025-00999")
        self.assertEqual(anchor.evidence_hash, evidence_hash)
        self.assertEqual(anchor.network, "preview")

        # **CRITICAL TEST**: Verify metadata is persisted in database
        # Retrieve the anchor from DB (this is the real test)
        retrieved_anchor = BlockchainAnchor.objects.get(id=anchor.id)

        # Check that metadata exists and is not empty
        self.assertIsNotNone(retrieved_anchor.metadata, "Metadata should not be None")
        self.assertNotEqual(retrieved_anchor.metadata, {}, "Metadata should not be empty dict")

        # Verify metadata structure
        self.assertIn("anchor_data", retrieved_anchor.metadata, "Metadata should contain 'anchor_data'")
        self.assertIn("submission_time", retrieved_anchor.metadata, "Metadata should contain 'submission_time'")

        # Verify anchor_data contents
        anchor_data = retrieved_anchor.metadata.get("anchor_data", {})
        self.assertEqual(anchor_data.get("action"), "anchor_evidence")
        self.assertEqual(anchor_data.get("report_id"), "RRS-2025-00999")
        self.assertEqual(anchor_data.get("category"), "corruption")
        self.assertEqual(anchor_data.get("is_anonymous"), True)
        self.assertEqual(anchor_data.get("network"), "preview")

        # Verify submission_time is preserved
        submission_time = retrieved_anchor.metadata.get("submission_time")
        self.assertIsNotNone(submission_time)
        self.assertGreater(submission_time, 0)

        print(f"✅ Metadata persisted correctly: {json.dumps(retrieved_anchor.metadata, indent=2)}")

    def test_blockchain_anchor_metadata_json_serializable(self):
        """
        Test that BlockchainAnchor.metadata is JSON serializable
        (required for proper JSONField storage).
        """
        evidence_hash = "445c57360fc85302a09b9061f612637d0b795a5649d5a6dfe390e06bae484dfc"

        metadata = {
            "anchor_data": {
                "action": "anchor_evidence",
                "report_id": "RRS-2025-00998",
                "evidence_hash": evidence_hash,
                "category": "theft",
                "is_anonymous": False,
                "timestamp": 1704067200000,
                "network": "preview",
                "reporter": {
                    "name": "John Doe",
                    "phone": "+250788123456",
                    "email": "john@example.com"
                }
            },
            "submission_time": 1704067200000
        }

        anchor = BlockchainAnchor.objects.create(
            report_id="RRS-2025-00998",
            evidence_hash=evidence_hash,
            ipfs_cid="QmTestCID998",
            transaction_hash="9ee7e5fa9fbb6cef039d7b8752e38d874149991e42dddcf68495eb46d735fd47",
            status=BlockchainAnchor.Status.PENDING,
            network="preview",
            metadata=metadata
        )

        # Retrieve and verify JSON structure
        retrieved = BlockchainAnchor.objects.get(id=anchor.id)
        
        # Ensure metadata is valid JSON (JSONField should handle this)
        self.assertIsInstance(retrieved.metadata, dict)
        
        # Verify complex nested structure is preserved
        reporter = retrieved.metadata.get("anchor_data", {}).get("reporter", {})
        self.assertEqual(reporter.get("name"), "John Doe")
        self.assertEqual(reporter.get("phone"), "+250788123456")

        # Ensure we can serialize it to JSON string
        json_str = json.dumps(retrieved.metadata)
        self.assertIsInstance(json_str, str)
        self.assertIn("John Doe", json_str)

        print(f"✅ Metadata is JSON serializable and nested structure preserved")

    def test_blockchain_anchor_metadata_default_empty_dict(self):
        """
        Test that when metadata is not provided, it defaults to an empty dict
        (or None based on model definition).
        """
        anchor = BlockchainAnchor.objects.create(
            report_id="RRS-2025-00997",
            evidence_hash="8cc8fc60f589d8b846ecbafabe893580ae817cad82841e87466e40ff8abd46ca",
            ipfs_cid="QmTestCID997",
            transaction_hash="61a779734959d9d499d2b1a6ff3fcd12781fd58bc664f4ff054b5cf29d88b3a5",
            status=BlockchainAnchor.Status.PENDING,
            network="preview"
            # metadata not provided
        )

        retrieved = BlockchainAnchor.objects.get(id=anchor.id)
        
        # Metadata should be an empty dict (from default=dict)
        self.assertIsNotNone(retrieved.metadata)
        self.assertEqual(retrieved.metadata, {})

        print(f"✅ Metadata defaults to empty dict correctly")

    def test_blockchain_anchor_metadata_update(self):
        """
        Test that metadata can be updated and changes persist.
        """
        initial_metadata = {
            "anchor_data": {
                "action": "anchor_evidence",
                "report_id": "RRS-2025-00996",
            },
            "submission_time": 1704067200000
        }

        anchor = BlockchainAnchor.objects.create(
            report_id="RRS-2025-00996",
            evidence_hash="4f540f712e69e4169faf56813ea3054c9a27ee784b577a891401622ace1eecbe",
            ipfs_cid="QmTestCID996",
            transaction_hash="9ee7e5fa9fbb6cef039d7b8752e38d874149991e42dddcf68495eb46d735fd47",
            status=BlockchainAnchor.Status.PENDING,
            network="preview",
            metadata=initial_metadata
        )

        # Update metadata to add confirmation info
        anchor.metadata["confirmations"] = 5
        anchor.metadata["confirmed_at"] = "2025-11-26T14:30:00Z"
        anchor.save()

        # Retrieve and verify update persisted
        retrieved = BlockchainAnchor.objects.get(id=anchor.id)
        self.assertEqual(retrieved.metadata.get("confirmations"), 5)
        self.assertEqual(retrieved.metadata.get("confirmed_at"), "2025-11-26T14:30:00Z")

        print(f"✅ Metadata updates persist correctly")

    def test_report_integration_with_blockchain_metadata(self):
        """
        End-to-end test: Create a Report and verify BlockchainAnchor metadata
        is properly stored when anchoring is performed.
        """
        # Create a test report
        report = Report.objects.create(
            category="corruption",
            description="Test corruption report for metadata verification",
            location_description="Kigali, Rwanda",
            latitude="-1.950000",
            longitude="30.060000",
            is_anonymous=True,
            status="new"
        )

        # Simulate the anchoring process (as done in AsyncReportSubmitAPI.process_report_blockchain)
        evidence_json = {
            "report_id": str(report.id),
            "reference_code": report.reference_code,
            "category": report.category,
            "description": report.description,
            "latitude": str(report.latitude),
            "longitude": str(report.longitude),
            "location_description": report.location_description,
            "timestamp": report.created_at.isoformat(),
            "is_anonymous": report.is_anonymous
        }

        # Generate evidence hash
        evidence_hash = self.cardano.generate_evidence_hash(evidence_json)

        # Create anchor transaction
        anchor_result = self.cardano.create_anchor_transaction(
            report_id=report.reference_code,
            evidence_hash=evidence_hash,
            category=report.category,
            is_anonymous=report.is_anonymous,
            reporter_info=None
        )

        # Create BlockchainAnchor with metadata (as done in views.py)
        anchor = BlockchainAnchor.objects.create(
            report_id=report.reference_code,
            evidence_hash=evidence_hash,
            ipfs_cid="QmIntegrationTest",
            transaction_hash=anchor_result.get("tx_hash", ""),
            status=BlockchainAnchor.Status.PENDING,
            network="preview",
            metadata={
                "anchor_data": anchor_result.get("anchor_data", {}),
                "submission_time": anchor_result.get("timestamp", 0)
            }
        )

        # Retrieve anchor and verify metadata
        retrieved_anchor = BlockchainAnchor.objects.get(report_id=report.reference_code)

        # **KEY ASSERTIONS**
        self.assertIsNotNone(retrieved_anchor.metadata, "Anchor metadata should not be None")
        self.assertNotEqual(retrieved_anchor.metadata, {}, "Anchor metadata should not be empty")

        # Verify the report reference is in the metadata
        anchor_data = retrieved_anchor.metadata.get("anchor_data", {})
        self.assertEqual(anchor_data.get("report_id"), report.reference_code)

        print(f"✅ Report integration test passed: Metadata preserved for {report.reference_code}")
        print(f"   Metadata: {json.dumps(retrieved_anchor.metadata, indent=2)}")
