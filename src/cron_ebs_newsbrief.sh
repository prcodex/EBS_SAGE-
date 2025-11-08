#!/bin/bash
# EBS Clean NewsBreif Batch Processor - Cron Job
# Runs every 2 hours to process 20 NewsBreif emails

LOG_DIR="/home/ubuntu/logs/ebs_clean"
mkdir -p $LOG_DIR

LOG_FILE="$LOG_DIR/newsbrief_batch_$(date +%Y%m%d).log"

echo "========================================" >> $LOG_FILE
echo "Starting NewsBreif batch at $(date)" >> $LOG_FILE
echo "========================================" >> $LOG_FILE

export ANTHROPIC_API_KEY='YOUR_ANTHROPIC_API_KEY_HERE'
cd /home/ubuntu/newspaper_project
python3 newsbrief_batch_ebs.py >> $LOG_FILE 2>&1

echo "Completed at $(date)" >> $LOG_FILE
echo "" >> $LOG_FILE
