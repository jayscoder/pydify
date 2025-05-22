from peewee import Model, CharField, SqliteDatabase
from config import DATABASE_PATH

db = SqliteDatabase(DATABASE_PATH)

class BaseModel(Model):
    class Meta:
        database = db
        
class DifySite(BaseModel):
    base_url = CharField(max_length=255)
    email = CharField(max_length=255)
    password = CharField(max_length=255)