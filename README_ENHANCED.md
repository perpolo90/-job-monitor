# Enhanced Job Monitor System

A comprehensive job monitoring system that scrapes job sites and sends email alerts for new positions matching your criteria. This enhanced version includes SQLite database tracking, timezone support, and platform-specific selectors.

## 🚀 New Features

### 1. **SQLite Database Integration**
- **Job Tracking**: All jobs are stored in a SQLite database (`jobs.db`)
- **Status Management**: Track application status (new, applied, interviewed, etc.)
- **History Tracking**: Complete audit trail of status changes
- **Duplicate Prevention**: Automatic detection of previously seen jobs

### 2. **Timezone Support**
- **Poland Timezone**: Configured for Europe/Warsaw by default
- **Proper Scheduling**: Daily runs at 9:00 AM Poland time
- **Timezone Flexibility**: Can be changed via command line argument

### 3. **Enhanced Company List**
- **20 Companies**: Comprehensive list of fintech and AI companies
- **Platform Detection**: Automatic detection of job board platforms
- **Generic Selectors**: Fallback selectors for common platforms

### 4. **Platform-Specific Selectors**
- **Lever**: `.posting`, `.posting-btn`, `.posting-name`
- **Greenhouse**: `.opening`, `.opening a`, `.opening h3`
- **Ashby**: `.job-posting`, `.job-posting h3`, `.job-posting a`
- **Workday**: `.job-result`, `.job-result h3`, `.job-result a`
- **Bamboo**: `.job-listing`, `.job-listing h3`, `.job-listing a`

## 🏢 Supported Companies

| Company | URL | Platform |
|---------|-----|----------|
| N26 | https://n26.com/en-eu/careers | Custom |
| Klarna | https://www.klarna.com/careers/ | Custom |
| Revolut | https://www.revolut.com/en-PL/careers/ | Custom |
| Scale AI | https://scale.com/careers#open-roles | Custom |
| Tools for Humanity | https://www.toolsforhumanity.com/careers | Custom |
| Worldcoin | https://world.org/pl-pl/careers | Custom |
| MoonPay | https://jobs.lever.co/moonpay | **Lever** |
| Coinbase | https://www.coinbase.com/careers/positions | Custom |
| Coinmarketcap | https://coinmarketcap.com/jobs/#jobs | Custom |
| Kraken | https://jobs.ashbyhq.com/kraken.com | **Ashby** |
| BitPanda | https://www.bitpanda.com/en/career | Custom |
| Palantir | https://www.palantir.com/careers/ | Custom |
| Perplexity | https://www.perplexity.ai/hub/careers#open-roles | Custom |
| Anthropic | https://www.anthropic.com/jobs | Custom |
| Binance | https://www.binance.com/en/careers/job-openings?team=All | Custom |

## 🛠️ Installation

1. **Clone and setup**:
```bash
git clone <repository>
cd job-monitor
pip install -r requirements.txt
playwright install
```

2. **Configure**:
   - Update `config.json` with your email credentials
   - Modify keywords if needed
   - Add/remove companies as desired

3. **Test**:
```bash
python job_monitor.py --test --debug
```

## 📊 Database Management

### View Jobs
```bash
# View all jobs
python db_manager.py view

# View jobs by status
python db_manager.py view --status new
python db_manager.py view --status applied

# View job details
python db_manager.py details --id 1

# View status summary
python db_manager.py summary
```

### Update Job Status
```bash
# Update job status
python db_manager.py update --id 1 --new-status applied --notes "Applied via company website"

# Common statuses: new, applied, interviewed, offered, rejected, withdrawn
```

## 🚀 Usage

### Test Mode (Immediate Execution)
```bash
python job_monitor.py --test --debug
```

### Production Mode (Scheduled)
```bash
# Start with default timezone (Europe/Warsaw)
python job_monitor.py

# Start with custom timezone
python job_monitor.py --timezone America/New_York

# Show browser for debugging
python job_monitor.py --browser
```

### Command Line Options
- `--test`: Run immediately instead of scheduling
- `--debug`: Enable verbose debugging output
- `--browser`: Show browser window (disable headless mode)
- `--timezone`: Specify timezone (default: Europe/Warsaw)
- `--config`: Path to configuration file

## ⏰ Scheduling

The job monitor runs daily at 9:00 AM in the configured timezone:

- **Default**: Europe/Warsaw (Poland)
- **Configurable**: Any valid timezone string
- **Immediate**: Runs once when started, then schedules daily runs

## 📧 Email Notifications

- **HTML Format**: Beautiful, formatted job listings
- **Job Details**: Title, company, location, department, employment type
- **Direct Links**: Clickable links to job postings
- **Duplicate Prevention**: Only sends alerts for new jobs

## 🔍 Job Filtering

Jobs are filtered based on keywords in the job title:
- **Current Keywords**: `["operation", "project", "support"]`
- **Case Insensitive**: Matches regardless of capitalization
- **Partial Matching**: Finds jobs containing any keyword

## 🗄️ Database Schema

### Jobs Table
```sql
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_hash TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    url TEXT NOT NULL,
    location TEXT,
    department TEXT,
    employment_type TEXT,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'new',
    notes TEXT
);
```

### Job Status History Table
```sql
CREATE TABLE job_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (job_hash) REFERENCES jobs (job_hash)
);
```

## 🐛 Troubleshooting

### Common Issues

1. **No jobs found**:
   - Check debug HTML files in the current directory
   - Verify company URLs are accessible
   - Check if selectors need updating

2. **Email not sending**:
   - Verify SMTP credentials in `config.json`
   - Check Gmail App Password settings
   - Ensure network connectivity

3. **Scheduling not working**:
   - Verify timezone configuration
   - Check system time settings
   - Review log files for errors

### Debug Mode
```bash
python job_monitor.py --test --debug --browser
```
This will:
- Show browser window
- Save HTML debug files
- Display detailed logging
- Show selector information

## 📁 File Structure

```
job-monitor/
├── job_monitor.py          # Main enhanced job monitor
├── db_manager.py           # Database management utility
├── config.json             # Configuration file
├── requirements.txt        # Python dependencies
├── jobs.db                 # SQLite database (created automatically)
├── job_monitor.log         # Application logs
├── debug_*.html            # Debug HTML files (when issues occur)
└── README_ENHANCED.md      # This file
```

## 🔧 Configuration

### Email Settings
```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-email@gmail.com",
    "sender_password": "your-app-password",
    "recipient_email": "your-email@gmail.com"
  }
}
```

### Company Configuration
```json
{
  "name": "Company Name",
  "url": "https://company.com/careers",
  "selectors": {
    "job_container": ".job-listing",
    "title": ".job-title",
    "link": "a.job-link"
  }
}
```

## 🚀 Future Enhancements

- **Web Dashboard**: Browser-based job management interface
- **Advanced Filtering**: Location, salary, experience level filters
- **Integration APIs**: Connect with job application tracking systems
- **Mobile Notifications**: Push notifications for new jobs
- **Analytics**: Job market trends and insights

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

---

**Note**: This enhanced version maintains backward compatibility with the original job monitor while adding powerful new features for professional job hunting and tracking.
