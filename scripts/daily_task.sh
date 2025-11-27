#!/bin/bash

LOG_DIR=~/daily_log
CURRENT_DATE=$(date +"%Y-%m-%d")
LOG_FILE="$LOG_DIR/${CURRENT_DATE}.txt"

mkdir -p "$LOG_DIR"

echo "======================================================================" > "$LOG_FILE"
echo "$(date): 每日任务开始执行" >> "$LOG_FILE"


















