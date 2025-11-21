# WireGuard Traffic Statistics Monitor

A Python script that monitors and reports WireGuard traffic statistics by collecting data from a Docker container running WireGuard or Amnezia. The script tracks data transfer metrics for each peer across different time periods.

## Features

- **Multi-period tracking**: Monitor traffic statistics for daily, weekly, monthly periods and last check
- **Docker integration**: Collects data directly from WireGuard running in a Docker container
- **Human-readable output**: Displays data in easily readable formats (B, KB, MB, GB, TB)
- **Persistent storage**: Saves historical data to JSON files for trend analysis
- **Delta calculations**: Shows traffic changes since the last check for each period

## Configuration Parameters

The script can be configured through environment variables:

### Required Environment Variables

- `WG_CONTAINER` - Name of the Docker container running WireGuard (default: `"wg-easy"`)
- `WG_INTERFACE` - WireGuard interface name (default: `"wg0"`)
- `WG_DATA_DIR` - Directory to store persistent statistics data (default: `"/var/opt/wg-stats"`)
- `PERIOD` - Comma-separated list of tracking periods (default: `"daily,weekly,monthly,lastcheck"`)

### Available Periods

- `daily` - Resets statistics daily
- `weekly` - Resets statistics weekly
- `monthly` - Resets statistics monthly
- `lastcheck` - Tracks changes since the last script execution (never resets)

## Usage

### Basic Usage
```bash
python3 wg-stats.py
```

### Custom Configuration Example
```bash
export WG_CONTAINER="my-wireguard"
export WG_INTERFACE="wg0"
export WG_DATA_DIR="/opt/wireguard/stats"
export PERIOD="daily,weekly,lastcheck"
python3 wg-stats.py
```

### Output Example
```
WireGuard Traffic Report (wg-easy:wg0)
Timestamp: 21 November 2025 14:30:25

=== Daily stats ===
Peer: 10.8.0.2/32
  RX: 1.25 GB (Total), +125.50 MB since last check
  TX: 245.75 MB (Total), +15.20 MB since last check

=== Weekly stats ===
Peer: 10.8.0.2/32
  RX: 8.45 GB (Total), +1.25 GB since last check
  TX: 1.75 GB (Total), +245.75 MB since last check
```

## How It Works

1. **Data Collection**: Executes `wg show <interface> dump` inside the specified Docker container
2. **Data Parsing**: Extracts peer information and transfer statistics (RX/TX bytes)
3. **Period Management**:
   - Generates period keys (daily: YYYY-MM-DD, weekly: YYYY-WWW, monthly: YYYY-MM)
   - Automatically resets statistics when periods change
4. **Storage**: Saves current statistics to JSON files in the data directory
5. **Reporting**: Calculates and displays deltas from previous measurements

## File Structure

The script creates JSON files in the data directory with the naming pattern:
```
{DATA_DIR}/{WG_CONTAINER}_{WG_INTERFACE}_{period}.json
```

Example:
```
/var/opt/wg-stats/
├── wg-easy_wg0_daily.json
├── wg-easy_wg0_weekly.json
├── wg-easy_wg0_monthly.json
└── wg-easy_wg0_lastcheck.json
```

## Dependencies

- Python 3.6+
- Docker
- WireGuard installed in the target container
- Appropriate permissions to execute `docker exec` commands

## Error Handling

- Exits with error code 1 if unable to execute WireGuard commands
- Handles missing data files gracefully
- Manages counter resets (negative deltas) by assuming fresh start

## Use Cases

- **Bandwidth monitoring**: Track data usage per client over time
- **Billing systems**: Provide data for usage-based billing
- **Network troubleshooting**: Identify unusual traffic patterns
- **Capacity planning**: Understand long-term traffic trends

## Notes

- Ensure the script has permission to write to the data directory
- The script should be run regularly (e.g., via cron) for accurate period tracking
- Counter resets are handled by treating negative deltas as fresh measurements
- Peer identification is based on `allowed_ips` from WireGuard dump output

# WireGuard Traffic Report Email Wrapper

A bash wrapper script `wg_stats.sh` generates WireGuard traffic statistics reports and sends them via email using msmtp. Can be used within cron.

## Overview

This script automates the process of generating WireGuard traffic reports and emailing them to specified recipients. It serves as a convenient wrapper around the Python statistics script, handling configuration, execution, and email delivery.

## Features

- **Automated reporting**: Generates traffic reports with a single command
- **Email integration**: Sends reports via msmtp mail transfer agent
- **Flexible configuration**: Customizable through environment variables
- **Error handling**: Validates script existence and configuration

## Configuration

The script can be configured using environment variables:

### Environment Variables

