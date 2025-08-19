# 🚀 Railway Deployment Checklist

## ✅ Pre-Deployment Checklist

### **1. Code Preparation**
- [x] Dockerfile created and tested
- [x] railway.toml configured with cron scheduling
- [x] Environment variables moved to .env.example
- [x] Production job monitor created (job_monitor_production.py)
- [x] Web server with health checks created (web_server.py)
- [x] Startup script created (startup.py)
- [x] All tests passing (test_production.py)

### **2. Configuration Files**
- [x] requirements.txt updated with Flask
- [x] config.json contains non-sensitive data only
- [x] .env.example shows required environment variables
- [x] .gitignore excludes sensitive files

### **3. Railway Configuration**
- [x] railway.toml with proper settings
- [x] Cron job scheduled for 7 AM UTC (9 AM Poland time)
- [x] Health check endpoint configured
- [x] Restart policy configured

## 🚀 Deployment Steps

### **Step 1: Prepare Repository**
```bash
# Ensure all files are committed
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### **Step 2: Deploy to Railway**
1. Go to [Railway.app](https://railway.app)
2. Create new project
3. Connect GitHub repository
4. Railway will auto-detect Dockerfile and deploy

### **Step 3: Configure Environment Variables**
In Railway dashboard, add these variables:

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

### **Step 4: Gmail Setup**
1. Enable 2-factor authentication on Gmail
2. Generate App Password:
   - Google Account → Security → 2-Step Verification → App passwords
   - Generate for "Mail"
   - Use as SENDER_PASSWORD

## 🔍 Post-Deployment Verification

### **1. Health Check**
- Visit: `https://your-app.railway.app/health`
- Should return: `{"status": "healthy", "timezone": "Europe/Warsaw"}`

### **2. Status Check**
- Visit: `https://your-app.railway.app/status`
- Verify configuration is loaded correctly

### **3. Logs Verification**
- Check Railway dashboard logs
- Look for successful startup messages
- Verify no error messages

### **4. Cron Job Test**
- Wait for next scheduled run (7 AM UTC)
- Check logs for job execution
- Verify email notifications sent

## 🛠️ Troubleshooting

### **Common Issues**

#### **Deployment Fails**
- Check Dockerfile syntax
- Verify all dependencies in requirements.txt
- Check Railway logs for build errors

#### **Health Check Fails**
- Verify web server is starting
- Check environment variables are set
- Review startup logs

#### **Email Not Sending**
- Verify Gmail App Password
- Check SMTP settings
- Ensure 2FA is enabled

#### **Cron Job Not Running**
- Check Railway cron configuration
- Verify timezone settings
- Review cron execution logs

### **Debug Commands**
```bash
# Test locally
python test_production.py

# Test web server
python web_server.py

# Test job monitor
python job_monitor_production.py --test --debug
```

## 📊 Monitoring

### **Railway Dashboard**
- Monitor resource usage
- View real-time logs
- Check deployment status
- Track cron job execution

### **Health Endpoints**
- `/health` - Service health
- `/status` - Configuration status
- `/` - Service information

### **Log Levels**
- `INFO` - Normal operation
- `DEBUG` - Detailed debugging
- `ERROR` - Error messages

## 🔄 Maintenance

### **Updates**
1. Update code locally
2. Push to GitHub
3. Railway auto-deploys
4. Monitor deployment logs

### **Environment Changes**
1. Update variables in Railway dashboard
2. Redeploy if needed
3. Test health endpoints

### **Database Management**
- Database stored in Railway persistent storage
- Automatic backups through Railway
- Can be accessed via Railway terminal

## 🎯 Success Criteria

### **Deployment Success**
- [ ] Application deploys without errors
- [ ] Health check endpoint responds
- [ ] All environment variables loaded
- [ ] Database initializes correctly

### **Operation Success**
- [ ] Cron job runs daily at 9 AM Poland time
- [ ] Email notifications sent for new jobs
- [ ] Database updated with job information
- [ ] No duplicate notifications sent

### **Monitoring Success**
- [ ] Logs show successful operation
- [ ] Health checks pass consistently
- [ ] Resource usage within limits
- [ ] No critical errors in logs

---

**Note**: This checklist ensures a smooth deployment and operation of the Job Monitor system on Railway.
