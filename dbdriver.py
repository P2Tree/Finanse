from dbmodel import User, Book, Bill, Transfer, \
                          Account, AccountGroup, AccountStatMonth
from dbmodel import db
from utils import info, warning, error, ask
from datetime import datetime, date, time

class DatabaseDriver():
    def __init__(self):
        self.current_user = None
        self.create_database()

    def get_user(self):
        return self.current_user

    def get_all_accounts(self):
        accounts = Account.select().execute()
        return accounts

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
        user = User.get_or_none(email=email, password=password)
        if not user:
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

        group = AccountGroup.get_or_none(account_group_name=group_name, user_id=self.current_user.id)
        if not group:
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

    def create_account_stat_month(self, date_str, account_name, amount, adjust, interest_income,
                                  invest_income, normal_income, normal_outcome, transfer):
        account = Account.get_or_none(account_name=account_name, user_id=self.current_user.id)
        if not account:
            warning("Account %s is not existed." % account_name)
            return None

        stat_month = AccountStatMonth.get_or_none(date=date_str, account_id=account.id)
        if not stat_month:
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
        else:
            info("Statistic with account %s in month %s-%s is already existed." %
                    (account.account_name,
                        datetime.strptime(date_str, '%Y-%m-%d').year,
                        datetime.strptime(date_str, '%Y-%m-%d').month))

    def create_bill(self, amount, inout, account, date, time, comments, book):
        bill_id = Bill.insert(amount=amount, inout_type=inout, account_id=account.id,
                              billing_date=date, billing_time=time, comments=comments,
                              book_id=book.id, user_id=self.current_user.id)
        return bill_id

    def create_transfer(self, amount, from_account, to_account, date, time, comments, book):
        transfer_id = Transfer.insert(amount=amount, from_account_id=from_account.id,
                                      to_account_id=to_account.id, transfer_date=date,
                                      transfer_time=time, comments=comments,
                                      book_id=book.id, user_id=self.current_user.id)
        return transfer_id

def CreateTestBill(driver, book):
    account_gs = Account.get(account_name="工商银行储蓄卡")
    account_pf = Account.get(account_name="浦发银行信用卡")

    driver.create_bill(3.0, "收入", account_gs, date(2020, 11, 1), time(8, 0, 0),
                       "捡钱", book)
    driver.create_bill(60.0, "支出", account_pf, date(2020, 11, 1),
                       time(10, 20, 0), "买菜", book)
    info("Test bills are inserted.")

    driver.create_transfer(1000, account_gs, account_pf, date(2020, 11, 2),
                           time(10, 30, 00), "信用卡还款", book)
    info("Test transfers are inserted.")

def InitDatabase(driver):
    # 创建账本
    book = driver.create_book("日常账本")
    # 创建账户分组
    groups = []
    groups.append(driver.create_account_group("住房基金", "用于住房支出"))
    groups.append(driver.create_account_group("日常开支", "日常消费使用"))
    # 创建账户，并指定分组
    normal_accounts = []
    credit_accounts = []
    normal_accounts.append(driver.create_account("工商银行储蓄卡", False, "住房基金"))
    credit_accounts.append(driver.create_account("浦发银行信用卡", True, "日常开支"))
    # 创建账单条目
    CreateTestBill(driver, book)
    # 创建账户月统计信息
    # 日期、账户、余额、调整额、利息收入、投资收入、常规收入（>0）、常规支出（>0）、转账
    driver.create_account_stat_month("2020-10-01", "工商银行储蓄卡", 1000.2, 0.0, 0.8, -10.0, 5000.0, 19.8, -20.0)
    driver.create_account_stat_month("2020-10-30", "浦发银行信用卡", -110.5, 5.0, 0.0, 0.0, 0.0, 898.8, 20.0)

def CheckDatabase(driver):

    # 查看账户
    info("Check all of accounts in the datebase:")
    accounts = driver.get_all_accounts()
    for account in accounts:
        account_group_name = AccountGroup.get(id=account.account_group_id).account_group_name
        info("account: %s, is_credit: %s, init_balance: %f, remain_balance: %f, currency: %s, user: %s, group: %s" %
                (account.account_name, account.is_credit, account.init_balance,
                 account.remain_balance, account.currency, driver.get_user().nickname,
                 account_group_name))

        # 同时查看账户内的账单信息
        info("Check all of bills in the account %s" % account.account_name)
        bills = driver.get_all_bills(account)
        for bill in bills:
            book_name = Book.get(id=bill.book_id).book_name
            info("amount: %f, inout_type: %s, billing_date: %s, billing_time: %s, comments: %s, book: %s" %
                    (bill.amount, bill.inout_type, bill.billing_date,
                        bill.billing_time, bill.comments, book_name))

        # 同时查看账户的月统计信息
        info("Check all of month statistics of the account %s" % account.account_name)
        stat_months = driver.get_all_stat_months(account)
        for stat_month in stat_months:
            info("date: %s, amount: %f, adjust: %f, interest_income: %f, invest_income: %f, normal_income: %f, normal_outcome: %f, transfer: %f]" %
                    (stat_month.date, stat_month.amount,
                        stat_month.adjust, stat_month.interest_income,
                        stat_month.invest_income, stat_month.normal_income,
                        stat_month.normal_outcome, stat_month.transfer))
        info("Next account")

if __name__ == "__main__":
    db.connect(reuse_if_open = True)

    driver = DatabaseDriver()

    ins = ask("Sign in (1) or sign up (2): ")
    if ins == '1':
        driver.login()
    elif ins == '2':
        driver.create_user()
    else:
        error("Wrong input.")
        exit()

    InitDatabase(driver)

    CheckDatabase(driver)

    db.close()