- `WG_CONTAINER` - Docker container name running WireGuard (default: `"wg-easy"`)
- `WG_INTERFACE` - WireGuard interface name (default: `"wg0"`)
- `WG_DATA_DIR` - Directory for statistics data storage (default: `"/var/opt/wg-stats"`)
- `PERIOD` - Reporting period (default: `"monthly"`)
- `PYTHON_SCRIPT` - Path to the Python statistics script (default: `"./wg_stats.py"`)

### Email Configuration

- `EMAIL_TO` - Recipient email address (default: `"recipient@email.com"`)
- `EMAIL_FROM` - Sender email address (default: `"sender@domain.com"`)
- `EMAIL_SUBJECT` - Email subject line (automatically includes period and container name)

## Usage

### Basic Usage
```bash
./wg_stats.sh
```

### Custom Configuration Example
```bash
export WG_CONTAINER="my-wireguard"
export WG_INTERFACE="wg1"
export PERIOD="weekly"
export EMAIL_TO="admin@company.com"
export EMAIL_FROM="wireguard@company.com"
./wg_stats.sh
```

### One-liner with Inline Configuration
```bash
WG_CONTAINER="my-vpn" PERIOD="daily" EMAIL_TO="me@example.com" ./wg_stats.sh
```

## Prerequisites

### Required Software
- **msmtp** - Mail transfer agent (must be installed and configured)
- **Python 3** - For the statistics script
- **Docker** - To access WireGuard container
- **WireGuard Python script** - The `wg_stats.py` script must be accessible

### msmtp Configuration
Ensure msmtp is properly configured. Typically this involves creating `~/.msmtprc` or `/etc/msmtprc`:

```ini
# Example msmtp configuration
defaults
auth on
tls on
tls_trust_file /etc/ssl/certs/ca-certificates.crt

account primary
host smtp.your-email-provider.com
port 587
from sender@domain.com
user your-username
password your-password

account default : primary
```

## Script Workflow

1. **Validation**: Checks if the Python script exists
2. **Configuration**: Applies environment variable defaults
3. **Report Generation**: Executes the Python script and saves output to `email_report.txt`
4. **Email Composition**: Creates email headers and combines with report content
5. **Delivery**: Sends the email using msmtp

## File Output

The script creates a temporary file:
- `email_report.txt` - Contains the raw statistics report (overwritten each run)

## Error Handling

- **Script validation**: Exits with error if Python script is not found
- **msmtp errors**: Any msmtp failures will be displayed in the terminal
- **Environment fallbacks**: Uses sensible defaults for missing configuration

## Email Format

The generated email includes:
- Proper email headers (From, To, Subject)
- Empty line separating headers from body
- The complete traffic statistics report

Example email subject:
```
WireGuard monthly Traffic Report for wg-easy
```

## Automation

### Cron Job Example
Set up automated daily reports by adding to crontab:

```bash
# Send daily WireGuard report at 6 AM
0 6 * * * /path/to/wg_stats.sh

# Send weekly report every Monday at 7 AM
0 7 * * 1 WG_CONTAINER="wg-easy" PERIOD="weekly" /path/to/wg_stats.sh
```

### Systemd Service Example
Create a systemd service for more advanced scheduling:

```ini
[Unit]
Description=WireGuard Monthly Traffic Report
After=network.target

[Service]
Type=oneshot
Environment=WG_CONTAINER=wg-easy
Environment=PERIOD=monthly
Environment=EMAIL_TO=admin@example.com
ExecStart=/path/to/wg_stats.sh
User=root

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Common Issues

1. **Script not found**: Ensure `wg_stats.py` is in the same directory or update `PYTHON_SCRIPT` path
2. **msmtp failures**: Verify msmtp configuration and test email sending independently
3. **Permission errors**: Ensure the script has execute permissions (`chmod +x wg_stats.sh`)
4. **Docker access**: The user must have permission to execute `docker exec` commands

### Testing

Test the email functionality without sending:
```bash
# Generate report without sending email
./wg_stats.sh
cat email_report.txt

# Test msmtp configuration separately
echo "Test message" | msmtp --debug --from=sender@domain.com recipient@email.com
```

## Security Considerations

- Store email credentials securely in msmtp configuration file
- Set appropriate file permissions on configuration files
- Consider using app-specific passwords for email accounts
- Run with minimal necessary privileges

## Customization

### Adding HTML Email Support
To send HTML formatted reports, modify the email section:

```bash
{
  echo "From: $EMAIL_FROM"
  echo "To: $EMAIL_TO"
  echo "Subject: $EMAIL_SUBJECT"
  echo "Content-Type: text/html"
  echo
  echo "<html><body><pre>"
  cat email_report.txt
  echo "</pre></body></html>"
} | msmtp --from="$EMAIL_FROM" -- "$EMAIL_TO"
```

### Multiple Recipients
To send to multiple recipients, modify the `EMAIL_TO` variable:

```bash
EMAIL_TO="admin@company.com,team@company.com,manager@company.com"
```