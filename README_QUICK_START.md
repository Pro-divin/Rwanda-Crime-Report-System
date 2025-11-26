# 🇷🇼 Rwanda Report System - Quick Start (5 Minutes)

## What is this?

A **blockchain-powered reporting platform** that allows Rwandan citizens to report crimes securely. Evidence is anchored on Cardano blockchain and stored on IPFS.

---

## ⚡ Quick Start

### 1. Install Dependencies (2 min)

```bash
# Navigate to project
cd "C:\Users\peril ops\Desktop\RRS"

# Install Python packages
cd backend
pip install -r requirements.txt

# Install Aiken (if not already installed)
# Follow: https://aiken-lang.org/getting-started
```

### 2. Setup Database (1 min)

```bash
cd backend
python manage.py migrate
python manage.py createsuperuser
# Username: admin
# Password: (create your own)
```

### 3. Build Smart Contract (1 min)

```bash
cd blockchain/rrs-contract
aiken build
```

### 4. Start Server (1 min)

```bash
cd backend
python manage.py runserver
```

### 5. Access the System

- **Home**: http://localhost:8000/
- **Report**: http://localhost:8000/report/submit/
- **Status**: http://localhost:8000/report/status/
- **Admin**: http://localhost:8000/admin/

---

## 📝 How It Works

```
Citizen submits report
         ↓
Django validates & saves
         ↓
Media uploaded to IPFS 📦
         ↓
Evidence hash generated 🔐
         ↓
Hash anchored on Cardano ⛓️
         ↓
Reference code returned
         ↓
Citizen checks status anytime
```

---

## 🧪 Test It

```bash
# Run complete system test
python test_system.py
```

Expected output:
```
✅ Django Setup
✅ API Endpoints
✅ Blockchain Utilities
✅ Database Models
✅ REST Serializers
✅ Smart Contracts
✅ Report Submission

🎉 ALL TESTS PASSED!
```

---

## 📊 Default Credentials

- **Admin Panel**: http://localhost:8000/admin/
- **Username**: admin
- **Password**: (what you set during setup)

---

## 🔗 API Examples

### Submit Report

```bash
curl -X POST http://localhost:8000/api/report/submit/ \
  -F "category=theft" \
  -F "description=Stolen motorbike from my home" \
  -F "location_description=Gisozi, Kigali" \
  -F "is_anonymous=true"
```

Response:
```json
{
  "success": true,
  "reference_code": "RRS-2025-00001",
  "message": "Report submitted successfully!"
}
```

### Check Status

```bash
curl http://localhost:8000/api/report/status/RRS-2025-00001/
```

### Verify on Blockchain

```bash
curl -X POST http://localhost:8000/api/blockchain/verify/RRS-2025-00001/
```

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
python manage.py runserver 8001
```

### Reset Database

```bash
cd backend
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Build Errors

```bash
cd blockchain/rrs-contract
aiken build --strict
```

### IPFS Not Available

The system works without IPFS using simulated CIDs. Install IPFS Desktop for production.

---

## 📚 Full Documentation

See `SETUP_GUIDE.md` for complete details:
- Architecture overview
- Database schema
- All API endpoints
- Blockchain deployment
- Security features
- Troubleshooting

---

## 🎯 Key Features

✅ **Secure Reporting** - Encrypted submission
✅ **Anonymous Option** - Privacy preserved
✅ **Blockchain Anchored** - Tamper-proof evidence
✅ **GPS Tracking** - Incident location
✅ **Media Support** - Photos/videos
✅ **Reference Tracking** - Status updates
✅ **Admin Dashboard** - Review reports
✅ **IPFS Integration** - Distributed storage

---

## 🔐 Data Flow

```
User Input
    ↓
Frontend Validation
    ↓
Django API
    ↓
┌─────────────┬──────────────┬────────────────┐
├─ Database  │ IPFS Storage │ Cardano Chain │
└─────────────┴──────────────┴────────────────┘
    ↓
Public Reference Code
    ↓
User Can Verify Evidence
```

---

## 📞 Support

- **Issues**: Check console for error messages
- **Logs**: `python manage.py runserver` shows errors in real-time
- **Admin**: Access http://localhost:8000/admin/ to view/manage reports
- **Tests**: Run `python test_system.py` to verify all components

---

## ✅ What's Included

```
RRS/
├── backend/              # Django API
│   ├── apps/
│   │   ├── reports/      # Report submission & status
│   │   ├── blockchain/   # Cardano integration
│   │   ├── users/        # Authentication
│   │   └── dashboard/    # Admin interface
│   ├── config/           # Django settings
│   ├── db.sqlite3        # Database (created on first run)
│   └── manage.py
├── blockchain/           # Aiken smart contracts
│   └── rrs-contract/     # Smart contract source
├── static/               # Frontend files
│   └── index.html
├── SETUP_GUIDE.md        # Complete documentation
├── README_QUICK_START.md # This file
└── test_system.py        # System verification
```

---

## 🚀 Next Steps

1. ✅ Run quick start (you are here)
2. 📖 Read `SETUP_GUIDE.md` for full documentation
3. 🔌 Configure Blockfrost for Cardano testnet
4. ⛓️ Deploy smart contract to Cardano
5. 👥 Create admin users for your team
6. 🌐 Configure domain for production
7. 🔒 Set up HTTPS certificate
8. 📊 Monitor reports and statistics

---

## 📄 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

Built for the **Cardano + Aiken Hackathon**

Technologies:
- Cardano Blockchain
- Aiken Smart Contracts
- Django REST Framework
- IPFS Protocol
- Python/JavaScript

---

**🎉 Welcome to Rwanda Report System!**

Start reporting safely and securely today.

For detailed setup, see `SETUP_GUIDE.md`
