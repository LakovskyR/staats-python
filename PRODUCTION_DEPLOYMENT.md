# STAATS Python - Production Deployment Guide for aplusa

## 🎯 Deployment Strategy

**Three-tier deployment for your team:**
1. **Internal Web App** - For analysts and non-technical users
2. **CLI Tool** - For automation and power users
3. **GitHub Repository** - For developers and version control

---

## 📋 Step 1: GitHub Repository Setup

### Create Repository

```bash
# On your machine
cd staats_python

# Initialize git
git init

# Create .gitignore (already provided)
# Files to exclude: output/, *.xlsx, __pycache__, etc.

# Add all files
git add .

# Initial commit
git commit -m "Initial commit: STAATS Python v1.0"

# Create GitHub repo (on github.com)
# Organization: aplusa or your personal account
# Repository name: staats-python
# Description: Professional survey data processing - 100x faster than Excel VBA
# Visibility: Private (for now)

# Connect and push
git remote add origin https://github.com/YOUR_ORG/staats-python.git
git branch -M main
git push -u origin main
```

### Repository Settings

**Protect main branch:**
- Settings → Branches → Add rule
- Branch name pattern: `main`
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging

**Add collaborators:**
- Settings → Collaborators
- Add aplusa team members

**Create project board:**
- Projects → New project → Board
- Columns: Backlog, In Progress, Review, Done

---

## 📋 Step 2: Local Development Setup

### For Each Developer

```bash
# 1. Clone repository
git clone https://github.com/YOUR_ORG/staats-python.git
cd staats-python

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Test installation
python demo.py
python complete_demo.py

# 6. Run web app
streamlit run app.py
# Opens at http://localhost:8501
```

### Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes
# ... edit files ...

# 3. Test changes
python demo.py

# 4. Commit changes
git add .
git commit -m "Add feature: description"

# 5. Push to GitHub
git push origin feature/your-feature-name

# 6. Create Pull Request on GitHub
# Review → Approve → Merge to main
```

---

## 📋 Step 3: Internal Web App Deployment

### Option A: Simple Shared Server (Easiest)

**Requirements:**
- Windows/Mac/Linux server in aplusa network
- Python 3.12+ installed
- Always-on machine

**Setup:**

```bash
# 1. Clone on server
git clone https://github.com/YOUR_ORG/staats-python.git
cd staats-python

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run as service (Windows)
# Create run_staats.bat:
@echo off
cd C:\path\to\staats-python
python -m venv venv
call venv\Scripts\activate
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
pause

# 4. Create Windows Task Scheduler job
# - Run run_staats.bat on system startup
# - Run as: SYSTEM or dedicated user

# 5. Configure Windows Firewall
# - Allow inbound port 8501

# 6. Share URL with team
# http://SERVER-IP:8501
```

**Linux/Mac:**

```bash
# Create systemd service
sudo nano /etc/systemd/system/staats.service

[Unit]
Description=STAATS Python Web App
After=network.target

[Service]
Type=simple
User=staats
WorkingDirectory=/opt/staats-python
ExecStart=/opt/staats-python/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable staats
sudo systemctl start staats
sudo systemctl status staats
```

### Option B: Docker Deployment (Recommended)

**Requirements:**
- Docker installed on server
- Docker Compose (optional)

**Setup:**

```bash
# 1. Clone repository
git clone https://github.com/YOUR_ORG/staats-python.git
cd staats-python

# 2. Build image
docker build -t staats-python:latest .

# 3. Run container
docker run -d \
  --name staats-web \
  -p 8501:8501 \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/temp:/app/temp \
  --restart unless-stopped \
  staats-python:latest

# 4. Check status
docker ps
docker logs staats-web

# Access at http://SERVER-IP:8501
```

**With Docker Compose:**

```bash
# Simply run
docker-compose up -d

# Update
git pull
docker-compose down
docker-compose up -d --build

# Logs
docker-compose logs -f
```

### Option C: Cloud Deployment

#### Google Cloud Run (Serverless - Auto-scaling)

```bash
# 1. Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# 2. Login
gcloud auth login

# 3. Set project
gcloud config set project YOUR_PROJECT_ID

# 4. Deploy
gcloud run deploy staats-python \
  --source . \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 300

# Returns URL: https://staats-python-XXX.run.app
```

**Costs:** ~€10-50/month depending on usage (pay per use)

#### AWS ECS (Elastic Container Service)

```bash
# 1. Install AWS CLI
# https://aws.amazon.com/cli/

# 2. Create ECR repository
aws ecr create-repository --repository-name staats-python

