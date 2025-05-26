from config import DATABASE_PATH
from peewee import BooleanField, CharField, Model, SqliteDatabase, TextField

db = SqliteDatabase(DATABASE_PATH)


class BaseModel(Model):
    class Meta:
        database = db


class Site(BaseModel):
    """站点模型，用于存储多个Dify站点信息"""

    name = CharField(max_length=255)  # 站点名称
    base_url = CharField(max_length=255)  # 站点URL
    email = CharField(max_length=255)  # 登录邮箱
    password = CharField(max_length=255)  # 登录密码
    description = TextField(null=True)  # 站点描述
    is_default = BooleanField(default=False)  # 是否为默认站点


def create_tables():
    """创建数据库表"""
    with db:
        db.create_tables([Site], safe=True)
