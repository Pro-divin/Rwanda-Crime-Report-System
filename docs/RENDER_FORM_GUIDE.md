# Render Deployment Form - Step-by-Step Guide

This guide shows you exactly what to enter in each field on the Render dashboard.

---

## 📝 Form Fields - What to Enter

### 1. **Name**
**Field:** "A unique name for your web service"

**Enter:**
```
rrs-presentation
```
(or any name you prefer, e.g., `rrs-demo`, `rwanda-crime-reports`)

---

### 2. **Project** (Optional)
**Field:** "Add this web service to a project once it's created"

**Enter:**
```
Rwanda Crime report system
```
(Leave as is - it's already set)

---

### 3. **Environment**
**Field:** "Choose the runtime environment"

**Select:**
```
Python 3
```
(Already selected - good!)

---

### 4. **Branch**
**Field:** "The Git branch to build and deploy"

**Select:**
```
main
```
(Already selected - correct!)

---

### 5. **Region**
**Field:** "Your services in the same region can communicate..."

**Select:**
```
Oregon (US West)
```
(Current selection is fine, or choose your region)

---

### 6. **Root Directory** (Optional)
**Field:** "If set, Render runs commands from this directory..."

**Enter:**
```
backend
```

**Why?** Your Django app is in the `backend/` folder, not root.

---

### 7. **Build Command** ⭐ IMPORTANT
**Field:** "Render runs this command to build your app..."

**Replace the default with:**
```
pip install -r backend/requirements.txt && cd backend && python manage.py migrate --noinput && python manage.py collectstatic --noinput
```

**Step by step:**
- `pip install -r backend/requirements.txt` - Install Python packages
- `cd backend` - Enter backend folder
- `python manage.py migrate --noinput` - Setup database
- `python manage.py collectstatic --noinput` - Collect static files (CSS, JS, images)

---

### 8. **Start Command** ⭐ IMPORTANT
**Field:** "Render runs this command to start your app..."

**Replace the default with:**
```
cd backend && gunicorn config.wsgi:application --bind 0.0.0.0:10000
```

**What it does:**
- `cd backend` - Go to backend folder
- `gunicorn config.wsgi:application` - Run Django with Gunicorn
- `--bind 0.0.0.0:10000` - Listen on port 10000 (Render requirement)

---

### 9. **Instance Type**
**Field:** "For hobby projects / For professional use"

**Select:**
```
Free
```
(For testing/demo. Choose "Starter" ($7/mo) for production)

---

### 10. **Environment Variables** ⭐ CRITICAL
**Field:** "Set environment-specific config and secrets..."

**Add EACH variable by clicking "Add Environment Variable":**

#### Variable 1: DEBUG
| Field | Value |
|-------|-------|
| NAME | `DEBUG` |
| VALUE | `False` |

#### Variable 2: SECRET_KEY
| Field | Value |
|-------|-------|
| NAME | `SECRET_KEY` |
| VALUE | `Pz3H|8K8M^v#nQ3z}Ym;1neWyfcSqssp+$1f;f5GMBl^]dLMvV` |

#### Variable 3: ALLOWED_HOSTS
| Field | Value |
|-------|-------|
| NAME | `ALLOWED_HOSTS` |
| VALUE | `*.render.com,localhost,127.0.0.1` |

#### Variable 4: BLOCKFROST_PROJECT_ID
| Field | Value |
|-------|-------|
| NAME | `BLOCKFROST_PROJECT_ID` |
| VALUE | `your-blockfrost-api-key-here` |

**How to get Blockfrost key:**
1. Go to https://blockfrost.io
2. Sign up (free)
3. Create a project → Get API key
4. Copy and paste here

#### Variable 5: ANCHOR_BROADCAST
| Field | Value |
|-------|-------|
| NAME | `ANCHOR_BROADCAST` |
| VALUE | `False` |

**Note:** For demo, keep `False`. When ready for production, change to `True` (requires valid Blockfrost key and IPFS running).

#### Variable 6: DATABASE_URL
| Field | Value |
|-------|-------|
| NAME | `DATABASE_URL` |
| VALUE | Leave empty - Render auto-generates this |

---

## 🎯 Summary - Quick Checklist

```
[ ] Name: rrs-presentation
[ ] Environment: Python 3
[ ] Branch: main
[ ] Region: Oregon (or your choice)
[ ] Root Directory: backend
[ ] Build Command: (see above - long command with migrate + collectstatic)
[ ] Start Command: (see above - cd backend && gunicorn...)
[ ] Instance Type: Free
[ ] Environment Variables (6 total):
    [ ] DEBUG = False
    [ ] SECRET_KEY = Pz3H|8K8M^v#nQ3z}Ym;1neWyfcSqssp+$1f;f5GMBl^]dLMvV
    [ ] ALLOWED_HOSTS = *.render.com,localhost,127.0.0.1
    [ ] BLOCKFROST_PROJECT_ID = (your key)
    [ ] ANCHOR_BROADCAST = False
    [ ] DATABASE_URL = (leave empty)
```

---

## 🚀 Final Step

**Once all fields are filled in correctly:**

1. Scroll to bottom
2. Click **"Deploy Web Service"** button
3. Wait 5-10 minutes for deployment
4. You'll get a live URL like: `https://rrs-presentation.onrender.com`

---

## ✅ Verify Deployment Works

After deployment completes:

1. **Check if site loads:**
   ```
   https://rrs-presentation.onrender.com
   ```

2. **Create admin user in Render Shell:**
   - Go to your service in Render
   - Click "Shell" tab
   - Run: `python backend/manage.py createsuperuser`
   - Create username/password

3. **Login to admin:**
   ```
   https://rrs-presentation.onrender.com/admin
   ```

4. **Test API:**
   ```
   https://rrs-presentation.onrender.com/api/reports/
   ```

---

## 🆘 Common Mistakes to Avoid

❌ **Wrong Build Command** → Database won't migrate
- ✅ Use: `pip install -r backend/requirements.txt && cd backend && python manage.py migrate --noinput && python manage.py collectstatic --noinput`

❌ **Wrong Start Command** → App won't start
- ✅ Use: `cd backend && gunicorn config.wsgi:application --bind 0.0.0.0:10000`

❌ **Missing Root Directory** → Can't find requirements.txt
- ✅ Set to: `backend`

❌ **Empty SECRET_KEY** → Site crashes
- ✅ Use: `Pz3H|8K8M^v#nQ3z}Ym;1neWyfcSqssp+$1f;f5GMBl^]dLMvV`

❌ **DEBUG = True** → Security risk
- ✅ Use: `False`

---

## 📞 Need Help?

- Check Render logs: Service → **Logs** tab
- Common error: `CommandError: No such table` → Run migrate in Shell
- See: `RENDER_DEPLOYMENT.md` in your repo

---

**You're ready! Follow this guide and your site will be live in ~20 minutes! 🚀**
