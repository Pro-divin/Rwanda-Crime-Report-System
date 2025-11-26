# Rwanda Report System (RRS) - Complete Setup Guide

## 🌍 Project Overview

Rwanda Report System is a **blockchain-powered citizen reporting platform** that allows Rwandan citizens to report crimes and emergencies securely. Evidence is protected using:

- **Cardano Blockchain** - Immutable tamper-proof evidence anchoring
- **Aiken Smart Contracts** - On-chain validation logic
- **IPFS** - Decentralized file storage for media
- **Django REST API** - Secure backend processing

---

## 📋 System Architecture

```
┌─────────────────────────────────────────────────┐
│  Frontend (HTML/JS)                              │
│  - Report submission form                        │
│  - Status tracking                               │
│  - Anonymous/identified reporting                │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  Django REST API (Backend)                       │
│  - Report validation                             │
│  - Evidence hash generation                      │
│  - IPFS integration                              │
│  - Blockchain anchoring                          │
└─────────────────┬───────────────────────────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
┌─────▼─────┐ ┌──▼────────┐ ┌─▼──────────────┐
│ SQLite DB │ │   IPFS    │ │  Cardano       │
│           │ │  (Files)  │ │  Blockchain    │
└───────────┘ └───────────┘ └────────────────┘
      │
┌─────▼─────────────────────────────────────────┐
│  Aiken Smart Contracts (Plutus)               │
│  - Evidence validation rules                  │
│  - Verification logic                         │
└───────────────────────────────────────────────┘
```

---

## ⚙️ Prerequisites

### Required Software
- **Python 3.9+** - For Django backend
- **Node.js** - For npm packages
- **Aiken** - For smart contract compilation
- **IPFS Desktop** (optional) - For local IPFS node

### Installation

#### 1. Python & Django
```bash
python --version  # Should be 3.9+
pip install -r backend/requirements.txt
```

#### 2. Aiken
```bash
# Install via Rust (recommended)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
curl -fsSL https://get.aiken-lang.org | bash

# Verify installation
aiken --version
```

#### 3. IPFS (Optional but recommended)
```bash
# Install IPFS Desktop from https://github.com/ipfs/ipfs-desktop
# Or use Go-IPFS CLI
ipfs --version
```

---

## 🚀 Quick Start (5 minutes)

### Step 1: Clone & Navigate
```bash
cd "C:\Users\peril ops\Desktop\RRS"
```

### Step 2: Setup Database
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Create admin account
```

### Step 3: Build Smart Contracts
```bash
cd ../blockchain/rrs-contract
aiken build
```

### Step 4: Start Django Server
```bash
cd ../../backend
python manage.py runserver
```

### Step 5: Access the System
- **Home Page**: http://localhost:8000/
- **Report Page**: http://localhost:8000/report/submit/
- **Status Page**: http://localhost:8000/report/status/
- **Admin Panel**: http://localhost:8000/admin/

---

## 📝 User Guide

### Submitting a Report

1. Go to **http://localhost:8000/report/submit/**
2. Fill out the form:
   - **Incident Type**: Select from dropdown (Theft, Kidnapping, etc.)
   - **Description**: Detailed account of the incident
   - **Location**: Text description or GPS coordinates
   - **Media**: Optional images/videos (Max 10MB)
   - **Anonymous**: Check to report anonymously

3. Click **"Submit Report"**

4. System will:
   - Save report to database ✅
   - Upload media to IPFS 📦
   - Generate SHA-256 evidence hash 🔐
   - Anchor hash on Cardano blockchain ⛓️
   - Return reference code (e.g., `RRS-2025-00001`)

### Checking Report Status

1. Go to **http://localhost:8000/report/status/**
2. Enter your reference code (e.g., `RRS-2025-00001`)
3. View:
   - **Status**: New → In Review → Forwarded → Actioned → Closed
   - **Blockchain**: Confirmation status
   - **Evidence**: IPFS link and hash verification
   - **Submission Date**: When report was filed

### Admin Dashboard

Access at **http://localhost:8000/admin/**

Features:
- View all reports
- Filter by category, status, date
- Mark as reviewed/forwarded
- Export reports
- Manage users

---

## 🔗 API Endpoints

### Report Submission
```
POST /api/report/submit/
Content-Type: multipart/form-data

Parameters:
- category: string (theft, kidnapping, corruption, house_fire, road_accident, other)
- description: string (required, min 10 chars)
- location_description: string
- latitude: float (optional)
- longitude: float (optional)
- is_anonymous: boolean
- reporter_name: string (optional)
- reporter_phone: string (optional)
- reporter_email: string (optional)
- media_file: file (optional, max 10MB)

Response:
{
  "success": true,
  "reference_code": "RRS-2025-00001",
  "message": "Report submitted successfully!"
}
```

### Check Report Status
```
GET /api/report/status/RRS-2025-00001/

Response:
{
  "success": true,
  "data": {
    "reference_code": "RRS-2025-00001",
    "status": "in_review",
    "category": "theft",
    "description": "...",
    "evidence_hash": "a1b2c3d4...",
    "blockchain": {
      "status": "confirmed",
      "transaction_hash": "tx_hash...",
      "confirmations": 1
    }
  }
}
```

### Check Blockchain Status
```
GET /api/blockchain/status/RRS-2025-00001/

Response:
{
  "success": true,
  "blockchain_status": {
    "report_id": "RRS-2025-00001",
    "tx_hash": "...",
    "confirmations": 1,
    "status": "confirmed",
    "network": "preview"
  }
}
```

### Verify Evidence
```
POST /api/blockchain/verify/RRS-2025-00001/

