import peewee
from peewee import *
import datetime

db = MySQLDatabase('Finanse', user='root', passwd='yangliuming')

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    email = CharField(max_length = 30, unique = True)
    password = CharField(max_length = 64)
    nickname = CharField(max_length = 30)

class Book(BaseModel):
    book_name = CharField(max_length = 20, unique = True)
    is_default = BooleanField(default = False)
    user_id = ForeignKeyField(User, backref = "books")

class Bill(BaseModel):
    amount = FloatField(default = 0)
    inout_type = CharField(default = "支出", max_length = 10)
    created_datetime = DateTimeField(null = True, default = datetime.datetime.now)
    billing_date = DateField(null = True)
    billing_time = TimeField(null = True)
    comments = CharField(null = True, max_length = 50)
    book_id = ForeignKeyField(Book, backref = "bills")
    user_id = ForeignKeyField(User, backref = "bills")

class AccountGroup(BaseModel):
    account_group_name = CharField(max_length = 30)
    user_id = ForeignKeyField(User, backref = "accountgroups")
    comments = CharField(null = True, max_length = 50)

class Account(BaseModel):
    account_name = CharField(max_length = 30)
    is_credit = BooleanField(default = False)
    user_id = ForeignKeyField(User, backref = "accounts")
    account_group_id = ForeignKeyField(AccountGroup, backref = "accounts")