# 3. Build and push image
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.eu-west-1.amazonaws.com
docker build -t staats-python .
docker tag staats-python:latest YOUR_ACCOUNT.dkr.ecr.eu-west-1.amazonaws.com/staats-python:latest
docker push YOUR_ACCOUNT.dkr.ecr.eu-west-1.amazonaws.com/staats-python:latest

# 4. Create ECS cluster and service (via AWS Console)
# - Fargate launch type
# - 1 vCPU, 2GB RAM
# - Port 8501
# - Application Load Balancer
```

**Costs:** ~€30-100/month for always-on

#### Azure Container Apps

```bash
# 1. Install Azure CLI
az login

# 2. Create resource group
az group create --name staats-rg --location westeurope

# 3. Create container app
az containerapp up \
  --name staats-python \
  --resource-group staats-rg \
  --location westeurope \
  --source . \
  --target-port 8501 \
  --ingress external

# Returns URL: https://staats-python.XXXXX.westeurope.azurecontainerapps.io
```

**Costs:** ~€20-80/month

---

## 📋 Step 4: CLI Tool for Automation

### Install Globally

```bash
# Option 1: Add to PATH
# Copy staats_cli.py to a directory in PATH
cp staats_cli.py /usr/local/bin/staats
chmod +x /usr/local/bin/staats

# Option 2: Create alias
echo 'alias staats="python /path/to/staats-python/staats_cli.py"' >> ~/.bashrc
source ~/.bashrc

# Usage
staats process survey.csv config.json -o results.xlsx
```

### Scheduled Jobs (Automation)

**Windows Task Scheduler:**

```batch
REM Create weekly_report.bat
@echo off
cd C:\path\to\staats-python
call venv\Scripts\activate

REM Download latest data from network drive
copy \\network\surveys\latest.csv data\current.csv

REM Process
python staats_cli.py process data\current.csv config\weekly.json -o output\weekly_report.xlsx

REM Email results (using PowerShell)
powershell -File send_report.ps1

REM Create Task Scheduler job:
REM - Trigger: Weekly, Monday 9:00 AM
REM - Action: Run weekly_report.bat
```

**Linux Cron:**

```bash
# Edit crontab
crontab -e

# Add job (runs Monday 9 AM)
0 9 * * 1 /opt/staats-python/run_weekly.sh

# run_weekly.sh
#!/bin/bash
cd /opt/staats-python
source venv/bin/activate
python staats_cli.py process /data/latest.csv /config/weekly.json -o /output/weekly_report.xlsx
# Email results
mail -s "Weekly Report" team@aplusa.com < /output/weekly_report.xlsx
```

---

## 📋 Step 5: Team Training

### Training Sessions

**Session 1: Web App Users (1 hour)**
- Target: Analysts, managers
- Content:
  - Upload data
  - Configure questions
  - Create recodes
  - Generate tabs
  - Download Excel

**Session 2: Power Users (2 hours)**
- Target: Senior analysts, data processors
- Content:
  - Python basics
  - CLI tool usage
  - Configuration files
  - Automation

**Session 3: Developers (3 hours)**
- Target: IT team
- Content:
  - Code architecture
  - GitHub workflow
  - Adding features
  - Deployment

### Documentation

**Create internal wiki:**
- How to upload data
- Common recode patterns
- Troubleshooting guide
- FAQ

---

## 📋 Step 6: Migration Plan

### Phase 1: Parallel Running (Month 1)
- Keep using Excel STAATS
- Run same analyses in STAATS Python
- Compare outputs
- Build confidence

### Phase 2: Pilot Project (Month 2)
- Select 2-3 studies to run entirely in Python
- Full team involved
- Document issues
- Refine workflows

### Phase 3: Full Migration (Month 3)
- All new studies use Python
- Excel STAATS for legacy only
- Full team trained
- Automated reports live

### Phase 4: Optimization (Month 4+)
- Add custom features
- Integrate with other systems
- Advanced automation
- Performance tuning

---

## 📋 Step 7: Monitoring & Maintenance

### Health Checks

**Web App:**
```bash
# Check if running
curl http://SERVER:8501/_stcore/health

# Restart if needed
docker restart staats-web
# or
systemctl restart staats
```

**Automated monitoring:**
```bash
# Create monitor.sh
#!/bin/bash
if ! curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo "STAATS web app is down, restarting..."
    docker restart staats-web
    echo "Alert: STAATS restarted" | mail -s "STAATS Alert" admin@aplusa.com
fi

# Add to cron (every 5 minutes)
*/5 * * * * /opt/staats-python/monitor.sh
```

### Updates

```bash
# 1. Pull latest code
cd staats-python
git pull origin main

