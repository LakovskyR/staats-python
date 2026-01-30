# 🚀 STAATS Python - Quick Deploy Instructions

## What You Downloaded

Complete STAATS Python system (27 files):
- ✅ Web app, CLI tool, Python API
- ✅ All documentation
- ✅ Automated deployment script
- ✅ Sample data and demos

---

## 📦 Step 1: Extract the ZIP File (30 seconds)

1. **Right-click** `staats-python-complete.zip`
2. **Click** "Extract All..."
3. **Choose location:** Your Documents or Projects folder
4. **Extract** to create `staats_python` folder

---

## 🚀 Step 2: Run Automated Deployment (5 minutes)

Open Command Prompt (cmd) or PowerShell and run:

```cmd
cd C:\path\to\staats_python
DEPLOY.bat
```

**This script will automatically:**
1. ✅ Initialize Git
2. ✅ Push code to GitHub (you'll need to enter credentials)
3. ✅ Install Python dependencies
4. ✅ Start Streamlit web app

**Opens at:** http://localhost:8501

---

## 🔑 GitHub Credentials

When prompted during push:
- **Username:** `LakovskyR`
- **Password:** Your Personal Access Token (NOT your GitHub password)

**Don't have a token?**
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: "STAATS Python"  
4. Select scope: ✅ **repo** (all sub-options)
5. Click "Generate token"
6. **Copy immediately** (you won't see it again!)
7. Use as password when pushing

---

## ✅ Verify It Works

After DEPLOY.bat completes:

1. **Web app opens** in browser at http://localhost:8501
2. **Click "📁 Load Data"** → "📊 Load Sample Data"
3. **Click "🗺️ Configure"** → "🔍 Auto-Detect Question Types"
4. **Click "📊 Analyze"** → Create a cross-tab → Generate
5. **Click "💾 Export"** → Download Excel file

**If all 5 steps work → Success!** 🎉

---

## 👥 Share with Your Team

To let team members access the web app:

### Find Your IP Address:
```cmd
ipconfig
```
Look for "IPv4 Address"

### Restart with Network Access:
```cmd
cd C:\path\to\staats_python
streamlit run app.py --server.address=0.0.0.0
```

**Share URL:** `http://YOUR-IP:8501`

---

## 📖 Full Documentation

Inside the `staats_python` folder:

| File | Purpose |
|------|---------|
| `PUSH_AND_DEPLOY.md` | Detailed deployment guide |
| `START_HERE.md` | Quick start guide |
| `COMPLETE_GUIDE.md` | Full usage instructions |
| `PRODUCTION_DEPLOYMENT.md` | Production options |

---

## 🆘 Troubleshooting

### "git: command not found"
**Install Git:** https://git-scm.com/downloads

### "python: command not found"  
**Install Python 3.12+:** https://www.python.org/downloads/

### "streamlit: command not found"
```cmd
pip install streamlit
```

### Port 8501 already in use
```cmd
streamlit run app.py --server.port=8502
```

---

## 🎯 What's Next?

**TODAY:**
- ✅ Extract ZIP
- ✅ Run DEPLOY.bat
- ✅ Test with sample data

**THIS WEEK:**
- Share with 3 team members
- Process first real study
- Document time savings

**NEXT WEEK:**
- Train full team
- Migrate 50% of studies  
- Set up automation

---

## 💪 Bottom Line

**You have everything you need to replace Excel STAATS.**

**Next 5 minutes:**
1. Extract ZIP
2. Run DEPLOY.bat
3. Test it works

**Done!** You're processing surveys 100x faster. 🚀

---

**Questions?** Check the documentation files in the folder or visit:
https://github.com/LakovskyR/staats-python
