# STAATS Python - Docker Production Deployment

**Docker deployment on internal server - 15 minute setup**

---

## Prerequisites

- Server with Docker installed (Ubuntu 20.04+ or Windows Server 2019+)
- 4GB RAM minimum, 8GB recommended
- 20GB disk space
- Network access to server

---

## Installation Steps

### 1. Install Docker

**Ubuntu/Linux:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**Windows Server:**
- Install Docker Desktop from https://www.docker.com/products/docker-desktop
- Restart server after installation

### 2. Clone Repository

```bash
git clone https://github.com/LakovskyR/staats-python.git
cd staats-python
```

### 3. Configure Production Settings

Edit `docker-compose.yml`:

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
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 4. Start Services

```bash
docker-compose up -d
```

### 5. Verify Deployment

```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs -f

# Test health endpoint
curl http://localhost:8501/_stcore/health
```

**Access app:** http://SERVER-IP:8501

---

## Daily Operations

### View Logs
```bash
docker-compose logs -f
docker-compose logs --tail=100
```

### Restart Service
```bash
docker-compose restart
```

### Stop Service
```bash
docker-compose down
```

### Update to Latest Code
```bash
git pull
docker-compose down
docker-compose up -d --build
```

### Check Resource Usage
```bash
docker stats
```

---

## Backup & Restore

### Create Backup

Create script: `backup.sh`

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/staats-python"

# Backup data
docker-compose exec -T staats-web tar -czf - /app/output > $BACKUP_DIR/data-$DATE.tar.gz

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "data-*.tar.gz" -mtime +30 -delete
```

Make executable:
```bash
chmod +x backup.sh
```

Add to crontab (daily at 2 AM):
```bash
crontab -e
# Add line:
0 2 * * * /path/to/backup.sh >> /var/log/staats-backup.log 2>&1
```

### Restore from Backup

```bash
docker-compose down
tar -xzf backup-YYYYMMDD.tar.gz -C ./output
docker-compose up -d
```

---

## Firewall Configuration

**Ubuntu/Debian:**
```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 8501/tcp # STAATS app
sudo ufw enable
```

**Internal network only:**
```bash
sudo ufw allow from 10.0.0.0/8 to any port 8501
```

---

## SSL/HTTPS Setup

### Install nginx

```bash
sudo apt-get install nginx certbot
```

### Configure nginx

Create `/etc/nginx/sites-available/staats`:

```nginx
upstream staats {
    server localhost:8501;
}

server {
    listen 80;
    server_name staats.aplusa.internal;

    location / {
        proxy_pass http://staats;
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
sudo systemctl restart nginx
```

### Get SSL Certificate

```bash
sudo certbot --nginx -d staats.aplusa.internal
```

---

## Monitoring

### Health Check Script

Create `health-check.sh`:

```bash
#!/bin/bash
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8501/_stcore/health)

if [ $RESPONSE -eq 200 ]; then
    echo "OK - Service is healthy"
    exit 0
else
    echo "CRITICAL - Service is down (HTTP $RESPONSE)"
    docker-compose restart
    exit 2
fi
```

Add to crontab (check every 5 minutes):
```bash
*/5 * * * * /path/to/health-check.sh >> /var/log/staats-health.log 2>&1
```

### Log Rotation

Create `/etc/logrotate.d/staats-python`:

```
/var/log/staats-*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 root root
}
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Check system resources
df -h
free -m

# Rebuild container
docker-compose down
docker-compose up -d --build
```

### Port Already in Use

```bash
# Find process using port 8501
sudo lsof -i :8501
sudo kill <PID>

# Or change port in docker-compose.yml
ports:
  - "8502:8501"
```

### Out of Memory

```bash
# Increase memory limit in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 8G
```

### Cannot Access from Network

```bash
# Check firewall
sudo ufw status

# Check docker network
docker network inspect bridge

# Ensure binding to 0.0.0.0
docker-compose logs | grep "address"
```

---

## Production Checklist

**Before Go-Live:**

- [ ] Docker installed and tested
- [ ] Repository cloned to /opt/staats-python or similar
- [ ] docker-compose.yml configured with production settings
- [ ] Firewall configured (port 8501 or nginx)
- [ ] Backup script created and tested
- [ ] Backup cron job configured
- [ ] Health check script configured
- [ ] Log rotation configured
- [ ] SSL certificate installed (if using nginx)
- [ ] Team can access http://SERVER-IP:8501
- [ ] aplusa logo displays correctly
- [ ] Test with sample data successful
- [ ] Test with real study successful

**Post-Deployment:**

- [ ] Monitor logs first 24 hours
- [ ] Verify backups running
- [ ] Train 3 team members
- [ ] Document internal URL
- [ ] Add to monitoring dashboard
- [ ] Schedule weekly restart (optional)

---

## Team Access

**Share with team:**

**URL:** http://SERVER-IP:8501  
**Internal hostname:** http://staats.aplusa.internal (if DNS configured)

**Usage:**
1. Open URL in browser
2. Upload CSV/Excel file
3. Configure or import STAATS.xlsm
4. Generate analysis
5. Download Excel results

---

## Maintenance Schedule

**Daily:**
- Automated backup (2 AM)
- Health check (every 5 minutes)

**Weekly:**
- Review logs for errors
- Check disk space
- Update to latest code (git pull)

**Monthly:**
- Test backup restore
- Review resource usage
- Update Docker images

---

## Support Contacts

**For deployment issues:**
- IT Support Team
- Data Processing Team
- GitHub Issues: https://github.com/LakovskyR/staats-python/issues

**For usage questions:**
- Data Processing Team
- Internal documentation

---

## Quick Reference

**Start service:**
```bash
docker-compose up -d
```

**Stop service:**
```bash
docker-compose down
```

**View logs:**
```bash
docker-compose logs -f
```

**Update:**
```bash
git pull && docker-compose up -d --build
```

**Restart:**
```bash
docker-compose restart
```

**Backup:**
```bash
./backup.sh
```

**Check health:**
```bash
curl http://localhost:8501/_stcore/health
```

---

**Deployment time: 15 minutes**  
**Maintenance time: 5 minutes/week**  
**Expected uptime: 99%+**
