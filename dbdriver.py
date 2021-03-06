# -*- coding:utf-8 -*-
"""
This module is used for drive database and provide APIs to operate the database.
"""
from datetime import datetime
from utils import info, error, warning, ask

from dbmodel import User, Bill, Transfer, \
                          Account, AccountGroup, AccountStatMonth
from app import db

class NotFindItemError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
    pass

class DatabaseDriver():
    def __init__(self):
        self.current_user = None
        self.create_database()

    def get_user(self):
        return self.current_user

    # May throw exception
    def get_account(self, name):
        try:
            account = Account.get(account_name=name)
        except Account.DoesNotExist:
            raise NotFindItemError("Not find account %s." % name)
        else:
            return account

    # May throw exception
    def get_account_group(self, name):
        try:
            group = AccountGroup.get(account_group_name=name)
        except AccountGroup.DoesNotExist:
            raise NotFindItemError("Not find account group %s." % name)
        else:
            return group

    def get_all_accounts(self):
        accounts = Account.select().execute()
        return accounts

    def get_all_bills(self, account):
        bills = Bill.select().where(Bill.account_id==account.id and
                                    Bill.user_id==self.current_user.id).execute()
        return bills

    def get_all_stat_months(self, account):
        stat_months = AccountStatMonth.select().where(AccountStatMonth.account_id==account.id)
        return stat_months

    def create_database(self):
        if not db.table_exists("user"):
            User.create_table()
        if not db.table_exists("accountgroup"):
            AccountGroup.create_table()
        if not db.table_exists("account"):
            Account.create_table()
        if not db.table_exists("bill"):
            Bill.create_table()
        if not db.table_exists("transfer"):
            Transfer.create_table()
        if not db.table_exists("accountstatmonth"):
            AccountStatMonth.create_table()

    def login(self):
        email = ask("Input login email: ")
        password = ask("Input password: ")
        try:
            user = User.get(email=email, password=password)
        except User.DoesNotExist:
            info("Not find you in the system.")
            ins = ask("Sign up? (y/n): ")
            if ins == 'y':
                self.create_user()
            else:
                exit()
        else:
            self.current_user = user
            info("Welcome you, %s" % user.nickname)

    def create_user(self):
        email = ask("Input login email: ")
        password = ask("Input password: ")
        valid_password = ask("Input same password again: ")
        while password != valid_password:
            warning("password wrong, try again: ")
            password = ask("Input password: ")
            valid_password = ask("Input same password again: ")

        nickname = ask("Input nickname: ")
        user = User.get_or_create(email=email, nickname=nickname, password=password)

        if user[1]:
            info("New user %s created." % nickname)
        else:
            info("User %s already existed." % nickname)

        self.current_user = user[0]

    def create_account(self, name, is_credit=False, group_name=None, currency=None):
        if not group_name:
            group = AccountGroup.get_or_create(account_group_name="未分组")[0]

        if not currency:
            currency = "RMB"

        try:
            group = AccountGroup.get(account_group_name=group_name, user_id=self.current_user.id)
        except AccountGroup.DoesNotExist:
            warning("Account group %s is not existed." % group_name)
            return None

        account = Account.get_or_create(account_name=name, is_credit=is_credit,
                                        user_id=self.current_user.id,
                                        account_group_id=group.id,
                                        currency=currency)

        if account[1]:
            info("New account %s created." % name)
        else:
            info("Account %s already existed." % name)

        return account[0]

    def create_account_group(self, name, comments=None):
        account_group = AccountGroup.get_or_create(account_group_name=name, comments=comments, user_id=self.current_user.id)

        if account_group[1]:
            info("New account group %s created." % name)
        else:
            info("Account group %s already existed." % name)

        return account_group[0]

    def create_account_stat_month(self, month_str, account_name, amount, adjust, interest_income,
                                  invest_income, normal_income, normal_outcome, transfer):
        try:
            account = Account.get(account_name=account_name, user_id=self.current_user.id)
        except Account.DoesNotExist:
            warning("Account %s is not existed." % account_name)
            return None

        date_str = month_str + "-01"
        try:
            stat_month = AccountStatMonth.get(date=date_str, account_id=account.id)
            info("Statistic with account %s in month %s-%s is already existed." %
                    (account.account_name,
                        datetime.strptime(date_str, '%Y-%m-%d').year,
                        datetime.strptime(date_str, '%Y-%m-%d').month))
        except AccountStatMonth.DoesNotExist:
            stat_month = AccountStatMonth.create(date=date_str, account_id=account.id,
                                                 amount=amount, adjust=adjust,
                                                 interest_income=interest_income,
                                                 invest_income=invest_income,
                                                 normal_income=normal_income,
                                                 normal_outcome=normal_outcome,
                                                 transfer=transfer)
            info("Statistic with account %s in month %s-%s is inserted." %
                    (account.account_name,
                        datetime.strptime(date_str, '%Y-%m-%d').year,
                        datetime.strptime(date_str, '%Y-%m-%d').month))

    def create_bill(self, amount, inout, account, date, time, comments):
        Bill.insert(amount=amount, inout_type=inout, account_id=account.id,
                    billing_date=date, billing_time=time, comments=comments,
                    user_id=self.current_user.id).execute()

    def create_transfer(self, amount, from_account, to_account, date, time, comments):
        Transfer.insert(amount=amount, from_account_id=from_account.id,
                        to_account_id=to_account.id, transfer_date=date,
                        transfer_time=time, comments=comments,
                        user_id=self.current_user.id).execute()

    def month_stat_sumup(self, month):
        stat_months = AccountStatMonth.select().where(
                AccountStatMonth.date==month+'-01')

        if not stat_months:
            warning("No statistic item be found in %s month" % month)
            return

        sumups = {'amount': 0.0, 'adjust': 0.0, 'interest_income': 0.0,
                'invest_income': 0.0, 'normal_income': 0.0, 'normal_outcome': 0.0,
                'transfer': 0.0}
        for stat in stat_months:
            sumups['amount'] += stat.amount
            sumups['adjust'] += stat.adjust
            sumups['interest_income'] += stat.interest_income
            sumups['invest_income'] += stat.invest_income
            sumups['normal_income'] += stat.normal_income
            sumups['normal_outcome'] += stat.normal_outcome
            sumups['transfer'] += stat.transfer

        info("Statistic data in %s is:" % month)
        for k,v in sumups.items():
            info("sumup %s: %f" % (k, v))

    def account_stat_sumup(self, account_name, month):
        try:
            account = self.get_account(account_name)
        except NotFindItemError as err:
            warning(err.args[0])
            return

        stat_account = AccountStatMonth.select().where(
                AccountStatMonth.account_id==account.id,
                AccountStatMonth.date==month+'-01')

        if not stat_account:
            warning("No statistic item be found of account %s" % account.account_name)
            return

        reminde = 0.0
        amount = 0.0
        for stat in stat_account:
            reminde += stat.adjust + stat.interest_income + stat.invest_income + \
                      stat.normal_income + stat.normal_outcome + stat.transfer
            amount += stat.amount

        info("Amount remaind of %s in %s is: %f" % (account_name, month, reminde))
        info("Amount amount of %s in %s is: %f" % (account_name, month, amount))




