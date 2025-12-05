import json
import hashlib
import requests
import time
from datetime import datetime
from django.conf import settings
from pathlib import Path

# PyCardano imports
try:
    from pycardano import (
        BlockFrostChainContext,
        TransactionBuilder as PyCardanoTransactionBuilder,
        TransactionOutput,
        Value,
        Metadata,
        AlonzoMetadata,
        AuxiliaryData,
        TransactionBody,
        TransactionWitnessSet,
        VerificationKeyWitness,
        Transaction,
        PaymentExtendedSigningKey,
        PaymentSigningKey,
        Address,
        Network
    )
    PYCARDANO_AVAILABLE = True
except ImportError:
    PYCARDANO_AVAILABLE = False
    print("⚠️ PyCardano not found. Blockchain features will be simulated.")

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
        self.should_broadcast = getattr(settings, 'ANCHOR_BROADCAST', True)

    def _get_wallet_info(self):
        # Logic to find and load key
        try:
            # Try standard location
            skey_path = settings.BASE_DIR.parent / "backend" / "keys" / "payment.skey"
            if not skey_path.exists():
                skey_path = settings.BASE_DIR.parent / "secure" / "payment.skey.json"
            
            if not skey_path.exists():
                print(f"❌ Signing key not found at {skey_path}")
                return None, None

            # Load key
            try:
                # Try loading as extended first (just in case)
                signing_key = PaymentExtendedSigningKey.load(str(skey_path))
            except:
                signing_key = PaymentSigningKey.load(str(skey_path))

            # Verify key validity
            verification_key = signing_key.to_verification_key()
            
            # Workaround for empty verification key (if loaded as extended but is simple, or vice versa issues)
            if len(verification_key.payload) == 0:
                priv_bytes = signing_key.payload[:32]
                signing_key = PaymentSigningKey(priv_bytes)
                verification_key = signing_key.to_verification_key()

            # Derive address
            # Network.TESTNET covers Preprod and Preview
            address = Address(payment_part=verification_key.hash(), network=Network.TESTNET)
            
            return address, signing_key
            
        except Exception as e:
            print(f"❌ Error loading wallet: {e}")
            return None, None

    def anchor_evidence_hash(self, report_id, evidence_hash, category, is_anonymous):
        """
        Anchors the evidence hash to the Cardano blockchain.
        Returns the transaction hash.
        """
        if not self.should_broadcast or not PYCARDANO_AVAILABLE:
            print("⚠️ Broadcasting disabled or PyCardano missing. Simulating.")
            return hashlib.sha256(f"{report_id}{evidence_hash}{time.time()}".encode()).hexdigest()

        try:
            print(f"🔗 Anchoring Report {report_id} to Cardano ({self.network})...")
            
            # 1. Setup Context
            context = BlockFrostChainContext(
                project_id=self.blockfrost_key,
                base_url="https://cardano-preview.blockfrost.io/api"
            )
            
            # 2. Get Wallet
            payment_address, signing_key = self._get_wallet_info()
            if not payment_address:
                raise Exception("Could not load wallet for signing.")
                
            # 3. Build Metadata
            meta_dict = {
                674: {
                    "msg": [f"RRS Report: {report_id}", f"Cat: {category}"],
                    "hash": evidence_hash,
                    "anon": "Yes" if is_anonymous else "No",
                    "ts": int(time.time())
                }
            }
            
            metadata_obj = Metadata(meta_dict)
            alonzo_metadata = AlonzoMetadata(metadata=metadata_obj)
            auxiliary_data = AuxiliaryData(data=alonzo_metadata)
            
            # 4. Build Transaction
            builder = PyCardanoTransactionBuilder(context)
            builder.add_input_address(payment_address)
            builder.add_output(TransactionOutput(payment_address, Value(1500000))) # Min ADA
            builder.auxiliary_data = auxiliary_data
            
            tx_body = builder.build(change_address=payment_address)
            
            # 5. Sign
            signature = signing_key.sign(tx_body.hash())
            vk = signing_key.to_verification_key()
            vk_witness = VerificationKeyWitness(vk, signature)
            witness_set = TransactionWitnessSet(vkey_witnesses=[vk_witness])
            
            tx = Transaction(tx_body, witness_set, auxiliary_data=auxiliary_data)
            
            # 6. Submit
            print("🚀 Submitting transaction to Blockfrost...")
            context.submit_tx(tx)
            
            tx_id = str(tx.id)
            print(f"✅ Transaction submitted: {tx_id}")
            return tx_id

        except Exception as e:
            print(f"❌ Blockchain anchoring failed: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to simulation so the report is still saved
            return f"FAILED_ANCHOR_{int(time.time())}"

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
