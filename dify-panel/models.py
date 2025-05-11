from peewee import *
import datetime
from config import DATABASE_PATH

# 创建数据库连接
db = SqliteDatabase(DATABASE_PATH)


class BaseModel(Model):
    """基础模型类，提供共用的元数据"""
    class Meta:
        database = db


class User(BaseModel):
    """用户模型，用于存储登录用户信息"""
    username = CharField(unique=True)
    password = CharField()  # 实际应用中应当存储密码的哈希值
    created_at = DateTimeField(default=datetime.datetime.now)
    last_login = DateTimeField(null=True)

    @classmethod
    def authenticate(cls, username, password):
        """用户认证方法"""
        try:
            user = cls.get(cls.username == username)
            if user.password == password:  # 实际应用中应比较哈希值
                user.last_login = datetime.datetime.now()
                user.save()
                return user
            return None
        except cls.DoesNotExist:
            return None


class DifyServer(BaseModel):
    """Dify服务器配置"""
    name = CharField()
    base_url = CharField()
    email = CharField()
    password = CharField()
    is_default = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.now()
        if self.is_default:
            # 确保只有一个默认服务器
            DifyServer.update(is_default=False).where(DifyServer.id != self.id).execute()
        return super(DifyServer, self).save(*args, **kwargs)


class DifyAppCache(BaseModel):
    """Dify应用缓存，用于存储应用列表信息"""
    server = ForeignKeyField(DifyServer, backref='apps')
    app_id = CharField()
    name = CharField()
    description = TextField(null=True)
    mode = CharField()  # chat, completion, workflow, agent-chat, advanced-chat
    icon = CharField(null=True)
    icon_background = CharField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.now()
        return super(DifyAppCache, self).save(*args, **kwargs)
    
    class Meta:
        indexes = (
            # 创建一个唯一索引，每个服务器中的app_id都是唯一的
            (('server', 'app_id'), True),
        )


class DifyToolProviderCache(BaseModel):
    """Dify工具提供者缓存"""
    server = ForeignKeyField(DifyServer, backref='tool_providers')
    provider_id = CharField()
    name = CharField()
    description = TextField(null=True)
    type = CharField(null=True)  # 如builtin、custom等
    icon = CharField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.now()
        return super(DifyToolProviderCache, self).save(*args, **kwargs)
    
    class Meta:
        indexes = (
            # 创建一个唯一索引，每个服务器中的provider_id都是唯一的
            (('server', 'provider_id'), True),
        )


# 创建表格
def create_tables():
    with db:
        db.create_tables([User, DifyServer, DifyAppCache, DifyToolProviderCache])


# 初始化数据库
def initialize_database():
    create_tables()
    
    # 如果没有用户，创建一个默认用户
    if User.select().count() == 0:
        User.create(username='admin', password='admin')
    
    # 如果没有服务器配置，可以在这里添加默认服务器

# 确保在导入模块时创建表格
if __name__ == '__main__':
    initialize_database()
else:
    create_tables()
