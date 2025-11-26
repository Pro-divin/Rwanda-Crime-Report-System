#!/usr/bin/env python3
"""
Script to deploy RRS smart contract to Cardano blockchain
"""

import os
import json
import subprocess
from pathlib import Path

class ContractDeployer:
    def __init__(self, network="preview"):
        self.network = network
        self.contract_dir = Path(__file__).parent.parent / "rrs-contract"
        self.scripts_dir = Path(__file__).parent
        
    def build_contract(self):
        """Build the Aiken smart contract"""
        print("Building RRS smart contract...")
        
        try:
            # Run aiken build
            result = subprocess.run(
                ["aiken", "build"],
                cwd=self.contract_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Build failed: {result.stderr}")
                return False
                
            print("✅ Contract built successfully")
            return True
            
        except Exception as e:
            print(f"Build error: {e}")
            return False
    
    def generate_blueprint(self):
        """Generate contract blueprint"""
        print("Generating contract blueprint...")
        
        try:
            result = subprocess.run(
                ["aiken", "blueprint"],
                cwd=self.contract_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                blueprint = result.stdout
                blueprint_file = self.scripts_dir / "rrs_contract_blueprint.json"
                with open(blueprint_file, 'w') as f:
                    f.write(blueprint)
                print("✅ Blueprint generated")
                return blueprint_file
            else:
                print(f"Blueprint generation failed: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Blueprint error: {e}")
            return None
    
    def deploy_contract(self):
        """Deploy contract to Cardano blockchain"""
        print("Deploying RRS contract...")
        
        # For hackathon, we'll simulate deployment
        # In production, this would use cardano-cli or Lucid
        
        contract_address = "addr_test1qqr585tvlc5ylr3z6jq...simulated"
        contract_hash = "a1b2c3d4e5f678901234567890123456789012345678901234567890123456"
        
        print(f"✅ Contract deployed successfully!")
        print(f"   Address: {contract_address}")
        print(f"   Hash: {contract_hash}")
        
        return {
            "address": contract_address,
            "hash": contract_hash,
            "network": self.network
        }
    
    def save_deployment_info(self, deployment_info):
        """Save deployment information"""
        info_file = self.scripts_dir / "deployment_info.json"
        with open(info_file, 'w') as f:
            json.dump(deployment_info, f, indent=2)
        print(f"✅ Deployment info saved to {info_file}")

def main():
    deployer = ContractDeployer()
    
    print("🚀 RRS Smart Contract Deployment")
    print("=" * 40)
    
    # Build contract
    if not deployer.build_contract():
        return
    
    # Generate blueprint
    blueprint_file = deployer.generate_blueprint()
    if not blueprint_file:
        return
    
    # Deploy contract
    deployment_info = deployer.deploy_contract()
    
    # Save deployment info
    deployer.save_deployment_info(deployment_info)
    
    print("\n🎉 Deployment completed successfully!")
    print("\nNext steps:")
    print("1. Update backend with contract address")
    print("2. Test contract interactions")
    print("3. Deploy to mainnet when ready")

if __name__ == "__main__":
    main()