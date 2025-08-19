# Job Monitor - Railway Deployment Guide

This guide explains how to deploy the Job Monitor system to Railway with proper configuration and monitoring.

## 🚀 Quick Deploy to Railway

### 1. **Fork/Clone Repository**
```bash
git clone <your-repo-url>
cd job-monitor
```

### 2. **Deploy to Railway**
1. Go to [Railway.app](https://railway.app)
2. Create a new project
3. Connect your GitHub repository
4. Railway will automatically detect the Dockerfile and deploy

### 3. **Configure Environment Variables**
In your Railway project dashboard, add these environment variables:

#### **Required Variables**
```
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-gmail-app-password
RECIPIENT_EMAIL=your-email@gmail.com
```

#### **Optional Variables**
```
TIMEZONE=Europe/Warsaw
SCHEDULE_TIME=09:00
LOG_LEVEL=INFO
DATABASE_URL=jobs.db
WEB_ONLY=false
MONITOR_ONLY=false
```

### 4. **Gmail App Password Setup**
1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password as `SENDER_PASSWORD`

## 📋 Railway Configuration

### **railway.toml**
The `railway.toml` file configures:
- **Dockerfile build**: Uses our custom Dockerfile
- **Health checks**: `/health` endpoint
- **Cron scheduling**: Daily at 7 AM UTC (9 AM Poland time)
- **Restart policy**: Automatic restart on failure

### **Cron Job**
```toml
[cron]
schedule = "0 7 * * *"  # 7 AM UTC = 9 AM Poland time
command = "python job_monitor_production.py --test"
```

## 🔧 System Architecture

### **Components**
1. **Web Server** (`web_server.py`): Health checks and status endpoints
2. **Job Monitor** (`job_monitor_production.py`): Main monitoring logic
3. **Startup Script** (`startup.py`): Orchestrates both components
4. **Database** (`jobs.db`): SQLite database for job tracking

### **Endpoints**
- `/health` - Health check for Railway
- `/` - Service information
- `/status` - Configuration status

## 📊 Monitoring & Logs

### **Railway Dashboard**
- View real-time logs
- Monitor resource usage
- Check deployment status
- View cron job execution

### **Log Levels**
- `INFO` - Normal operation logs
- `DEBUG` - Detailed debugging information
- `ERROR` - Error messages and stack traces

### **Health Checks**
Railway automatically checks `/health` endpoint:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-13T21:00:00+02:00",
  "timezone": "Europe/Warsaw",
  "service": "job-monitor",
  "version": "2.0.0"
}
```

## 🔄 Cron Job Execution

### **Schedule**
- **Time**: Daily at 9:00 AM Poland time (7:00 AM UTC)
- **Command**: `python job_monitor_production.py --test`
- **Duration**: Single execution (not continuous)

### **Execution Flow**
1. Railway triggers cron job
2. Job monitor runs once
3. Scrapes all configured companies
4. Sends email alerts for new jobs
5. Updates database
6. Exits successfully

## 🛠️ Troubleshooting

### **Common Issues**

#### **1. Email Not Sending**
- Verify Gmail App Password is correct
- Check `SENDER_EMAIL` and `RECIPIENT_EMAIL` are set
- Ensure 2FA is enabled on Gmail account

#### **2. Health Check Failing**
- Check logs for startup errors
- Verify all environment variables are set
- Check if web server is starting properly

#### **3. Cron Job Not Running**
- Verify cron schedule in Railway dashboard
- Check logs for cron execution
- Ensure timezone is set correctly

#### **4. Database Issues**
- Check if `jobs.db` file is being created
- Verify database permissions
- Check for SQLite errors in logs

### **Debug Mode**
To enable debug logging, set:
```
LOG_LEVEL=DEBUG
```

### **Manual Testing**
You can manually trigger a job run:
1. Go to Railway dashboard
2. Open terminal
3. Run: `python job_monitor_production.py --test --debug`

## 🔒 Security

### **Environment Variables**
- Sensitive data (emails, passwords) stored as environment variables
- Never commit credentials to repository
- Railway encrypts environment variables

### **Database**
- SQLite database stored in Railway's persistent storage
- Automatic backups through Railway
- No external database required

### **Network**
- All web scraping done through Railway's network
- No need to expose internal services
- Health checks only accessible to Railway

## 📈 Scaling

### **Current Setup**
- Single instance deployment
- Suitable for personal job monitoring
- Low resource usage

### **Future Scaling**
- Multiple instances for redundancy
- External database (PostgreSQL)
- Load balancing for web endpoints
- Advanced monitoring and alerting

## 🔄 Updates

### **Automatic Deployments**
- Railway automatically deploys on git push
- Zero-downtime deployments
- Automatic rollback on failure

### **Manual Updates**
1. Update code locally
2. Push to GitHub
3. Railway automatically redeploys
4. Monitor logs for successful deployment

## 📞 Support

### **Railway Support**
- [Railway Documentation](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)
- [Railway Status](https://status.railway.app)

### **Job Monitor Issues**
- Check logs in Railway dashboard
- Verify environment variables
- Test locally with `--debug` flag
- Review this documentation

## 🎯 Success Metrics

### **Monitoring Success**
- Health checks passing
- Cron jobs executing daily
- Email alerts being sent
- Database being updated

### **Job Discovery**
- Jobs found across companies
- Keywords matching correctly
- No duplicate notifications
- Status tracking working

---

**Note**: This deployment is optimized for Railway's infrastructure and includes proper health checks, logging, and error handling for production use.
