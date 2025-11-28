#!/bin/bash

LOG_DIR=~/daily_log
CURRENT_DATE=$(date +"%Y-%m-%d")
LOG_FILE="$LOG_DIR/${CURRENT_DATE}.txt"

mkdir -p "$LOG_DIR"

echo "======================================================================" | tee -a "$LOG_FILE"
echo "$(date): 每日任务开始执行" | tee -a "$LOG_FILE"




echo "$(date): 开始同步 Github 仓库内容" | tee -a "$LOG_FILE"

cd ~/Blog
git pull | tee -a "$LOG_FILE"

echo "$(date): 同步 Github 仓库内容成功" | tee -a "$LOG_FILE"


echo "$(date): 开始同步 Github 仓库内容到服务端" | tee -a "$LOG_FILE"

cd /var/www/html
rm -rf *
cp -rf ~/Blog/* ./

echo "$(date): 同步 Github 仓库内容到服务端成功" | tee -a "$LOG_FILE"


echo "$(date): 开始重启 nginx 服务" | tee -a "$LOG_FILE"

systemctl restart nginx

echo "Nginx 重启状态: $?" | tee -a "$LOG_FILE"




echo "$(date): 每日任务执行完毕" | tee -a "$LOG_FILE"
echo "======================================================================" | tee -a "$LOG_FILE"