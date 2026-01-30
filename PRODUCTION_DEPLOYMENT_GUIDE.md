# STAATS Python - Production Deployment Guide

**Docker Deployment for aplusa Internal Server**

---

## Prerequisites

**Required:**
- Server with Docker installed (Ubuntu 20.04+ or Windows Server 2019+)
- 4GB RAM minimum, 8GB recommended
- 20GB disk space
- Git installed
- Network access to GitHub

**Optional:**
- Domain name for SSL
- nginx for load balancing
- Backup solution

---

## Quick Setup (15 Minutes)

### Step 1: Install Docker

**Ubuntu/Linux:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**Windows Server:**
- Download Docker Desktop from docker.com
- Install and restart server
- Verify: `docker --version`

### Step 2: Clone Repository

```bash
cd /opt  # or C:\apps on Windows
git clone https://github.com/LakovskyR/staats-python.git
cd staats-python
```

### Step 3: Start Application

```bash
docker-compose up -d
```

### Step 4: Verify

```bash
# Check status
docker-compose ps

# Check logs
docker-compose logs -f

# Test access
curl http://localhost:8501/_stcore/health
```

**Access:** http://SERVER-IP:8501

---

## Production Configuration

### docker-compose.yml

Replace default file with production config:

```yaml
version: '3.8'

services:
  staats-web:
    build: .
    ports:
      - "8501:8501"
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
      - STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
      - STREAMLIT_SERVER_ENABLE_CORS=false
    volumes:
      - ./output:/app/output
      - ./temp:/app/temp
      - ./assets:/app/assets:ro
    restart: always
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Streamlit Configuration

Create `.streamlit/config.toml`:

```toml
[server]
headless = true
port = 8501
enableCORS = false
maxUploadSize = 200
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[client]
showErrorDetails = false
toolbarMode = "minimal"

[theme]
primaryColor = "#C1272D"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

---

## Security Configuration

### Firewall Rules

