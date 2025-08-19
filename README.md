# Daily Job Monitor

A simple and automated job monitoring system that scrapes job listings from company websites and sends email alerts for new positions matching your criteria.

## Features

- **Automated Monitoring**: Runs daily at a scheduled time to check for new job postings
- **Multi-Company Support**: Monitor job listings from multiple companies simultaneously
- **Keyword Filtering**: Case-insensitive keyword matching in job titles
- **Email Alerts**: Receive HTML email notifications for new matching jobs
- **Duplicate Prevention**: Tracks seen jobs to prevent duplicate alerts
- **Error Handling**: Graceful error handling - continues if one site fails
- **Test Mode**: Run immediately with `--test` flag for testing
- **Comprehensive Logging**: Detailed logs for debugging and monitoring

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Your Settings

Edit `config.json` with your specific requirements:

#### Add Your Target Companies

Replace the example companies with real companies you want to monitor:

```json
{
  "companies": [
    {
      "name": "Google",
      "url": "https://careers.google.com/jobs/results/",
      "selectors": {
        "job_container": "div.job-listing",
        "title": "h2.job-title",
        "link": "a.job-link"
      }
    },
    {
      "name": "Microsoft",
      "url": "https://careers.microsoft.com/us/en/search-results",
      "selectors": {
        "job_container": ".job-item",
        "title": ".job-title",
        "link": "a.apply-link"
      }
    }
  ]
}
```

#### Configure Your Keywords

Add keywords that should match job titles:

```json
{
  "keywords": [
    "python",
    "developer",
    "software engineer",
    "data scientist",
    "machine learning"
  ]
}
```

#### Set Up Email Notifications

Configure your email settings (Gmail example):

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

**Note**: For Gmail, you'll need to use an "App Password" instead of your regular password. See [Gmail App Passwords](https://support.google.com/accounts/answer/185833) for setup instructions.

### 3. Test Your Configuration

Run a test to make sure everything is working:

```bash
python job_monitor.py --test
```

This will:
- Scrape all configured company websites
- Filter jobs by your keywords
- Show you any new jobs found
- Send an email alert if new jobs are found

### 4. Run the Daily Monitor

Start the daily monitoring system:

```bash
python job_monitor.py
```

The system will:
- Run immediately to check for jobs
- Schedule daily runs at the time specified in `config.json` (default: 9:00 AM)
- Continue running until you stop it with Ctrl+C

## Configuration Details

### Company Configuration

Each company in the `companies` array requires:

- **name**: Company name for logging and email alerts
- **url**: The job listings page URL
- **selectors**: CSS selectors to find job elements on the page

#### CSS Selectors Explained

The `selectors` object contains:

- **job_container**: Selector for the container element that holds each job listing
- **title**: Selector for the job title element
- **link**: Selector for the link to the job details

#### Finding the Right Selectors

1. **Inspect the job listings page** in your browser (F12)
2. **Find a job listing** on the page
3. **Right-click and "Inspect Element"** on the job title
4. **Look at the HTML structure** to identify:
   - The container that wraps each job
   - The element containing the job title
   - The link element

Example HTML structure:
```html
<div class="job-listing">           <!-- job_container -->
  <h2 class="job-title">           <!-- title -->
    Software Engineer
  </h2>
  <a href="/job/123">Apply</a>     <!-- link -->
</div>
```

### Email Configuration

#### Gmail Setup

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
3. **Use the app password** in your config instead of your regular password

#### Other Email Providers

- **Outlook/Hotmail**: Use `smtp-mail.outlook.com` on port 587
- **Yahoo**: Use `smtp.mail.yahoo.com` on port 587
- **Custom SMTP**: Use your provider's SMTP settings

### Schedule Configuration

Set the daily run time in `config.json`:

```json
{
  "schedule_time": "09:00"
}
```

Use 24-hour format (HH:MM).

## Usage Examples

### Test Mode (Run Once)

```bash
python job_monitor.py --test
```

### Custom Configuration File

```bash
python job_monitor.py --config my-config.json
```

### Daily Monitoring

```bash
python job_monitor.py
```

## File Structure

```
job-monitor/
├── job_monitor.py      # Main monitoring script
├── config.json         # Configuration settings
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── .gitignore         # Git ignore file
├── jobs_seen.json     # Tracks seen jobs (created automatically)
└── job_monitor.log    # Log file (created automatically)
```

## Troubleshooting

### Common Issues

1. **"Configuration file not found"**
   - Make sure `config.json` exists in the same directory
   - Check that the JSON syntax is valid

2. **"Failed to scrape [company]"**
   - The website structure may have changed
   - Update the CSS selectors in your config
   - Check if the website blocks automated requests

3. **"Email configuration incomplete"**
   - Fill in all email settings in `config.json`
   - For Gmail, use an App Password, not your regular password

4. **"No jobs found"**
   - Check that your keywords match job titles
   - Verify the CSS selectors are correct
   - Test with `--test` flag to see what's being scraped

### Debugging

1. **Check the log file**: `job_monitor.log` contains detailed information
2. **Run in test mode**: Use `--test` to see immediate results
3. **Inspect website structure**: Use browser dev tools to find correct selectors

### Rate Limiting

Some websites may block frequent requests. The script includes:
- User-Agent headers to mimic a real browser
- 30-second timeout for requests
- Error handling to continue if one site fails

## Advanced Configuration

### Multiple Keywords

You can add multiple keywords to catch different job types:

```json
{
  "keywords": [
    "python",
    "javascript",
    "react",
    "node.js",
    "data scientist",
    "machine learning engineer"
  ]
}
```

### Complex CSS Selectors

For websites with complex structures, you can use advanced CSS selectors:

```json
{
  "selectors": {
    "job_container": "div[data-job-id], .career-item",
    "title": "h2:not(.subtitle), .job-title:first-child",
    "link": "a[href*='job'], a.apply-button"
  }
}
```

## Security Notes

- **Never commit your email password** to version control
- **Use App Passwords** for Gmail instead of your main password
- **Keep your config.json secure** - it contains sensitive information
- **Consider using environment variables** for production deployments

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License. 