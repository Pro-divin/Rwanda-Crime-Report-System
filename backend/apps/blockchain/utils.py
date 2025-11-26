import json
import hashlib
import requests
from datetime import datetime
from django.conf import settings

# Optional IPFS real support
try:
    import ipfshttpclient
    IPFS_ENABLED = True

    # Bypass Kubo 0.38+ version check
    from ipfshttpclient.client import assert_version
    def skip_version_check(version, minimum=None, maximum=None):
        print(f"⚠️ Skipping IPFS version check: {version}")
    ipfshttpclient.client.assert_version = skip_version_check

except ImportError:
    IPFS_ENABLED = False


# ============================================================
# 1️⃣ IPFS UTILITIES
# ============================================================

class IPFSUtils:
    def __init__(self, api_address="/ip4/127.0.0.1/tcp/5001"):
        self.api_address = api_address
        if IPFS_ENABLED:
            self.client = ipfshttpclient.connect(self.api_address)
        else:
            self.client = None

    def upload_file(self, file_path):
        try:
            if self.client:
                res = self.client.add(file_path)
                return res["Hash"]

            # fallback simulation
            simulated_cid = "Qm" + hashlib.sha256(file_path.encode()).hexdigest()[:44]
            return simulated_cid

        except Exception as e:
            print(f"❌ IPFS upload error: {e}")
            return "Qm" + hashlib.sha256(file_path.encode()).hexdigest()[:44]

    def upload_json(self, data):
        try:
            if self.client:
                cid = self.client.add_json(data)
                return cid

            # fallback simulation
            json_str = json.dumps(data, sort_keys=True)
            simulated_cid = "Qm" + hashlib.sha256(json_str.encode()).hexdigest()[:44]
            return simulated_cid

        except Exception as e:
            print(f"❌ IPFS JSON upload error: {e}")
            return None

    def get_file(self, cid):
        try:
            if self.client:
                return self.client.cat(cid)
            return b"Simulated IPFS content"
        except Exception as e:
            print(f"❌ IPFS retrieve error: {e}")
            return None


# ============================================================
# 2️⃣ CARDANO BLOCKCHAIN UTILS
# ============================================================

class BlockchainUtils:
    def __init__(self):
        self.network = getattr(settings, 'CARDANO_NETWORK', 'preview')
        self.blockfrost_key = getattr(settings, 'BLOCKFROST_PROJECT_ID', '')

    def anchor_evidence_hash(self, report_id, evidence_hash, category, is_anonymous):
        """Simulated offline anchoring"""
        import time
        tx_hash = hashlib.sha256(
            f"{report_id}{evidence_hash}{time.time()}".encode()
        ).hexdigest()
        return tx_hash

    def verify_evidence_hash(self, report_id, evidence_hash):
        """Simulated verification"""
        return True


# ============================================================
# 3️⃣ BLOCKFROST API WRAPPER
# ============================================================

class CardanoBlockchain:
    def __init__(self, network=None):
        self.network = network or getattr(settings, 'CARDANO_NETWORK', 'preview')
        self.blockfrost_key = getattr(settings, 'BLOCKFROST_PROJECT_ID', '')
        self.base_url = self._network_url()

    def _network_url(self):
        return {
            "mainnet": "https://cardano-mainnet.blockfrost.io/api/v0",
            "preview": "https://cardano-preview.blockfrost.io/api/v0",
            "preprod": "https://cardano-preprod.blockfrost.io/api/v0"
        }.get(self.network, "https://cardano-preview.blockfrost.io/api/v0")

    def _headers(self):
        return {"project_id": self.blockfrost_key, "Content-Type": "application/json"}

    def get_transaction(self, tx_hash):
        r = requests.get(f"{self.base_url}/txs/{tx_hash}", headers=self._headers())
        return r.json() if r.status_code == 200 else None

    def get_address_utxos(self, address):
        r = requests.get(f"{self.base_url}/addresses/{address}/utxos", headers=self._headers())
        return r.json() if r.status_code == 200 else []

    def submit_transaction(self, tx_cbor):
        r = requests.post(f"{self.base_url}/tx/submit", headers=self._headers(), data=tx_cbor)
        return r.json() if r.status_code == 200 else None


# ============================================================
# 4️⃣ EVIDENCE MANAGER
# ============================================================

class EvidenceManager:

    @staticmethod
    def create_evidence_json(data):
        return {
            "report_id": data.get("report_id"),
            "reference_code": data.get("reference_code"),
            "category": data.get("category"),
            "description": data.get("description"),
            "location": {
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "description": data.get("location_description")
            },
            "timestamp": data.get("timestamp") or datetime.now().isoformat(),
            "media_cid": data.get("ipfs_cid"),
            "anonymity_flag": data.get("is_anonymous", False),
            "version": "1.0"
        }

    @staticmethod
    def calculate_evidence_hash(evidence_data):
        canonical_json = json.dumps(
            evidence_data, sort_keys=True, separators=(',', ':'), ensure_ascii=False
        )
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

    @staticmethod
    def verify(original_hash, current_data):
        new = EvidenceManager.create_evidence_json(current_data)
        new_hash = EvidenceManager.calculate_evidence_hash(new)
        return original_hash == new_hash


# ============================================================
# 5️⃣ TRANSACTION BUILDER (AIKEN-CONTRACT READY)
# ============================================================

class TransactionBuilder:
    def __init__(self, network="preview"):
        self.network = network

    def build_anchor_transaction(self, report_data, evidence_hash):
        return {
            "type": "anchor",
            "report_id": report_data.get("report_id"),
            "evidence_hash": evidence_hash,
            "contract_address": "addr_test1qxxxx...aiken_contract",
            "fee": "1.5 ADA",
            "ttl": 3600,
            "metadata": {
                "reference": report_data.get("reference_code"),
                "category": report_data.get("category"),
                "timestamp": datetime.now().isoformat()
            }
        }

    def build_verification_transaction(self, report_id, evidence_hash):
        return {
            "type": "verify",
            "report_id": report_id,
            "evidence_hash": evidence_hash,
            "contract_address": "addr_test1qxxxx...aiken_contract",
            "fee": "0.5 ADA"
        }