# 2. Update dependencies
pip install -r requirements.txt --upgrade

# 3. Test
python demo.py

# 4. Restart service
docker-compose down
docker-compose up -d --build
# or
systemctl restart staats
```

### Backups

```bash
# Configuration files
cp -r config/ backup/config_$(date +%Y%m%d)/

# Database/outputs
tar -czf backup_$(date +%Y%m%d).tar.gz output/

# Automate
0 2 * * * /opt/staats-python/backup.sh
```

---

## 📋 Step 8: Security Considerations

### Access Control

**Web App:**
- Add authentication (Streamlit doesn't have built-in auth)
- Use reverse proxy (Nginx) with basic auth
- VPN for external access

**Nginx reverse proxy with auth:**

```nginx
# /etc/nginx/sites-available/staats
server {
    listen 80;
    server_name staats.aplusa.internal;

    auth_basic "STAATS Login";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}

# Create password file
sudo htpasswd -c /etc/nginx/.htpasswd username
```

### Data Privacy

- **Never commit sensitive data** to GitHub
- Use `.gitignore` properly
- Store configs in separate private repo
- Use environment variables for credentials

```bash
# .env file (not in git)
DATABASE_URL=postgresql://...
API_KEY=secret...

# Load in Python
import os
from dotenv import load_dotenv
load_dotenv()

db_url = os.getenv('DATABASE_URL')
```

---

## 📋 Step 9: Cost Estimation

### Cloud Deployment Costs

| Option | Setup Time | Monthly Cost | Pros | Cons |
|--------|------------|--------------|------|------|
| Internal Server | 2 hours | €0 | Free, full control | Requires hardware |
| Google Cloud Run | 1 hour | €10-50 | Serverless, auto-scale | Pay per use |
| AWS ECS | 4 hours | €30-100 | Reliable, integrated | Always-on cost |
| Azure Container Apps | 2 hours | €20-80 | Easy, Microsoft stack | Learning curve |

### Total Cost of Ownership

**First Year:**
- Development: Already done ✅
- Deployment: 1-2 days (€0-1000 depending on option)
- Training: 2 days (€500-2000)
- Hosting: €0-1200/year
- **Total: €500-4200**

**Time Savings:**
- 2-3 hours → 5 minutes per study
- 95% efficiency gain
- **ROI in first month** if processing 10+ studies/month

---

## 📋 Step 10: Next Steps Checklist

### Week 1: GitHub Setup
- [ ] Create GitHub repository
- [ ] Push code to GitHub
- [ ] Add team as collaborators
- [ ] Set up branch protection
- [ ] Create project board

### Week 2: Local Testing
- [ ] Clone to 3 team machines
- [ ] Install dependencies
- [ ] Run demos
- [ ] Test with real data
- [ ] Document any issues

### Week 3: Deployment
- [ ] Choose deployment option
- [ ] Set up internal web app
- [ ] Configure CLI for automation
- [ ] Create monitoring
- [ ] Document URLs/access

### Week 4: Training & Migration
- [ ] Train web app users
- [ ] Train power users
- [ ] Train developers
- [ ] Start parallel running
- [ ] Select pilot projects

### Month 2+: Production
- [ ] Full migration
- [ ] Automated reports
- [ ] Custom features
- [ ] Performance optimization

---

## 🎯 Recommended Path for aplusa

**Start Simple, Scale Smart:**

1. **This Week:**
   - Create GitHub repo
   - Install on 2-3 machines
   - Test with sample data

2. **Next Week:**
   - Deploy web app on internal server (Docker)
   - Share URL with team
   - Run first real study

3. **Month 2:**
   - Train full team
   - Migrate 50% of studies
   - Set up automation

4. **Month 3:**
   - Full production
   - Cloud deployment (if needed)
   - Advanced features

**Low risk, high reward. Start today.** 🚀

---

## 🆘 Support & Troubleshooting

### Common Issues

**Issue: "Module not found"**
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Issue: "Port 8501 already in use"**
```bash
# Solution: Use different port
streamlit run app.py --server.port=8502
```

**Issue: "Permission denied"**
```bash
# Solution: Check file permissions
chmod +x staats_cli.py
```

**Issue: "Out of memory"**
```bash
# Solution: Increase Docker memory
docker run --memory=4g staats-python
```

### Getting Help

1. Check GitHub Issues
2. Review documentation
3. Contact team lead
4. Create support ticket

---

**Ready to modernize aplusa's data processing?** Let's do this. 💪🔥
