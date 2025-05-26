#!/bin/bash
cd $(dirname $0)

# 设置迁移目录（确保该目录存在）
MIGRATION_DIR="migrations"

# 执行迁移
echo "Applying migrations..."
python -m peewee_migrate migrate

# 提示用户迁移完成
echo "Migrations applied successfully."
