from utils import info, warning, error, ask
from datetime import datetime, date, time
import csv

from dbdriver import DatabaseDriver
from dbmodel import User, Book, Bill, Transfer, \
                          Account, AccountGroup, AccountStatMonth
from app import db

def CreateTestBill(driver):
    try:
        filename = "testdata/bills.csv"
        billsFile = open(filename, "r")
        billsReader = csv.DictReader(billsFile)
    except:
        error("CSV file %s read failed." % filename)
        return

    for bill in billsReader:
        if driver.get_user().nickname != bill["user"]:
            warning("Current bill's user is %s, not you." % bill["user"])
            continue

        try:
            account = driver.get_account(bill["account"])
            book = driver.get_book(bill["book"])
        except:
            warning("Current bill insert failed.")
            continue

        driver.create_bill(float(bill["amount"]), bill["inout"], account, bill["billing_date"],
                           bill["billing_time"], bill["comments"], book)

    info("Test bills are inserted.")

def CreateTestTransfer(driver):
    try:
        filename = "testdata/transfers.csv"
        transferFile = open(filename, "r")
        transferReader = csv.DictReader(transferFile)
    except:
        error("CSV file %s read failed." % filename)
        return

    for transfer in transferReader:
        if driver.get_user().nickname != transfer["user"]:
            warning("Current transfer's user is %s, not you." % transfer["user"])
            continue

        try:
            from_account = driver.get_account(transfer["from_account"])
            to_account = driver.get_account(transfer["to_account"])
            book = driver.get_book(transfer["book"])
        except:
            warning("Current transfer insert failed.")
            continue

        driver.create_transfer(float(transfer["amount"]), from_account, to_account, transfer["transfer_date"],
                               transfer["transfer_time"], transfer["comments"], book)

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
    normal_accounts.append(driver.create_account("工商银行储蓄卡", False, "储备消费"))
    normal_accounts.append(driver.create_account("朝朝盈", False, "保本应急"))
    credit_accounts.append(driver.create_account("浦发银行信用卡", True, "日常开支"))
    # 创建账单条目
    CreateTestBill(driver)
    CreateTestTransfer(driver)
    # 创建账户月统计信息
    # 日期、账户、余额、调整额、利息收入、投资收入、常规收入（>0）、常规支出（>0）、转账
    driver.create_account_stat_month("2020-10", "工商银行储蓄卡", 1000.2, 0.0, 0.8, -10.0, 5000.0, 89.8, -20.0)
    driver.create_account_stat_month("2020-11", "工商银行储蓄卡", 2000.2, 1.0, 0.2, 30.0, 5000.0, 50.8, -20.0)
    driver.create_account_stat_month("2020-10", "浦发银行信用卡", -110.5, 5.0, 0.0, 0.0, 0.0, 898.8, 20.0)

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
