# RRS Blockchain Components

This directory contains the Cardano smart contracts and blockchain integration for the Rwanda Report System.

## Structure

- `rrs-contract/` - Aiken smart contract source code
- `scripts/` - Python scripts for deployment and interaction
- `deployment_info.json` - Contract deployment information

## Smart Contract

The RRS validator contract provides:

1. **Evidence Anchoring** - Store SHA-256 hashes of report evidence
2. **Tamper Verification** - Verify evidence integrity against blockchain record
3. **Report Management** - Support for anonymous and identified reports

## Deployment

1. Build the contract:
```bash
cd rrs-contract
aiken build