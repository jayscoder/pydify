好的，没问题。以下是用 Markdown 格式编写的 Python Peewee 库的完整用法文档。

````markdown
# Peewee 完整用法文档

Peewee 是一个小巧且易于使用的 Python ORM (Object-Relational Mapper)，它支持 SQLite、MySQL、PostgreSQL 和 CockroachDB 等数据库。本文档将详细介绍 Peewee 的各种功能和用法。

## 1. 安装

首先，你需要安装 Peewee 库。可以使用 pip 进行安装：

```bash
pip install peewee
```
````

## 2. 连接数据库

在使用 Peewee 之前，你需要连接到你的数据库。

### 2.1 SQLite

```python
from peewee import *

db = SqliteDatabase('my_database.db')

class BaseModel(Model):
    class Meta:
        database = db

db.connect()
db.create_tables([YourModel1, YourModel2]) # 创建你的模型对应的表
```

### 2.2 MySQL

```python
from peewee import *

db = MySQLDatabase('my_database', user='your_user', password='your_password', host='your_host', port=3306)

class BaseModel(Model):
    class Meta:
        database = db

db.connect()
db.create_tables([YourModel1, YourModel2])
```

### 2.3 PostgreSQL

```python
from peewee import *

db = PostgresqlDatabase('my_database', user='your_user', password='your_password', host='your_host', port=5432)

class BaseModel(Model):
    class Meta:
        database = db

db.connect()
db.create_tables([YourModel1, YourModel2])
```

### 2.4 CockroachDB

```python
from peewee import *

db = PostgresqlDatabase('my_database', user='your_user', password='your_password', host='your_host', port=26257)

class BaseModel(Model):
    class Meta:
        database = db

db.connect()
db.create_tables([YourModel1, YourModel2])
```

## 3. 定义模型

模型是 Python 类，它们继承自 `peewee.Model` 或你自定义的继承自 `peewee.Model` 的基类。每个模型类对应数据库中的一个表，而模型的每个属性对应表中的一个列。

```python
class User(BaseModel):
    username = CharField(unique=True)
    password = CharField()
    email = CharField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)

class Tweet(BaseModel):
    user = ForeignKeyField(User, backref='tweets')
    content = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)
    is_published = BooleanField(default=False)
```

### 3.1 字段类型

Peewee 提供了多种字段类型来映射数据库中的不同数据类型：

- `AutoField`: 自增长的整数主键。
- `BigIntegerField`: 大整数。
- `BooleanField`: 布尔值。
- `CharField`: 变长字符串。
- `DateField`: 日期。
- `DateTimeField`: 日期和时间。
- `DecimalField`: 定点数。
- `FloatField`: 浮点数。
- `ForeignKeyField`: 外键关联。
- `IntegerField`: 整数。
- `SmallIntegerField`: 小整数。
- `TextField`: 长文本。

### 3.2 字段选项

定义字段时，可以指定一些选项来约束字段的行为：

- `unique=True`: 确保字段的值在表中是唯一的。
- `null=True`: 允许字段的值为 NULL。
- `default=value`: 设置字段的默认值。
- `index=True`: 为字段创建索引以提高查询性能。
- `primary_key=True`: 将字段设置为主键。通常使用 `AutoField` 作为自增长的主键。
- `backref='relation_name'`: 在外键关联的反向引用中使用的属性名称。

### 3.3 元类 (Meta)

在模型类中定义一个名为 `Meta` 的内部类，用于指定模型的元数据，例如关联的数据库。

```python
class BaseModel(Model):
    class Meta:
        database = db
```

## 4. 基本的 CRUD 操作

### 4.1 创建数据 (Create)

使用模型类的 `create()` 方法或创建模型实例并调用 `save()` 方法来插入新记录。

```python
# 使用 create() 方法
user = User.create(username='alice', password='password123', email='alice@example.com')

# 创建实例并调用 save() 方法
user = User(username='bob', password='secure_password')
user.save()
```

### 4.2 读取数据 (Read)

使用模型类的 `select()` 方法来查询数据。

```python
# 查询所有用户
users = User.select()
for user in users:
    print(user.username, user.email)

# 根据条件查询
try:
    specific_user = User.get(User.username == 'alice')
    print(specific_user.email)
except User.DoesNotExist:
    print("User not found")

# 使用 where 子句
active_users = User.select().where(User.email.is_null(False))
for user in active_users:
    print(user.username, user.email)

# 使用 order_by 子句排序
ordered_users = User.select().order_by(User.created_at.desc())
for user in ordered_users:
    print(user.username, user.created_at)

# 使用 limit 和 offset 进行分页
recent_users = User.select().order_by(User.created_at.desc()).limit(10).offset(20)
for user in recent_users:
    print(user.username)
```

