#!/bin/bash

# Approach: (https://chat.openai.com/c/43be8685-b27b-4e3b-bd18-0856f8d23d7e)
# cron runs this script every minute New York in range of 9:20 - 16:20 US time
# Also this scripts writes the "heartbeat" message to log file, so the user knows
#that cron is running

# Installation steps required:
#chmod +x run_scheduler.sh
#install tzdata package: sudo apt-get install tzdata
#crontab -e
#CRON_TZ=America/New_York
# * 9-16 * * 1-5 /home/david/v2trading/run_scheduler.sh
#
# (Runs every minute of every hour on every day-of-week from Monday to Friday) US East time

# Path to the Python script
PYTHON_SCRIPT="v2realbot/scheduler/scheduler.py"

# Log file path
LOG_FILE="job.log"

# Timezone for New York
TZ='America/New_York'
NY_DATE_TIME=$(TZ=$TZ date +'%Y-%m-%d %H:%M:%S')
echo "NY_DATE_TIME: $NY_DATE_TIME"

# Check if log file exists, create it if it doesn't
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
fi

# Check the last line of the log file
LAST_LINE=$(tail -n 1 "$LOG_FILE")

# Cron trigger message
CRON_TRIGGER="Cron trigger: $NY_DATE_TIME"

# Update the log
if [[ "$LAST_LINE" =~ "Cron trigger:".* ]]; then
    # Replace the last line with the new trigger message
    sed -i '' '$ d' "$LOG_FILE"
    echo "$CRON_TRIGGER" >> "$LOG_FILE"
else
    # Append a new cron trigger message
    echo "$CRON_TRIGGER" >> "$LOG_FILE"
fi


# FOR DEBUG - Run the Python script and append output to log file
python3 "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1