#!/bin/bash
cd $(dirname $0)

# 设置迁移目录（确保该目录存在）
MIGRATION_DIR="migrations"

# 检查迁移目录是否存在，如果不存在则创建
if [ ! -d "$MIGRATION_DIR" ]; then
    echo "Migration directory doesn't exist. Creating..."
    mkdir -p "$MIGRATION_DIR"
fi

# 生成迁移文件
echo "Generating migrations..."
python -m peewee_migrate migrate

# 提示用户检查迁移文件
echo "Migrations generated in '$MIGRATION_DIR'. Please review and commit these changes."