### 4.3 更新数据 (Update)

使用 `update()` 方法来更新现有记录。

```python
# 更新单个字段
query = User.update(email='alice.updated@example.com').where(User.username == 'alice')
query.execute()

# 更新多个字段
query = User.update({User.password: 'new_password', User.email: 'bob.updated@example.com'}).where(User.username == 'bob')
query.execute()

# 获取更新后的行数
rows_updated = query.execute()
print(f"Updated {rows_updated} rows.")
```

### 4.4 删除数据 (Delete)

使用 `delete()` 方法来删除记录。

```python
# 删除符合条件的记录
query = User.delete().where(User.username == 'bob')
rows_deleted = query.execute()
print(f"Deleted {rows_deleted} rows.")

# 删除单个实例
try:
    user_to_delete = User.get(User.username == 'alice')
    user_to_delete.delete_instance()
except User.DoesNotExist:
    print("User not found")
```

## 5. 关系 (Relationships)

Peewee 支持一对一、一对多和多对多的关系。

### 5.1 外键 (ForeignKeyField)

使用 `ForeignKeyField` 定义一对多或一对一的关系。

```python
class Blog(BaseModel):
    name = CharField()

class Post(BaseModel):
    blog = ForeignKeyField(Blog, backref='posts')
    title = CharField()
    content = TextField()
```

通过 `backref` 参数，你可以从 `Blog` 实例访问其关联的 `Post` 实例列表。

```python
blog = Blog.create(name='My Awesome Blog')
Post.create(blog=blog, title='First Post', content='Hello, world!')
Post.create(blog=blog, title='Second Post', content='Another post.')

for post in blog.posts:
    print(post.title)
```

### 5.2 多对多关系 (ManyToManyField)

多对多关系需要一个中间表。Peewee 提供了 `ManyToManyField` 来简化这个过程。

```python
class Tag(BaseModel):
    name = CharField(unique=True)

class Post(BaseModel):
    title = CharField()
    content = TextField()
    tags = ManyToManyField(Tag, backref='posts')

class PostTag(BaseModel): # Peewee 会自动创建这个中间模型
    post = ForeignKeyField(Post, backref='post_tags')
    tag = ForeignKeyField(Tag, backref='tag_posts')

    class Meta:
        primary_key = CompositeKey('post', 'tag') # 定义联合主键

PostTag.create_table() # 需要显式创建中间表

post = Post.create(title='Peewee and Tags', content='Using many-to-many relationships.')
tag1 = Tag.create(name='python')
tag2 = Tag.create(name='peewee')

post.tags.add([tag1, tag2])

for tag in post.tags:
    print(tag.name)

for post in tag1.posts:
    print(post.title)
```

## 6. 查询 (Querying)

Peewee 提供了强大的查询 API。

### 6.1 基础查询

```python
# 查询所有字段
users = User.select()

# 查询特定字段
usernames = User.select(User.username)
for user in usernames:
    print(user.username)
```

### 6.2 条件查询 (WHERE)

使用 `where()` 方法添加查询条件。

```python
# 等于
active_user = User.select().where(User.is_active == True)

# 不等于
inactive_users = User.select().where(User.is_active != True)

# 大于、小于、大于等于、小于等于
recent_users = User.select().where(User.created_at > datetime.datetime(2023, 1, 1))

# IN 子句
selected_usernames = ['alice', 'bob']
users = User.select().where(User.username.in_(selected_usernames))

# NOT IN 子句
other_users = User.select().where(User.username.not_in(selected_usernames))

# NULL 值判断
no_email_users = User.select().where(User.email.is_null())
has_email_users = User.select().where(User.email.is_not_null())

# 模糊查询 (LIKE)
startswith_a = User.select().where(User.username % 'a%')
endswith_m = User.select().where(User.username % '%m')
contains_e = User.select().where(User.username % '%e%')
```

### 6.3 组合查询 (AND, OR)

使用 `&` (AND) 和 `|` (OR) 操作符组合多个查询条件。

