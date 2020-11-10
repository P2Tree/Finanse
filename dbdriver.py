from utils import info, warning, error, ask
from datetime import datetime, date, time

from dbmodel import User, Book, Bill, Transfer, \
                          Account, AccountGroup, AccountStatMonth
from app import db

class DatabaseDriver():
    def __init__(self):
        self.current_user = None
        self.create_database()

    def get_user(self):
        return self.current_user

    # May throw exception
    def get_account(self, account_name):
        try:
            account = Account.get(account_name=account_name)
        except Account.DoesNotExist:
            warning("Not find account %s" % account_name)
            raise Exception("Not find account %s" % account_name)
        else:
            return account

    def get_all_accounts(self):
        accounts = Account.select().execute()
        return accounts

    # May throw exception
    def get_book(self, book_name):
        try:
            book = Book.get(book_name=book_name)
        except Book.DoesNotExist:
            warning("Not find book %s" % book_name)
            raise Exception("Not find book %s" % book_name)
        else:
            return book

    def get_all_bills(self, account, book=None):
        if not book:
            bills = Bill.select().where(Bill.account_id==account.id and
                                        Bill.user_id==self.current_user.id).execute()
        return bills

    def get_all_stat_months(self, account, book=None):
        if not book:
            stat_months = AccountStatMonth.select().where(AccountStatMonth.account_id==account.id)
        return stat_months

    def create_database(self):
        if not db.table_exists("user"):
            User.create_table()
        if not db.table_exists("book"):
            Book.create_table()
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

    def create_book(self, name):
        book_name = self.current_user.nickname + "的" + name
        current_book = Book.get_or_create(
                book_name=book_name, is_default=True, user_id=self.current_user.id)

        if current_book[1]:
            info("New book %s created." % book_name)
        else:
            info("Book %s is already existed." % book_name)

        return current_book[0]

    def create_account(self, name, is_credit=False, group_name=None):
        if not group_name:
            group = AccountGroup.get_or_create(account_group_name="未分组")[0]

        try:
            group = AccountGroup.get(account_group_name=group_name, user_id=self.current_user.id)
        except AccountGroup.DoesNotExist:
            warning("Account group %s is not existed." % group_name)
            return None

        account = Account.get_or_create(account_name=name, is_credit=is_credit, user_id=self.current_user.id, account_group_id=group.id, currency="Dollar")

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

    def create_bill(self, amount, inout, account, date, time, comments, book):
        Bill.insert(amount=amount, inout_type=inout, account_id=account.id,
                    billing_date=date, billing_time=time, comments=comments,
                    book_id=book.id, user_id=self.current_user.id).execute()

    def create_transfer(self, amount, from_account, to_account, date, time, comments, book):
        Transfer.insert(amount=amount, from_account_id=from_account.id,
                        to_account_id=to_account.id, transfer_date=date,
                        transfer_time=time, comments=comments,
                        book_id=book.id, user_id=self.current_user.id).execute()

