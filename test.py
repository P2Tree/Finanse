# -*- coding:utf-8 -*-
from utils import info, warning, error, ask
from datetime import datetime, date, time
import csv

from dbdriver import DatabaseDriver
from dbdriver import NotFindItemError
from dbmodel import User, Book, Bill, Transfer, \
                          Account, AccountGroup, AccountStatMonth
from app import db

def create_test_bill(driver):
    try:
        filename = 'testdata/bills.csv'
        bills_file = open(filename, 'r')
        bills_reader = csv.DictReader(bills_file)
    except Exception():
        error("CSV file %s read failed." % filename)
        return

    for bill in bills_reader:
        if driver.get_user().nickname != bill['user']:
            warning("Current bill's user is %s, not you." % bill['user'])
            continue

        try:
            account = driver.get_account(bill['account'])
            book = driver.get_book(bill['book'])
        except NotFindItemError as e:
            warning(e.args[0])
            warning("Current bill insert failed.")
            continue

        driver.create_bill(float(bill['amount']), bill['inout'], account,
                           bill['billing_date'], bill['billing_time'],
                           bill['comments'], book)

    info("Test bills are inserted.")

def create_test_transfer(driver):
    try:
        filename = 'testdata/transfers.csv'
        transfer_file = open(filename, 'r')
        transfer_reader = csv.DictReader(transfer_file)
    except Exception():
        error("CSV file %s read failed." % filename)
        return

    for transfer in transfer_reader:
        if driver.get_user().nickname != transfer['user']:
            warning("Current transfer's user is %s, not you." % transfer['user'])
            continue

        try:
            from_account = driver.get_account(transfer['from_account'])
            to_account = driver.get_account(transfer['to_account'])
            book = driver.get_book(transfer['book'])
        except NotFindItemError as e:
            warning(e.args[0])
            warning("Current transfer insert failed.")
            continue

        driver.create_transfer(float(transfer['amount']), from_account, to_account,
                               transfer['transfer_date'], transfer['transfer_time'],
                               transfer['comments'], book)

    info("Test transfers are inserted.")

def create_test_account(driver):
    try:
        filename = 'testdata/accounts.csv'
        account_file = open(filename, 'r')
        account_reader = csv.DictReader(account_file)
    except Exception():
        error("CSV file %s read failed." % filename)
        return

    for account in account_reader:
        if driver.get_user().nickname != account['user']:
            warning("Current account's user is %s, not you." % account['user'])
            continue

        try:
            driver.get_account_group(name=account['group'])
        except NotFindItemError as e:
            warning(e.args[0])
            # create new account group at the meantime in create new account
            driver.create_account_group(account['group'])

        try:
            account = driver.get_account(name=account['name'])
        except NotFindItemError:
            account = driver.create_account(name=account['name'],
                                            is_credit=bool(account['is_credit']),
                                            group_name=account['group'],
                                            currency=account['currency'])
        else:
            warning("Account %s is already existed." % account['name'])

    info("Test accounts are created.")

def InitDatabase(driver):
    # 创建账本
    driver.create_book("日常账本")
    # 创建账户和账户分组
    create_test_account(driver)
    # 创建账单条目
    create_test_bill(driver)
    create_test_transfer(driver)
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
