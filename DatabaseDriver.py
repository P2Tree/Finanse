from DatabaseModel import User, Book, Bill, Account, AccountGroup, AccountStatMonth
from DatabaseModel import db
import datetime

class DatabaseDriver():
    def __init__(self):
        self.current_user = None
        self.create_database()

    def getUser(self):
        return self.current_user

    def create_database(self):
        if not db.table_exists("user"):
            User.create_table()
        if not db.table_exists("book"):
            Book.create_table()
        if not db.table_exists("bill"):
            Bill.create_table()
        if not db.table_exists("accountgroup"):
            AccountGroup.create_table()
        if not db.table_exists("account"):
            Account.create_table()
        if not db.table_exists("accountstatmonth"):
            AccountStatMonth.create_table()

    def login(self):
        email = input("Info: Input login email: ")
        password = input("Info: Input password: ")
        user = User.get_or_none(email=email, password=password)
        if not user:
            print("Info: Not find you in the system.")
            ins = input("Info: Sign up? (y/n): ")
            if ins == 'y':
                self.create_user()
            else:
                exit()
        else:
            self.current_user = user
            print("Info: Welcome you, %s" % user.nickname)

    def create_user(self):
        email = input("Info: Input login email: ")
        password = input("Info: Input password: ")
        valid_password = input("Info: Input same password again: ")
        while password != valid_password:
            print("Warning: password wrong, try again: ")
            password = input("Info: Input password: ")
            valid_password = input("Info: Input same password again: ")

        nickname = input("Info: Input nickname: ")
        user = User.get_or_create(email=email, nickname=nickname, password=password)

        if user[1]:
            print("Info: New user %s created." % nickname)
        else:
            print("Info: User %s already existed." % nickname)

        self.current_user = user[0]

    def create_book(self, name):
        book_name = self.current_user.nickname + "的" + name
        current_book = Book.get_or_create(
                book_name=book_name, is_default=True, user_id=self.current_user.id)

        if current_book[1]:
            print("Info: New book %s created." % book_name)
        else:
            print("Info: Book %s is already existed." % book_name)

        return current_book[0]

    def create_account(self, name, is_credit=False, group_name=None):
        if not group_name:
            group = AccountGroup.get_or_create(account_group_name="未分组")[0]

        group = AccountGroup.get_or_none(account_group_name=group_name, user_id=self.current_user.id)
        if not group:
            print("Warning: Account group %s is not existed." % group_name)
            return None

        account = Account.get_or_create(account_name=name, is_credit=is_credit, user_id=self.current_user.id, account_group_id=group.id, currency="Dollar")

        if account[1]:
            print("Info: New account %s created." % name)
        else:
            print("Info: Account %s already existed." % name)

        return account[0]

    def create_account_group(self, name, comments=None):
        account_group = AccountGroup.get_or_create(account_group_name=name, comments=comments, user_id=self.current_user.id)

        if account_group[1]:
            print("Info: New account group %s created." % name)
        else:
            print("Info: Account group %s already existed." % name)

        return account_group[0]

    def create_account_stat_month(self, date, account_name, amount, adjust, interest_income,
                                  invest_income, normal_income, normal_outcome, transfer):
        account = Account.get_or_none(account_name=account_name, user_id=self.current_user.id)
        if not account:
            print("Warning: Account %s is not existed." % account_name)
            return None

        stat_month = AccountStatMonth.get_or_none(date=date, account_id=account.id)
        if not stat_month:
            stat_month = AccountStatMonth.create(date=date, account_id=account.id,
                                                 amount=amount, adjust=adjust,
                                                 interest_income=interest_income,
                                                 invest_income=invest_income,
                                                 normal_income=normal_income,
                                                 normal_outcome=normal_outcome,
                                                 transfer=transfer)
            print("item is inserted.")
        else:
            print("item is already existed.")

        print("[date: %s, account: %s, amount: %f, adjust: %f, interest_income: %f, invest_income: %f, normal_income: %f, normal_outcome: %f, transfer: %f]" %
              (stat_month.date, account.account_name, stat_month.amount,
               stat_month.adjust, stat_month.interest_income,
               stat_month.invest_income, stat_month.normal_income,
               stat_month.normal_outcome, stat_month.transfer))

def CreateTestBill(user, book):
    with db.atomic():
        Bill.insert_many([
            (3.0, "支出", datetime.date(2020, 11, 1), datetime.time(8, 0, 0), "地铁", book.id, user.id),
            (60.0, "支出", datetime.date(2020, 11, 1), datetime.time(10, 20, 0), "买菜", book.id, user.id)
            ], ['amount', 'inout_type', 'billing_date', 'billing_time', 'comments', 'book_id', 'user_id']
            ).execute()

def InitDatabase(driver):
    # 创建账本
    book = driver.create_book("日常账本")
    # 创建账单条目
    CreateTestBill(driver.getUser(), book)
    # 创建账户分组
    groups = []
    groups.append(driver.create_account_group("住房基金", "用于住房支出"))
    groups.append(driver.create_account_group("日常开支", "日常消费使用"))
    # 创建账户，并指定分组
    normal_accounts = []
    credit_accounts = []
    normal_accounts.append(driver.create_account("工商银行储蓄卡", False, "住房基金"))
    credit_accounts.append(driver.create_account("浦发银行信用卡", True, "日常开支"))
    # 创建账户月统计信息
    # 日期、账户、余额、调整额、利息收入、投资收入、常规收入（>0）、常规支出（>0）、转账
    driver.create_account_stat_month("2020-10-00", "工商银行储蓄卡", 1000.2, 0.0, 0.8, -10.0, 5000.0, 19.8, -20.0)
    driver.create_account_stat_month("2020-10-00", "浦发银行信用卡", -110.5, 5.0, 0.0, 0.0, 0.0, 898.8, 20.0)

if __name__ == "__main__":
    db.connect(reuse_if_open = True)

    driver = DatabaseDriver()

    ins = input("Sign in (1) or sign up (2): ")
    if ins == '1':
        driver.login()
    elif ins == '2':
        driver.create_user()
    else:
        print("Error: Wrong input.")
        exit()

    InitDatabase(driver)

    db.close()