```python
active_no_email = User.select().where((User.is_active == True) & (User.email.is_null()))
alice_or_bob = User.select().where((User.username == 'alice') | (User.username == 'bob'))
```

### 6.4 排序 (ORDER BY)

使用 `order_by()` 方法对查询结果排序。

```python
# 升序
users_by_username = User.select().order_by(User.username)

# 降序
users_by_creation_desc = User.select().order_by(User.created_at.desc())

# 多字段排序
users_ordered = User.select().order_by(User.is_active.desc(), User.username)
```

### 6.5 分页 (LIMIT, OFFSET)

使用 `limit()` 和 `offset()` 方法进行分页。

```python
page_1 = User.select().limit(10) # 前 10 条记录
page_2 = User.select().limit(10).offset(10) # 第 11 到 20 条记录
```

### 6.6 连接 (JOIN)

使用 `join()` 方法连接不同的模型。

```python
# 内连接 (INNER JOIN)
tweets_with_users = Tweet.select(Tweet.content, User.username).join(User).where(User.is_active == True)
for tweet, user in tweets_with_users.tuples().iterator():
    print(f"{user}: {tweet}")

# 外连接 (LEFT OUTER JOIN)
blogs_with_posts = Blog.select(Blog.name, Post.title).join(Post, JOIN.LEFT_OUTER)
for blog, post in blogs_with_posts.tuples().iterator():
    print(f"Blog: {blog}, Post: {post or 'No posts'}")
```

### 6.7 子查询 (Subqueries)

Peewee 支持子查询。

```python
active_users_with_tweets = User.select().where(User.id.in_(Tweet.select(Tweet.user_id).where(Tweet.is_published == True)))
for user in active_users_with_tweets:
    print(user.username)
```

### 6.8 聚合 (Aggregation)

Peewee 提供了聚合函数，如 `count()`, `sum()`, `avg()`, `max()`, `min()`.

```python
# 统计用户数量
user_count = User.select().count()
print(f"Total users: {user_count}")

# 统计活跃用户数量
active_user_count = User.select().where(User.is_active == True).count()
print(f"Active users: {active_user_count}")

# 获取最早的创建时间
earliest_creation = User.select(fn.Min(User.created_at)).scalar()
print(f"Earliest creation: {earliest_creation}")

# 分组聚合 (GROUP BY)
user_tweet_counts = (User
                     .select(User.username, fn.COUNT(Tweet.id).alias('tweet_count'))
                     .join(Tweet, JOIN.LEFT_OUTER)
                     .group_by(User.id, User.username)
                     .order_by(fn.COUNT(Tweet.id).desc()))
for user in user_tweet_counts:
    print(f"{user.username}: {user.tweet_count}")
```

## 7. 事务 (Transactions)

Peewee 提供了事务管理来确保数据库操作的原子性。

```python
try:
    with db.atomic():
        user = User.create(username='transaction_user', password='trans_pass')
        Tweet.create(user=user, content='This is a transactional tweet.')
        # 模拟错误，导致事务回滚
        # raise Exception("Something went wrong")
except Exception as e:
    print(f"Transaction failed: {e}")
```

你也可以手动管理事务：

```python
txn = db.transaction()
try:
    user = User.create(username='manual_trans', password='manual_pass')
    Tweet.create(user=user, content='Manual transaction tweet.')
    txn.commit()
except Exception as e:
    txn.rollback()
    print(f"Manual transaction failed: {e}")
```

## 8. 索引 (Indexes)

你可以在模型定义中为字段添加索引。

```python
class Email(BaseModel):
    user = ForeignKeyField(User)
    email = CharField()

    class Meta:
        indexes = (
            (('user', 'email'), True), # 联合唯一索引
            (('email',), False),       # 普通索引
        )

Email.create_table() # 需要显式创建表才能创建索引
```

## 9. 使用现有数据库

如果你需要操作一个已经存在的数据库，只需要定义你的模型并确保字段名称和类型与数据库表结构匹配即可。不需要调用 `create_tables()`。

## 10. Peewee ORM 的高级特性

### 10.1 模型方法

你可以在模型类中定义自定义方法来封装业务逻辑。

```python
class User(BaseModel):
    username = CharField(unique=True)
    password = CharField()

    def is_valid_password(self, password):
        return self.password == password

user = User.get(User.username == 'test_user')
if user.is_valid_password('correct_password'):
    print("Password is valid.")
```

### 10.2 类方法和静态方法

