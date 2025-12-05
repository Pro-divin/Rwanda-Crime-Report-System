# 🚀 DEPLOYMENT CHECKLIST - Rwanda Crime Report System

## ✅ COMPLETED STEPS

- [x] Code cleaned and pushed to GitHub
- [x] Test files removed
- [x] `render.yaml` configuration created
- [x] `Procfile` created for deployment
- [x] Production documentation ready
- [x] SECRET_KEY generated: `Pz3H|8K8M^v#nQ3z}Ym;1neWyfcSqssp+$1f;f5GMBl^]dLMvV`

---

## 🎯 NEXT STEPS - DO THIS NOW TO GO LIVE

### 1. Create Render Account (2 minutes)
- Go to https://render.com
- Click "Sign up"
- Select "Sign up with GitHub"
- Authorize Render

### 2. Deploy Your App (5 minutes)
- In Render dashboard: **New +** → **Web Service**
- Select repository: `Rwanda-Crime-Report-System`
- Fill in:
  - **Name:** `rrs-presentation`
  - **Environment:** Python 3.11
  - **Build Command:** `pip install -r backend/requirements.txt && cd backend && python manage.py migrate --noinput && python manage.py collectstatic --noinput`
  - **Start Command:** `cd backend && gunicorn config.wsgi:application --bind 0.0.0.0:10000`
  - **Plan:** Free

### 3. Set Environment Variables (3 minutes)
Click "Advanced" and add:

```
DEBUG=False
SECRET_KEY=Pz3H|8K8M^v#nQ3z}Ym;1neWyfcSqssp+$1f;f5GMBl^]dLMvV
ALLOWED_HOSTS=*.render.com
BLOCKFROST_PROJECT_ID=your-blockfrost-key
ANCHOR_BROADCAST=False
```

### 4. Click "Create Web Service"
- Render automatically builds and deploys
- Wait 5-10 minutes for deployment
- You'll get a live URL!

### 5. Create Admin User (2 minutes)
- In Render dashboard → Your service → Shell tab
- Run: `python backend/manage.py createsuperuser`
- Create username: `admin` password: `your-choice`

### 6. Test It Works
```
https://rrs-presentation.onrender.com/admin
```
(Use admin credentials you just created)

---

## 📊 What Gets Deployed

| Component | Status |
|-----------|--------|
| Django Backend | ✅ Ready |
| PostgreSQL Database | ✅ Auto-created by Render |
| REST API | ✅ Working |
| Admin Dashboard | ✅ Ready |
| IPFS Integration | ✅ Ready (simulated mode) |
| Blockchain Integration | ✅ Ready (Preview Testnet) |
| Static Files | ✅ Will be collected |
| Media Storage | ⚠️ Limited (use Render's blob storage) |

---

## 🔑 Important Details

**Your GitHub Repo:** https://github.com/Pro-divin/Rwanda-Crime-Report-System

**Deployment Files Included:**
- `render.yaml` - Render configuration
- `Procfile` - Server startup command
- `RENDER_DEPLOYMENT.md` - Detailed instructions
- `docs/DEPLOYMENT_GUIDE.md` - Comprehensive guide

**Auto-Redeployment:**
Every time you push to GitHub, Render automatically redeploys!

```bash
git add .
git commit -m "Your changes"
git push origin main
# Render redeploys in ~2 minutes automatically
```

---

## 📝 Demo Data (Optional)

To create demo reports for your presentation, use the admin panel:
1. Go to `/admin`
2. Create Users (optional)
3. Create Reports with details
4. Upload media files
5. View on dashboard

Or run this script locally to pre-populate data:

```python
# Script to create demo data
python backend/manage.py shell

from django.contrib.auth.models import User
from apps.reports.models import Report

# Create a demo report
user = User.objects.create_user('demo', 'demo@example.com', 'demo123')
report = Report.objects.create(
    category='theft',
    description='Demo report for presentation',
    location_description='Kigali City Center',
    latitude='-1.9553',
    longitude='29.8739',
    user=user,
    is_anonymous=False
)
print(f"Created: {report.reference_code}")
```

---

## 🎬 Live Presentation Flow

Once deployed, show:

1. **Citizen Portal** - Submit a report
   ```
   https://rrs-presentation.onrender.com/submit
   ```

2. **Dashboard** - View analytics and map
   ```
   https://rrs-presentation.onrender.com/dashboard
   ```

3. **Admin Panel** - Manage reports
   ```
   https://rrs-presentation.onrender.com/admin
   ```

4. **Integrity Check** - Verify report hasn't been tampered
   ```
   Click "Verify Integrity" on any report
   ```

5. **Blockchain Record** - Show on Cardano Testnet
   ```
   https://preview.cexplorer.io/ (search for tx hash)
   ```

---

## ⏱️ Timeline

| Task | Time | Cumulative |
|------|------|-----------|
| Create Render account | 2 min | 2 min |
| Deploy app | 5 min | 7 min |
| Set environment vars | 3 min | 10 min |
| Wait for build | 5-10 min | 15-20 min |
| Create admin user | 2 min | 17-22 min |
| **LIVE!** | ✅ | **~20 minutes** |

---

## 🆘 Quick Troubleshooting

**Site shows blank/error?**
→ Check Logs in Render dashboard

**Database error?**
→ Run in Render Shell: `python backend/manage.py migrate`

**Static files not loading?**
→ Run in Render Shell: `python backend/manage.py collectstatic --noinput`

**Can't login to admin?**
→ Recreate superuser in Render Shell

For more help: See `RENDER_DEPLOYMENT.md` in root directory

---

## 📞 Render Support

- **Render Docs:** https://render.com/docs
- **Render Support:** https://render.com/support
- **Status Page:** https://render-status.com

---

## ✨ You're Ready to Go Live!

Your project is deployment-ready. The only thing left is:

1. ✅ Go to https://render.com
2. ✅ Sign up with GitHub
3. ✅ Follow the steps above
4. ✅ Share your live URL with the world

**Estimated time to go live: 20 minutes**

---

**Built with ❤️ for Rwanda 🇷🇼**

Good luck with your presentation! 🚀
