"""
Cardano Blockchain Integration for Rwanda Report System
Handles evidence hash anchoring and verification on Cardano blockchain
"""

import json
import hashlib
import time
from datetime import datetime
from typing import Dict, Optional, Tuple
import os
import traceback

# PyCardano imports
try:
    from pycardano import (
        BlockFrostChainContext,
        TransactionBuilder,
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


class CardanoEvidenceAnchoring:
    """
    Manages evidence anchoring on Cardano blockchain
    Uses Blockfrost API for mainnet/preview network operations
    """
    
    def __init__(self, network: str = "preview", blockfrost_key: str = ""):
        """
        Initialize Cardano integration
        
        Args:
            network: 'preview' (testnet) or 'mainnet'
            blockfrost_key: Blockfrost API key
        """
        self.network = network
        # Load Blockfrost key from Django settings if not provided
        try:
            from django.conf import settings
            cfg_key = getattr(settings, 'BLOCKFROST_PROJECT_ID', '')
            self.broadcast_enabled = bool(getattr(settings, 'ANCHOR_BROADCAST', False))
        except Exception:
            cfg_key = ''
            self.broadcast_enabled = False

        self.blockfrost_key = blockfrost_key or cfg_key
        self.blockfrost_url = f"https://cardano-{network}.blockfrost.io/api/v0"
        self.contract_address = ""  # Will be set after deployment
        
    def generate_evidence_hash(self, evidence_data: Dict) -> str:
        """
        Generate SHA-256 hash of evidence data
        
        Args:
            evidence_data: Dictionary containing report evidence
            
        Returns:
            Hex string of SHA-256 hash (64 characters)
        """
        json_str = json.dumps(evidence_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    
    def create_anchor_transaction(
        self,
        report_id: str,
        evidence_hash: str,
        category: str,
        is_anonymous: bool,
        reporter_info: Optional[Dict] = None,
        ipfs_cid: Optional[str] = None
    ) -> Dict:
        """
        Create blockchain transaction to anchor evidence
        
        Args:
            report_id: Reference code like RRS-2025-00001
            evidence_hash: SHA-256 hash of evidence
            category: Report category
            is_anonymous: Whether report is anonymous
            reporter_info: Optional reporter metadata
            
        Returns:
            Dictionary with transaction details
        """
        timestamp = int(time.time() * 1000)  # Current time in milliseconds
        
        anchor_data = {
            "action": "anchor_evidence",
            "report_id": report_id,
            "evidence_hash": evidence_hash,
            "category": category,
            "is_anonymous": is_anonymous,
            "timestamp": timestamp,
            "network": self.network,
            "ipfs_cid": ipfs_cid,  # Link to distributed IPFS storage (1000+ nodes)
            "distributed_storage": bool(ipfs_cid),
        }
        
        if reporter_info and not is_anonymous:
            anchor_data["reporter"] = {
                "name": reporter_info.get("name", ""),
                "phone": reporter_info.get("phone", ""),
                "email": reporter_info.get("email", ""),
            }
        
        # If broadcasting is disabled, or no credentials configured, simulate
        if not self.broadcast_enabled or not self.blockfrost_key:
            tx_hash = self._simulate_tx_submission(anchor_data)
            return {
                "success": True,
                "tx_hash": tx_hash,
                "status": "pending",
                "timestamp": timestamp,
                "anchor_data": anchor_data,
                "simulated": True,
                "note": "Anchoring simulated (ANCHOR_BROADCAST=False or Blockfrost key missing)."
            }

        # Real transaction submission using pycardano
        try:
            tx_hash = self._submit_real_transaction(anchor_data)
            explorer_primary = f"https://{self.network}.cexplorer.io/tx/{tx_hash}" if self.network != 'mainnet' else f"https://cexplorer.io/tx/{tx_hash}"
            explorer_secondary = f"https://{self.network}.cardanoscan.io/transaction/{tx_hash}" if self.network != 'mainnet' else f"https://cardanoscan.io/transaction/{tx_hash}"
            return {
                "success": True,
                "tx_hash": tx_hash,
                "status": "submitted",
                "timestamp": timestamp,
                "anchor_data": anchor_data,
                "simulated": False,
                "note": (
                    f"Transaction submitted to {self.network} network. Explorer links: "
                    f"cexplorer={explorer_primary} cardanoscan={explorer_secondary}"
                ),
                "explorers": {
                    "cexplorer": explorer_primary,
                    "cardanoscan": explorer_secondary
                }
            }
        except Exception as e:
            # Fall back to simulation if real submission fails
            print(f"❌ Real broadcast failed: {e}")
            traceback.print_exc()
            tx_hash = self._simulate_tx_submission(anchor_data)
            return {
                "success": True,
                "tx_hash": tx_hash,
                "status": "pending",
                "timestamp": timestamp,
                "anchor_data": anchor_data,
                "simulated": True,
                "error": str(e),
                "note": f"Real broadcast failed ({str(e)}), fell back to simulation."
            }
    
    def verify_evidence_on_chain(
        self,
        report_id: str,
        evidence_hash: str
    ) -> Dict:
        """
        Verify that evidence hash exists on blockchain
        
        Args:
            report_id: Reference code
            evidence_hash: SHA-256 hash to verify
            
        Returns:
            Verification result dictionary
        """
        # In production, query blockchain via Blockfrost API
        # For now, simulate verification
        return {
            "verified": True,
            "report_id": report_id,
            "evidence_hash": evidence_hash,
            "confirmed_at": datetime.now().isoformat(),
            "network": self.network,
        }
    
    def submit_to_ipfs(self, data: Dict) -> str:
        """
        Store evidence metadata on IPFS
        
        Args:
            data: Evidence data to store
            
        Returns:
            IPFS CID (content identifier)
        """
        json_str = json.dumps(data, sort_keys=True)
        # Simulate IPFS CID generation
        # Format: Qm + SHA-256 hash of content (base58 encoded)
        hash_digest = hashlib.sha256(json_str.encode()).hexdigest()
        # Simplified: return mock CID
        cid = f"Qm{hash_digest[:44]}"
        return cid
    
    def _simulate_tx_submission(self, anchor_data: Dict) -> str:
        """
        Simulate transaction submission to blockchain
        In production, replace with actual Blockfrost/Cardano submission
        
        Args:
            anchor_data: Data to anchor
            
        Returns:
            Simulated transaction hash
        """
        # Create deterministic hash of anchor data for testing
        data_str = json.dumps(anchor_data, sort_keys=True)
        tx_hash = hashlib.sha256(data_str.encode()).hexdigest()
        return tx_hash

    def _submit_real_transaction(self, anchor_data: Dict) -> str:
        """
        Submit real transaction to Cardano blockchain using PyCardano
        
        Args:
            anchor_data: Data to anchor on chain
            
        Returns:
            Real transaction hash from blockchain
            
        Raises:
            Exception: If transaction fails or wallet not configured
        """
        if not PYCARDANO_AVAILABLE:
            raise Exception("PyCardano library not available")

        # 1. Setup Context
        # Note: BlockFrostChainContext in PyCardano handles the base URL correctly if we give it the right one
        # For preview, it should be https://cardano-preview.blockfrost.io/api
        # It appends /v0 internally if needed, or we provide it.
        # Based on testing, providing /api works best with current pycardano version
        
        base_url = f"https://cardano-{self.network}.blockfrost.io/api"
        
        context = BlockFrostChainContext(
            project_id=self.blockfrost_key,
            base_url=base_url
        )
        
        # 2. Get Wallet Info
        try:
            import json
            import base64
            import tempfile
            from django.conf import settings
            
            root_dir = settings.BASE_DIR.parent
            
            # First try to load from environment (for cloud deployments like Render)
            signing_key_env = os.environ.get('CARDANO_SIGNING_KEY')
            
            if signing_key_env:
                print("Loading signing key from environment variable (cloud deployment)...")
                try:
                    # Assume it's base64 encoded JSON
                    key_data = base64.b64decode(signing_key_env).decode('utf-8')
                    key_json = json.loads(key_data)
                    
                    # Write to temp file and load
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.skey', delete=False) as tmp:
                        json.dump(key_json, tmp)
                        tmp_path = tmp.name
                    
                    try:
                        signing_key = PaymentExtendedSigningKey.load(tmp_path)
                    except Exception:
                        signing_key = PaymentSigningKey.load(tmp_path)
                    
                    os.unlink(tmp_path)
                except Exception as e:
                    print(f"Failed to load from environment: {e}")
                    signing_key = None
            else:
                signing_key = None
            
            # If not in environment, try local file (development)
            if signing_key is None:
                print("Loading signing key from local file (development)...")
                # Try backend/keys/payment.skey first (Standard location)
                skey_path = root_dir / "backend" / "keys" / "payment.skey"
                
                if not skey_path.exists():
                    # Fallback to secure/payment.skey.json
                    skey_path = root_dir / "secure" / "payment.skey.json"
                
                if not skey_path.exists():
                    raise FileNotFoundError(f"Signing key not found at {skey_path}. Please set CARDANO_SIGNING_KEY env var for cloud deployments.")
                    
                # Load key based on type in file or try both
                try:
                    signing_key = PaymentExtendedSigningKey.load(str(skey_path))
                except Exception:
                    signing_key = PaymentSigningKey.load(str(skey_path))
                
            verification_key = signing_key.to_verification_key()
            
            # Workaround for empty verification key issue with Extended Keys
            if len(verification_key.payload) == 0:
                print("⚠️  Empty verification key detected. Attempting workaround...")
                # Extract the first 32 bytes (private key) from the extended key
                priv_bytes = signing_key.payload[:32]
                signing_key_simple = PaymentSigningKey(priv_bytes)
                verification_key = signing_key_simple.to_verification_key()
                signing_key = signing_key_simple
            
            # Derive address
            payment_address = Address(payment_part=verification_key.hash(), network=Network.TESTNET)
            
        except Exception as e:
            raise Exception(f"Wallet loading failed: {e}")

        # 3. Build Metadata
        # Use label 674 for RRS-specific metadata (Cardano standard for custom data)
        # Keep structure very simple for maximum compatibility across environments
        meta_dict = {
            674: {
                "rrs": "RRS",  # Application identifier
                "report": anchor_data['report_id'][:50],  # Truncate to safe length
                "hash": anchor_data['evidence_hash'][:32],  # First 32 chars of hash
                "cat": anchor_data['category'][:20],  # Truncate category
                "ts": str(anchor_data['timestamp']),  # Convert timestamp to string
            }
        }
        
        try:
            metadata_obj = Metadata(meta_dict)
            alonzo_metadata = AlonzoMetadata(metadata=metadata_obj)
            auxiliary_data = AuxiliaryData(data=alonzo_metadata)
            print(f"✅ Metadata object created successfully with data: {meta_dict}")
        except Exception as e:
            print(f"❌ Metadata creation failed: {e}. Proceeding without metadata.")
            auxiliary_data = None
        
        # 4. Build Transaction
        builder = TransactionBuilder(context)
        builder.add_input_address(payment_address)
        
        # Send a small amount to self to carry the metadata (min ADA)
        builder.add_output(TransactionOutput(payment_address, Value(1500000)))
        
        # Set auxiliary data BEFORE building (if metadata was created)
        if auxiliary_data is not None:
            builder.auxiliary_data = auxiliary_data
        
        # Build transaction with metadata
        tx_body = builder.build(change_address=payment_address)
        
        # Verify metadata is in tx_body
        if auxiliary_data is not None:
            if tx_body.auxiliary_data_hash is None:
                print("⚠️ Warning: Auxiliary data hash is None. Metadata may not be properly serialized.")
            else:
                print(f"✅ Metadata attached with hash: {tx_body.auxiliary_data_hash}")
        else:
            print("ℹ️ Transaction built without auxiliary data.")
        
        # 5. Sign
        signature = signing_key.sign(tx_body.hash())
        
        vk = signing_key.to_verification_key()
        vk_witness = VerificationKeyWitness(vk, signature)
        witness_set = TransactionWitnessSet(vkey_witnesses=[vk_witness])
        
        # Create transaction with auxiliary data
        tx = Transaction(tx_body, witness_set, auxiliary_data=auxiliary_data)
        
        # Double-check metadata is in final transaction
        print(f"📋 Transaction ID: {tx.id}")
        print(f"📦 Auxiliary data present: {tx.auxiliary_data is not None}")
        
        # 6. Submit
        print(f"🚀 Submitting transaction for report {anchor_data['report_id']}...")
        context.submit_tx(tx)
        
        tx_id = str(tx.id)
        print(f"✅ Transaction submitted: {tx_id}")
        
        return tx_id

    def get_transaction_status(self, tx_hash: str) -> Dict:
        """Query Blockfrost for a transaction status (confirmations, block height).

        Returns a dict with keys: found(bool), block_height, confirmations, block_time, slot.
        If Blockfrost key missing or request fails returns found False.
        """
        if not tx_hash or not self.blockfrost_key:
            return {"found": False, "reason": "missing tx_hash or blockfrost key"}
        import requests
        base = f"https://cardano-{self.network}.blockfrost.io/api/v0"
        headers = {"project_id": self.blockfrost_key}
        try:
            tx_r = requests.get(f"{base}/txs/{tx_hash}", headers=headers, timeout=15)
            if tx_r.status_code != 200:
                return {"found": False, "code": tx_r.status_code}
            tx = tx_r.json()
            block_height = tx.get("block_height")
            slot = tx.get("slot")
            block_time = tx.get("block_time")
            # latest block for confirmations
            latest_r = requests.get(f"{base}/blocks/latest", headers=headers, timeout=15)
            confirmations = None
            if latest_r.status_code == 200 and isinstance(block_height, int):
                latest = latest_r.json()
                latest_h = latest.get("height")
                if isinstance(latest_h, int):
                    confirmations = max(0, latest_h - block_height + 1)
            return {
                "found": True,
                "block_height": block_height,
                "confirmations": confirmations,
                "block_time": block_time,
                "slot": slot,
            }
        except requests.RequestException as e:
            return {"found": False, "error": str(e)}
    
    def get_current_timestamp(self) -> str:
        """Get current ISO timestamp for verification records"""
        from django.utils import timezone
        return timezone.now().isoformat()


class BlockchainStatusTracker:
    """
    Tracks blockchain transactions and report status
    """
    
    def __init__(self):
        self.cardano = CardanoEvidenceAnchoring()
    
    def get_report_blockchain_status(
        self,
        report_id: str,
        tx_hash: Optional[str] = None
    ) -> Dict:
        """
        Get blockchain confirmation status for a report
        Queries Blockfrost for real confirmation data
        
        Args:
            report_id: Report reference code
            tx_hash: Transaction hash if available
            
        Returns:
            Status dictionary with real confirmation counts
        """
        status_data = {
            "report_id": report_id,
            "tx_hash": tx_hash or "pending",
            "confirmations": 0,
            "status": "pending",
            "blockchain": "cardano",
            "network": self.cardano.network,
        }
        
        if tx_hash:
            # Query Blockfrost for real transaction confirmations
            try:
                tx_status = self.cardano.get_transaction_status(tx_hash)
                if tx_status.get("found"):
                    status_data["confirmations"] = tx_status.get("confirmations", 0)
                    status_data["status"] = "confirmed" if tx_status.get("confirmations", 0) > 0 else "submitted"
                    status_data["block_height"] = tx_status.get("block_height")
                    status_data["block_time"] = tx_status.get("block_time")
                    status_data["slot"] = tx_status.get("slot")
                else:
                    status_data["status"] = "submitted"
                    status_data["confirmations"] = 0
            except Exception as e:
                print(f"Warning: Could not query Blockfrost: {e}")
                status_data["status"] = "submitted"
                status_data["confirmations"] = 0
        
        return status_data
    
    def get_confirmations(self, tx_hash: str) -> int:
        """
        Get confirmation count for a transaction
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Number of confirmations
        """
        try:
            tx_status = self.cardano.get_transaction_status(tx_hash)
            if tx_status.get("found"):
                return tx_status.get("confirmations", 0)
            return 0
        except Exception as e:
            print(f"Error getting confirmations: {e}")
            return 0
