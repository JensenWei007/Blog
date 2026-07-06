#!/bin/bash

cd /var/www/html
rm -rf *
cp -rf ~/Blog/* ./

systemctl restart nginx