你可以在模型类中定义类方法和静态方法。

```python
class User(BaseModel):
    username = CharField(unique=True)
    password = CharField()

    @classmethod
    def get_or_create_user(cls, username, password):
        try:
            return cls.get(cls.username == username)
        except cls.DoesNotExist:
            return cls.create(username=username, password=password)

    @staticmethod
    def hash_password(password):
        # 实际应用中应该使用更安全的哈希方法
        return f"hashed_{password}"

new_user = User.get_or_create_user('newbie', 'new_pass')
hashed = User.hash_password('plain_text')
print(hashed)
```

### 10.3 信号 (Signals)

Peewee 提供了信号机制，允许你在模型生命周期的不同阶段执行自定义操作。

```python
from peewee import pre_save, post_save

@pre_save(User)
def on_user_pre_save(model_class, instance):
    instance.username = instance.username.lower()

@post_save(User)
def on_user_post_save(model_class, instance, created):
    if created:
        print(f"New user created: {instance.username}")
    else:
        print(f"User updated: {instance.username}")

user = User.create(username='TestUser', password='test') # 输出: New user created: testuser
user.password = 'updated'
user.save() # 输出: User updated: testuser
```

### 10.4 复合键 (Composite Keys)

如果你的表有多个列组成的主键，可以使用 `CompositeKey`。

```python
class Relationship(BaseModel):
    follower = ForeignKeyField(User, backref='following')
    following = ForeignKeyField(User, backref='followers')

    class Meta:
        primary_key = CompositeKey('follower', 'following')

Relationship.create_table()
Relationship.create(follower=user1, following=user2)
```

### 10.5 JSON 字段

Peewee 提供 `JSONField` 来存储 JSON 数据。

```python
class Configuration(BaseModel):
    settings = JSONField()

config = Configuration.create(settings={'theme': 'dark', 'notifications': True})
print(config.settings['theme'])
config.settings['font_size'] = 16
config.save()
```

### 10.6 HStore 字段 (PostgreSQL)

对于 PostgreSQL，Peewee 提供了 `HStoreField` 来存储键值对。

```python
from playhouse.postgres_ext import HStoreField

class UserProfile(BaseModel):
    user = ForeignKeyField(User, unique=True)
    attributes = HStoreField()

profile = UserProfile.create(user=user, attributes={'age': '30', 'city': 'Tokyo'})
print(profile.attributes['city'])
profile.attributes['occupation'] = 'Engineer'
profile.save()
```

### 10.7 Array 字段 (PostgreSQL)

对于 PostgreSQL，Peewee 提供了数组字段。

```python
from playhouse.postgres_ext import ArrayField, IntegerArrayField, CharArrayField

class BlogPost(BaseModel):
    title = CharField()
    tags = CharArrayField()
    related_ids = IntegerArrayField()

post = BlogPost.create(title='Array Example', tags=['python', 'peewee', 'postgres'], related_ids=[1, 2, 3])
print(post.tags[1])
print(post.related_ids)
```

## 11. 数据库迁移 (Migrations)

Peewee 本身不包含内置的迁移工具，但有一些第三方库可以与 Peewee 配合使用，例如 `peewee-migrate`。这些工具可以帮助你管理数据库模式的变更。

## 12. 测试 (Testing)

在测试你的应用时，你可能需要使用内存数据库或事务来避免影响实际数据。

```python
from peewee import SqliteDatabase

test_db = SqliteDatabase(':memory:')

class TestBaseModel(Model):
    class Meta:
        database = test_db

class TestUser(TestBaseModel):
    username = CharField(unique=True)

test_db.connect()
test_db.create_tables([TestUser])

def test_user_creation():
    user = TestUser.create(username='test')
    assert user.username == 'test'

test_user_creation()
test_db.close()
```

或者使用事务进行测试：

```python
def test_database_operations():
    with db.atomic():
        user = User.create(username='test_trans', password='trans')
        assert User.get_or_none(User.username == 'test_trans') is not None
        # 在事务块结束时，所有操作都会回滚，不会影响数据库的实际数据

test_database_operations()
```

## 13. 总结

Peewee 是一个简洁而强大的 Python ORM，它提供了你需要的大部分数据库操作功能，同时保持了代码的清晰和易读性。通过本文档，你应该能够开始使用 Peewee 构建你的数据库驱动的应用程序。记住查阅 Peewee 的官方文档以获取更深入的信息和高级用法。

```

```
