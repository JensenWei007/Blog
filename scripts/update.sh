#!/bin/bash

cd ~/Blog && rm -rf archive/ category/ json/category.json && python3 scripts/archive/main.py

LATEST_ID=$(python3 -c "import json; ids=json.load(open('json/index.json')); print(ids[0])")
#cd ~/Blog && git add . && git commit -s -m "添加第${LATEST_ID}号文章" && git push

cd /var/www/html
rm -rf *
cp -rf ~/Blog/* ./

systemctl restart nginx