**Ubuntu:**
```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

**Windows:**
```powershell
New-NetFirewallRule -DisplayName "STAATS HTTP" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "STAATS HTTPS" -Direction Inbound -LocalPort 443 -Protocol TCP -Action Allow
```

### Internal Network Only

To restrict access to internal network:

```bash
sudo ufw allow from 10.0.0.0/8 to any port 8501
```

### SSL/HTTPS Setup

**Option 1: nginx Reverse Proxy**

Create `/etc/nginx/sites-available/staats`:

```nginx
server {
    listen 80;
    server_name staats.aplusa.internal;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/staats /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**Option 2: Let's Encrypt SSL**

```bash
sudo apt-get install certbot
sudo certbot certonly --standalone -d staats.aplusa.com
```

Update nginx config:
```nginx
server {
    listen 443 ssl;
    server_name staats.aplusa.com;
    
    ssl_certificate /etc/letsencrypt/live/staats.aplusa.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staats.aplusa.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8501;
        # ... same proxy settings as above
    }
}
```

---

## Maintenance Commands

### Daily Operations

```bash
# View logs
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# Check resource usage
docker stats

# Restart service
docker-compose restart

# Stop service
docker-compose down

# Start service
docker-compose up -d
```

### Updates

```bash
# Pull latest code
cd /opt/staats-python
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Verify
docker-compose ps
docker-compose logs --tail=50
```

### Backup

```bash
# Create backup script: /opt/backup-staats.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/staats-python"

mkdir -p $BACKUP_DIR

# Backup output files
docker-compose exec -T staats-web tar -czf - /app/output > $BACKUP_DIR/data-$DATE.tar.gz

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "data-*.tar.gz" -mtime +30 -delete

echo "Backup complete: data-$DATE.tar.gz"
```

Make executable:
```bash
chmod +x /opt/backup-staats.sh
```

Add to crontab (daily at 2 AM):
```bash
crontab -e
# Add line:
0 2 * * * /opt/backup-staats.sh >> /var/log/staats-backup.log 2>&1
```

### Restore from Backup

```bash
# Stop service
docker-compose down

# Restore data
tar -xzf /backup/staats-python/data-YYYYMMDD_HHMMSS.tar.gz -C ./output

# Start service
docker-compose up -d
```

---

## Monitoring

### Health Check

```bash
# Application health
curl http://localhost:8501/_stcore/health

# Container status
docker-compose ps

# Resource usage
docker stats --no-stream

# Disk usage
df -h
du -sh /var/lib/docker/
```

### Log Monitoring

```bash
# Real-time logs
docker-compose logs -f

# Error logs only
docker-compose logs | grep -i error

# Last hour of logs
docker-compose logs --since 1h
```

### Alert Setup

Create `/opt/check-staats.sh`:

```bash
#!/bin/bash
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8501/_stcore/health)

if [ "$STATUS" != "200" ]; then
    echo "STAATS is DOWN - Status: $STATUS"
    # Send email or notification here
    systemctl restart docker-compose@staats-python
fi
```

Add to crontab (check every 5 minutes):
```bash
*/5 * * * * /opt/check-staats.sh
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8501
sudo lsof -i :8501
sudo netstat -tulpn | grep 8501

# Kill process
sudo kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8502:8501"
```

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Check docker service
sudo systemctl status docker

# Restart docker
sudo systemctl restart docker

# Remove old containers
docker-compose down
docker system prune -a
docker-compose up -d
```

### Memory Issues

```bash
# Check memory usage
free -h
docker stats

# Increase memory limit in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 8G
```

### Slow Performance

```bash
# Check disk space
df -h

# Clean docker cache
docker system prune -a

# Check CPU usage
top
docker stats
```

### Cannot Access from Network

```bash
# Check firewall
sudo ufw status

# Check docker network
docker network inspect bridge

# Verify container is running
docker-compose ps

# Check server IP
ip addr show
```

---

## Team Access

### Share with Team

**Option 1: Direct IP Access**
- URL: `http://SERVER-IP:8501`
- Share IP with team
- Ensure firewall allows internal network

**Option 2: Internal Domain**
- Set up DNS: `staats.aplusa.internal` → `SERVER-IP`
- URL: `http://staats.aplusa.internal`
- Configure nginx for cleaner URLs

**Option 3: Network Share**
```bash
# Run on server's IP address
streamlit run app.py --server.address=0.0.0.0

# Find server IP
ip addr show  # Linux
ipconfig      # Windows

# Share URL with team
http://YOUR-SERVER-IP:8501
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Docker installed and running
- [ ] Git installed
- [ ] Repository cloned
- [ ] Server has 4GB+ RAM
- [ ] Server has 20GB+ disk space
- [ ] Firewall configured
- [ ] Network access verified

### Deployment

- [ ] docker-compose.yml configured
- [ ] .streamlit/config.toml created
- [ ] Logo file in assets/ folder
- [ ] `docker-compose up -d` executed
- [ ] Container running: `docker-compose ps`
- [ ] Health check passing: `curl http://localhost:8501/_stcore/health`
- [ ] Web interface accessible
- [ ] Sample data loads successfully

### Post-Deployment

- [ ] SSL certificate installed (if external access)
- [ ] nginx configured (if using)
- [ ] Backup script created and scheduled
- [ ] Monitoring script created
- [ ] Team access verified
- [ ] Documentation updated with server IP/URL
- [ ] Team trained on new interface
- [ ] Disaster recovery plan documented

### Production Ready

- [ ] All tests passed with real data
- [ ] Performance verified (response time < 3 seconds)
- [ ] Backup/restore tested
- [ ] Failover plan documented
- [ ] Team onboarding complete
- [ ] Old Excel VBA process documented for reference

---

## Performance Targets

**Response Times:**
- Data upload: < 5 seconds
- Auto-detect config: < 3 seconds
- Recode calculation: < 5 seconds
- Cross-tab generation: < 10 seconds
- Excel export: < 15 seconds

**Capacity:**
- Concurrent users: 10-20
- Max upload size: 200 MB
- Max rows: unlimited (tested to 100,000)
- Uptime target: 99.5%

---

## Support Escalation

**Level 1 - Self Service:**
- Restart container: `docker-compose restart`
- Check logs: `docker-compose logs`
- Check documentation

**Level 2 - IT Support:**
- Server issues
- Network issues
- Backup/restore
- Performance problems

**Level 3 - Development Team:**
- Application bugs
- Feature requests
- Integration issues
- Code updates

**Emergency Contact:**
- Data Processing Team Lead
- IT Infrastructure Team
- Development Team (for critical bugs)

---

## Migration from Excel VBA

### Week 1: Parallel Testing
- [ ] Deploy Docker instance
- [ ] Process 3 studies in both systems
- [ ] Compare outputs (should match 100%)
- [ ] Verify time savings (target: 95%)
- [ ] Document any differences

### Week 2: Partial Migration
- [ ] Train 5 analysts
- [ ] Migrate 25% of studies to Python
- [ ] Keep Excel VBA running for fallback
- [ ] Monitor performance
- [ ] Gather feedback

### Week 3-4: Full Migration
- [ ] Train all analysts
- [ ] Migrate 100% of new studies
- [ ] Excel VBA available for emergency only
- [ ] Monitor system load
- [ ] Optimize as needed

### Week 5+: Optimization
- [ ] Decommission Excel VBA
- [ ] Archive old macros
- [ ] Full team on Python STAATS
- [ ] Collect metrics (time saved, crashes avoided)
- [ ] Plan future enhancements

---

## Metrics to Track

**Before Python STAATS:**
- Average processing time per study: ______ hours
- Excel crashes per week: ______
- Max dataset size: ______ rows
- Studies processed per analyst per week: ______

**After Python STAATS:**
- Average processing time per study: ______ minutes
- Application crashes per week: 0
- Max dataset size: unlimited
- Studies processed per analyst per week: ______

**Target Improvements:**
- Time reduction: 95%
- Crash rate reduction: 100%
- Capacity increase: 10x
- Analyst productivity: 3-5x

---

## Production Environment Details

**Record for your deployment:**

- Server hostname: ___________________
- Server IP: ___________________
- Access URL: ___________________
- Docker version: ___________________
- Deployment date: ___________________
- Primary contact: ___________________
- Backup contact: ___________________
- Backup location: ___________________
- Update schedule: ___________________
- Last backup: ___________________
- Last update: ___________________