Response:
{
  "success": true,
  "evidence_verified": true,
  "blockchain_hash": "a1b2c3d4...",
  "confirmations": 1
}
```

---

## ⛓️ Blockchain Integration

### Smart Contract

Located in `blockchain/rrs-contract/lib/lib.ak`

**Validation Functions:**

```aiken
// Validates SHA-256 hashes
pub fn validate_sha256_hash(hash: ByteArray) -> Bool { ... }

// Validates report ID format
pub fn validate_report_id(report_id: ByteArray) -> Bool { ... }

// Validates incident category
pub fn validate_category(category: ByteArray) -> Bool { ... }

// Validates timestamp is within acceptable range
pub fn validate_timestamp_range(timestamp, current_time, max_age) -> Bool { ... }

// Validates evidence anchor
pub fn validate_anchor_params(...) -> Bool { ... }

// Validates evidence verification
pub fn validate_verify_params(...) -> Bool { ... }
```

### Building & Testing

```bash
cd blockchain/rrs-contract

# Build contract
aiken build

# Run tests
aiken check

# Generate blueprint
aiken build --output plutus.json
```

### Deployment to Cardano

1. **Preview Testnet** (testing):
   - Use for development/testing
   - Free test ADA available
   - Network: `preview`

2. **Mainnet** (production):
   - Real ADA required
   - Permanent records
   - Network: `mainnet`

---

## 🔒 Security Features

### Evidence Protection
- ✅ SHA-256 hashing ensures integrity
- ✅ IPFS immutability prevents tampering
- ✅ Blockchain timestamp proves creation date
- ✅ Smart contract validates all inputs

### Anonymity
- ✅ Anonymous reporting option
- ✅ No IP logging
- ✅ Encrypted storage
- ✅ Admin access logging

### Data Privacy
- ✅ GDPR compliant data retention
- ✅ User consent required
- ✅ Secure password hashing
- ✅ HTTPS recommended for production

---

## 📊 Database Schema

### Reports Table
```sql
├── id (UUID Primary Key)
├── reference_code (Unique, e.g., RRS-2025-00001)
├── category (theft, kidnapping, corruption, ...)
├── description (Text)
├── latitude / longitude (GPS Coordinates)
├── media_file (Path to uploaded file)
├── ipfs_cid (IPFS content hash)
├── evidence_hash (SHA-256 of evidence)
├── transaction_hash (Cardano tx hash)
├── is_hash_anchored (Boolean)
├── verified_on_chain (Boolean)
├── status (new, in_review, forwarded, actioned, closed)
├── is_anonymous (Boolean)
├── reporter_name / phone / email
├── created_at / updated_at (Timestamps)
└── blockchain_metadata (JSON)
```

### BlockchainAnchor Table
```sql
├── id (UUID Primary Key)
├── report_id (Foreign Key to Report)
├── evidence_hash (SHA-256 hash)
├── ipfs_cid (IPFS content identifier)
├── transaction_hash (Cardano tx hash)
├── block_number (Block height on chain)
├── confirmations (Number of confirmations)
├── status (pending, submitted, confirmed, failed)
├── network (preview or mainnet)
├── metadata (JSON with anchor data)
└── created_at / confirmed_at (Timestamps)
```

---

## 🛠️ Troubleshooting

### Database Issues
```bash
# Reset database
python manage.py migrate --zero reports
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### IPFS Issues
```bash
# Start IPFS daemon
ipfs daemon

# Check IPFS connectivity
curl http://localhost:5001/api/v0/id
```

### Smart Contract Issues
```bash
# Verify contract compilation
aiken build

# Check for syntax errors
aiken check --strict
```

### Django Issues
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check dependencies
pip install -r requirements.txt --upgrade

# Run tests
python manage.py test
```

---

## 📦 Dependencies

### Backend
```
Django>=4.2
djangorestframework>=3.14
django-cors-headers>=4.0
django-filter>=23.0
Pillow>=9.0
httpx>=0.24.0
```

### Blockchain
```
aiken>=1.0.0
cardano-py>=0.16.0
blockfrost-python>=0.7.0
```

### Optional
```
ipfshttpclient>=0.8.0
celery>=5.0  # For async tasks
redis>=4.0  # For Celery broker
```

---

## 📚 Additional Resources

- **Cardano Docs**: https://developers.cardano.org/
- **Aiken Language**: https://aiken-lang.org/
- **IPFS**: https://ipfs.io/
- **Django REST**: https://www.django-rest-framework.org/
- **Blockfrost API**: https://blockfrost.io/

---

## 👥 Support & Contact

For issues or questions:
- GitHub Issues: [Create an issue]
- Email: support@rrs.rw
- Discord: [Join our community]

---

## 📄 License

Rwanda Report System is licensed under the **MIT License**.

See LICENSE file for details.

---

## ✅ Deployment Checklist

Before going live:

- [ ] Database migrations completed
- [ ] Smart contracts built and tested
- [ ] IPFS node running (or using remote gateway)
- [ ] Blockfrost API key configured
- [ ] HTTPS certificate installed
- [ ] Admin users created
- [ ] Backup strategy implemented
- [ ] Monitoring/logging configured
- [ ] User documentation prepared
- [ ] Support team trained

---

**Built for Cardano + Aiken Hackathon**

🇷🇼 Making Rwanda Safer Through Blockchain Technology
