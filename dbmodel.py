from peewee import *
import datetime
from utils import info

from app import db

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    email = CharField(max_length=30, unique=True)
    password = CharField(max_length=64)
    nickname = CharField(max_length=30)

class Book(BaseModel):
    book_name = CharField(max_length=20, unique=True)
    is_default = BooleanField(constraints=[SQL("DEFAULT False")])
    user_id = ForeignKeyField(User, backref="books")

class AccountGroup(BaseModel):
    account_group_name = CharField(max_length=30)
    comments = CharField(null=True, max_length=50)
    user_id = ForeignKeyField(User, backref="accountgroups")

class Account(BaseModel):
    account_name = CharField(max_length=30)
    is_credit = BooleanField(constraints=[SQL("DEFAULT False")])
    init_balance = FloatField(constraints=[Check('init_balance >= 0.0'),
                                             SQL("DEFAULT 0.0")])
    remain_balance = FloatField(constraints=[Check('remain_balance >= 0.0'),
                                               SQL("DEFAULT 0.0")])
    currency = CharField(constraints=[Check("currency='RMB' OR currency='Dollar'"),
                                      SQL("DEFAULT 'RMB'")])
    user_id = ForeignKeyField(User, backref="accounts")
    account_group_id = ForeignKeyField(AccountGroup, backref="accounts")

class Bill(BaseModel):
    amount = FloatField(constraints=[Check("amount >= 0.0"), SQL("DEFAULT 0.0")])
    inout_type = CharField(max_length=10,
                           constraints=[Check("inout_type='支出' OR inout_type='收入'"),
                                        SQL("DEFAULT '支出'")])
    created_datetime = DateTimeField(null=True,
                                     constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    billing_date = DateField(null=True)
    billing_time = TimeField(null=True)
    comments = CharField(null=True, max_length=50)
    account_id = ForeignKeyField(Account, backref="bills")
    book_id = ForeignKeyField(Book, backref="bills")
    user_id = ForeignKeyField(User, backref="bills")

class Transfer(BaseModel):
    amount = FloatField(constraints=[Check("amount >= 0.0"), SQL("DEFAULT 0.0")])
    created_datetime = DateTimeField(null=True,
                                     constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    transfer_date = DateField(null=True)
    transfer_time = TimeField(null=True)
    comments = CharField(null=True, max_length=50)
    from_account_id = ForeignKeyField(Account, backref="bills")
    to_account_id = ForeignKeyField(Account, backref="bills")
    book_id = ForeignKeyField(Book, backref="bills")
    user_id = ForeignKeyField(User, backref="bills")

class AccountStatMonth(BaseModel):
    date = DateField()
    account_id = ForeignKeyField(Account, backref="AccountStatMonths")
    amount = FloatField(constraints=[ SQL("DEFAULT 0.0")],
                        help_text="每月余额")
    adjust = FloatField(constraints=[SQL("DEFAULT 0.0")],
                        help_text="每月月初调整额度")
    interest_income = FloatField(constraints=[SQL("DEFAULT 0.0")],
                                 help_text="每月利息收入")
    invest_income = FloatField(constraints=[SQL("DEFAULT 0.0")],
                               help_text="每月投资收入")
    normal_income = FloatField(constraints=[Check("normal_income >= 0.0"),
                                            SQL("DEFAULT 0.0")],
                               help_text="每月普通收入，如工资")
    normal_outcome = FloatField(constraints=[Check("normal_outcome >= 0.0"),
                                             SQL("DEFAULT 0.0")],
                                help_text="每月普通支出")
    transfer = FloatField(constraints=[SQL("DEFAULT 0.0")],
                          help_text="每月账户间转账额度")

