#!/bin/bash

WG_CONTAINER="${WG_CONTAINER:-wg-easy}"
WG_INTERFACE="${WG_INTERFACE:-wg0}"
WG_DATA_DIR="${WG_DATA_DIR:-/var/opt/wg-stats}"
PERIOD="${PERIOD:-monthly}"
PYTHON_SCRIPT="./wg_stats.py"

# Check if Python script exists
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
  echo "Error: Python script not found at $PYTHON_SCRIPT"
  exit 1
fi

# Run the Python script with environment variables
WG_CONTAINER="$WG_CONTAINER" WG_INTERFACE="$WG_INTERFACE" WG_DATA_DIR="$WG_DATA_DIR" PERIOD="$PERIOD" \
  /usr/bin/env python3 "$PYTHON_SCRIPT" > email_report.txt

# Email settings
EMAIL_TO="recipient@email.com"
EMAIL_FROM="sender@domain.com" # (should match msmtp config)
EMAIL_SUBJECT="WireGuard $PERIOD Traffic Report for $WG_CONTAINER"

# Prepare email headers and body
{
  echo "From: $EMAIL_FROM"
  echo "To: $EMAIL_TO"
  echo "Subject: $EMAIL_SUBJECT"
  echo
  cat email_report.txt
} | msmtp --from="$EMAIL_FROM" -- "$EMAIL_TO"