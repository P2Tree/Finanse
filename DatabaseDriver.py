from DatabaseModel import User, Book, Bill, Account, AccountGroup
from DatabaseModel import db
import datetime

class DatabaseDriver():
    def __init__(self):
        self.current_user = None
        self.CreateDatabase()

    def CreateDatabase(self):
        User.create_table()
        Book.create_table()
        Bill.create_table()
        AccountGroup.create_table()
        Account.create_table()

    def Login(self):
        email = input("Info: Input login email: ")
        password = input("Info: Input password: ")
        user = User.get_or_none(email = email, password = password)
        if not user:
            print("Info: Not find you in the system.")
            ins = input("Info: Sign up? (y/n): ")
            if ins == 'y':
                user = CreateUser()
            else:
                exit()
        else:
            print("Info: Welcome you, %s" % user.nickname)

        self.current_user = user

    def CreateUser(self):
        email = input("Info: Input login email: ")
        password = input("Info: Input password: ")
        valid_password = input("Info: Input same password again: ")
        while password != valid_password:
            print("Warning: password wrong, try again: ")
            password = input("Info: Input password: ")
            valid_password = input("Info: Input same password again: ")

        nickname = input("Info: Input nickname: ")
        user = User.get_or_create(email = email, nickname = nickname, password = password)

        if user[1]:
            print("Info: New user %s created." % nickname)
        else:
            print("Info: User %s already existed." % nickname)

        self.current_user = user[0]

    def CreateBook(self, name):
        book_name = self.current_user.nickname + "的" + name
        current_book = Book.get_or_create( \
                book_name = book_name, is_default = True, user_id = self.current_user.id)

        if current_book[1]:
            print("Info: New book %s created." % book_name)
        else:
            print("Info: Book %s is already existed." % book_name)

        return current_book[0]

    def CreateTestBill(self, book):
        with db.atomic():
            Bill.insert_many([
                (3.0, "支出", datetime.date(2020, 11, 1), datetime.time(8, 0, 0), "地铁", book.id, self.current_user.id),
                (60.0, "支出", datetime.date(2020, 11, 1), datetime.time(10, 20, 0), "买菜", book.id, self.current_user.id)
                ], ['amount', 'inout_type', 'billing_date', 'billing_time', 'comments', 'book_id', 'user_id']
                ).execute()

    def CreateAccount(self, name, is_credit = False, group = None):
        if not group:
            group = AccountGroup.get_or_create(account_group_name = "未分组")[0]
        account = Account.get_or_create(account_name = name, is_credit = is_credit, user_id = self.current_user.id, account_group_id = group.id)

        if account[1]:
            print("Info: New account %s created." % name)
        else:
            print("Info: Account %s already existed." % name)

        return account[0]

    def CreateAccountGroup(self, name, comments = None):
        account_group = AccountGroup.get_or_create(account_group_name = name, comments = comments, user_id = self.current_user.id)

        if account_group[1]:
            print("Info: New account group %s created." % name)
        else:
            print("Info: Account group %s already existed." % name)

        return account_group[0]

if __name__ == "__main__":
    db.connect(reuse_if_open = True)

    driver = DatabaseDriver()

    ins = input("Sign in (1) or sign up (2): ")
    if ins == '1':
        user = driver.Login()
    elif ins == '2':
        user = driver.CreateUser()
    else:
        print("Error: Wrong input.")
        exit()
    book = driver.CreateBook("日常账本")
    driver.CreateTestBill(book)
    house_group = driver.CreateAccountGroup("住房基金", "用于住房支出")
    daily_group = driver.CreateAccountGroup("日常开支", "日常消费使用")
    driver.CreateAccount("工商银行储蓄卡", False, house_group)
    driver.CreateAccount("浦发银行信用卡", True, daily_group)

    db.close()
