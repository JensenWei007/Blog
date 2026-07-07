# Blog

存储 `Blog` 的相关文件与重置化脚本。

## 迁移部署

### ssh免密登陆

```bash
cat ~/.ssh/authorized_keys
# 添加ssh public key到authorized_keys
```

### 安装nginx

```sh
apt install nginx
systemctl restart nginx
```

### 迁移文件

```sh
cd /var/www/html
rm -rf *
cp -rf ~/Blog/* ./
```

### 设置定时更新任务


```
python3 scripts/archive/main.py                   # 更新模式
python3 scripts/archive/main.py new_post.md       # 新增文章
python3 scripts/archive/main.py --dry-run          # 预览
python3 scripts/archive/main.py --id 2             # 指定条目
```
