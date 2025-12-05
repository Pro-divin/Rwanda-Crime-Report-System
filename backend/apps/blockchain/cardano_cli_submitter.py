"""
Alternative Cardano transaction submission using cardano-cli via WSL
This bypasses the pycardano library issue entirely
"""
import json
import subprocess
import hashlib
import os
from typing import Dict

class CardanoCliSubmitter:
    """Submit transactions using cardano-cli in WSL"""
    
    def __init__(self, network: str = "preview"):
        self.network = network
        self.network_magic = {
            "preview": "2",
            "preprod": "1",
            "mainnet": ""
        }.get(network, "2")
        
    def submit_evidence_transaction(
        self,
        anchor_data: Dict,
        signing_key_path: str,
        payment_address: str,
        blockfrost_key: str
    ) -> str:
        """
        Submit transaction with metadata using Blockfrost API + cardano-cli for signing
        
        Args:
            anchor_data: Evidence data to anchor
            signing_key_path: Path to payment.skey (Windows path)
            payment_address: Cardano address
            blockfrost_key: Blockfrost API key
            
        Returns:
            Transaction hash from blockchain
        """
        import requests
        
        # Use Blockfrost API for queries (no need for local node)
        base_url = f"https://cardano-{self.network}.blockfrost.io/api/v0"
        headers = {"project_id": blockfrost_key}
        
        # Convert Windows path to WSL path
        wsl_key_path = self._convert_to_wsl_path(signing_key_path)
        
        # Create temporary directory for transaction files
        temp_dir = "/tmp/rrs_tx"
        
        try:
            # Create temp directory in WSL
            self._run_wsl_command(f"mkdir -p {temp_dir}")
            
            # Step 1: Query UTXOs via Blockfrost API
            utxo_response = requests.get(
                f"{base_url}/addresses/{payment_address}/utxos",
                headers=headers,
                timeout=15
            )
            
            if utxo_response.status_code != 200:
                raise Exception(f"Failed to get UTXOs: {utxo_response.status_code}")
            
            utxos = utxo_response.json()
            
            if not utxos:
                raise Exception("No UTXOs available in wallet")
            
            # Get first UTXO
            utxo = utxos[0]
            tx_hash_in = utxo['tx_hash']
            tx_index = utxo['tx_index']
            tx_in = f"{tx_hash_in}#{tx_index}"
            
            # Get lovelace amount
            amount_in = int([amt for amt in utxo['amount'] if amt['unit'] == 'lovelace'][0]['quantity'])
            
            # Step 2: Create metadata file
            metadata = {
                "674": {
                    "msg": [
                        f"RRS Report: {anchor_data['report_id']}",
                        f"Evidence: {anchor_data['evidence_hash'][:32]}...",
                        f"Category: {anchor_data['category']}",
                        f"Timestamp: {anchor_data['timestamp']}"
                    ]
                }
            }
            
            # Write metadata to a Windows temp file first, then copy to WSL
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                json.dump(metadata, f)
                temp_metadata_path = f.name
            
            # Convert to WSL path and copy
            wsl_temp_path = self._convert_to_wsl_path(temp_metadata_path)
            self._run_wsl_command(f"cp {wsl_temp_path} {temp_dir}/metadata.json")
            
            # Cleanup Windows temp file
            os.remove(temp_metadata_path)
            
            # Step 3: Build transaction
            # Estimate fee (typically ~170000 lovelace)
            estimated_fee = 200000
            amount_out = amount_in - estimated_fee
            
            if amount_out < 1000000:
                raise Exception(f"Insufficient funds: {amount_in} lovelace available, need {estimated_fee + 1000000}")
            
            build_cmd = (
                f"cardano-cli transaction build-raw "
                f"--tx-in {tx_in} "
                f"--tx-out {payment_address}+{amount_out} "
                f"--metadata-json-file {temp_dir}/metadata.json "
                f"--fee {estimated_fee} "
                f"--out-file {temp_dir}/tx.raw"
            )
            
            self._run_wsl_command(build_cmd)
            
            # Step 4: Sign transaction
            sign_cmd = (
                f"cardano-cli transaction sign "
                f"--tx-body-file {temp_dir}/tx.raw "
                f"--signing-key-file {wsl_key_path} "
                f"--testnet-magic {self.network_magic} "
                f"--out-file {temp_dir}/tx.signed"
            )
            
            self._run_wsl_command(sign_cmd)
            
            # Step 5: Get transaction bytes for submission
            tx_bytes_cmd = f"cat {temp_dir}/tx.signed | xxd -p -c 0"
            tx_bytes_hex = self._run_wsl_command(tx_bytes_cmd).strip()
            
            # Step 6: Submit transaction via Blockfrost API
            submit_response = requests.post(
                f"{base_url}/tx/submit",
                headers={"project_id": blockfrost_key, "Content-Type": "application/cbor"},
                data=bytes.fromhex(tx_bytes_hex),
                timeout=15
            )
            
            if submit_response.status_code != 200:
                raise Exception(f"Transaction submission failed: {submit_response.status_code} - {submit_response.text}")
            
            # Step 7: Get transaction hash from Blockfrost response or calculate it
            tx_hash_result = submit_response.json()
            if isinstance(tx_hash_result, str):
                tx_hash = tx_hash_result
            else:
                # Calculate transaction hash from signed transaction
                txid_cmd = f"cardano-cli transaction txid --tx-file {temp_dir}/tx.signed"
                tx_hash = self._run_wsl_command(txid_cmd).strip()
            
            # Cleanup
            self._run_wsl_command(f"rm -rf {temp_dir}")
            
            return tx_hash
            
        except Exception as e:
            # Cleanup on error
            try:
                self._run_wsl_command(f"rm -rf {temp_dir}")
            except:
                pass
            raise Exception(f"cardano-cli transaction failed: {str(e)}")
    
    def _convert_to_wsl_path(self, windows_path: str) -> str:
        """Convert Windows path to WSL path"""
        # C:\Users\... -> /mnt/c/Users/...
        if ':' in windows_path:
            drive = windows_path[0].lower()
            path = windows_path[2:].replace('\\', '/')
            return f"/mnt/{drive}{path}"
        return windows_path
    
    def _run_wsl_command(self, command: str) -> str:
        """Run command in WSL and return output"""
        wsl_cmd = f'wsl bash -c "{command}"'
        
        result = subprocess.run(
            wsl_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise Exception(f"WSL command failed: {result.stderr}")
        
        return result.stdout


def test_cli_submission():
    """Test the cardano-cli submission"""
    print("=" * 80)
    print("  🧪 TESTING CARDANO-CLI SUBMISSION")
    print("=" * 80)
    print()
    
    submitter = CardanoCliSubmitter(network="preview")
    
    anchor_data = {
        "report_id": "RRS-TEST-CLI",
        "evidence_hash": "abcd1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "category": "corruption",
        "timestamp": 1701518400000
    }
    
    signing_key = r"C:\Users\peril ops\Desktop\RRS\backend\keys\payment.skey"
    address = "addr_test1vza7nn8c7p7rgcqsdjxvmwyqdztq9tgp8q89p2xugxc8djqmphalu"
    blockfrost_key = "previewWVajaYWaJWq9NZcNTgJsytyDOY2qTU5l"
    
    try:
        tx_hash = submitter.submit_evidence_transaction(
            anchor_data, signing_key, address, blockfrost_key
        )
        print("✅ Transaction submitted successfully!")
        print(f"   Transaction Hash: {tx_hash}")
        print(f"   View on explorer: https://preview.cexplorer.io/tx/{tx_hash}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    test_cli_submission()
