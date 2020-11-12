# -*- coding:utf-8 -*-
from utils import info, warning, error, ask
from datetime import datetime, date, time
import csv

from dbdriver import DatabaseDriver
from dbdriver import NotFindItemError
from dbmodel import User, Bill, Transfer, \
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

    for bill_item in bills_reader:
        if driver.get_user().nickname != bill_item['user']:
            warning("Current bill's user is %s, not you." % bill_item['user'])
            continue

        try:
            account = driver.get_account(bill_item['account'])
        except NotFindItemError as err:
            warning(err.args[0])
            warning("Current bill insert failed.")
            continue

        driver.create_bill(float(bill_item['amount']), bill_item['inout'], account,
                           bill_item['billing_date'], bill_item['billing_time'],
                           bill_item['comments'])

    info("Test bills are inserted.")

def create_test_transfer(driver):
    try:
        filename = 'testdata/transfers.csv'
        transfer_file = open(filename, 'r')
        transfer_reader = csv.DictReader(transfer_file)
    except Exception():
        error("CSV file %s read failed." % filename)
        return

    for transfer_item in transfer_reader:
        if driver.get_user().nickname != transfer_item['user']:
            warning("Current transfer's user is %s, not you." % transfer_item['user'])
            continue

        try:
            from_account = driver.get_account(transfer_item['from_account'])
            to_account = driver.get_account(transfer_item['to_account'])
        except NotFindItemError as err:
            warning(err.args[0])
            warning("Current transfer insert failed.")
            continue

        driver.create_transfer(float(transfer_item['amount']), from_account, to_account,
                               transfer_item['transfer_date'], transfer_item['transfer_time'],
                               transfer_item['comments'])

    info("Test transfers are inserted.")

def create_test_account(driver):
    try:
        filename = 'testdata/accounts.csv'
        account_file = open(filename, 'r')
        account_reader = csv.DictReader(account_file)
    except Exception():
        error("CSV file %s read failed." % filename)
        return

    for account_item in account_reader:
        if driver.get_user().nickname != account_item['user']:
            warning("Current account's user is %s, not you." % account_item['user'])
            continue

        try:
            driver.get_account_group(name=account_item['group'])
        except NotFindItemError as err:
            warning(err.args[0])
            # create new account group at the meantime in create new account
            driver.create_account_group(account_item['group'])

        try:
            driver.get_account(name=account_item['name'])
        except NotFindItemError:
            driver.create_account(name=account_item['name'],
                                            is_credit=bool(account_item['is_credit']),
                                            group_name=account_item['group'],
                                            currency=account_item['currency'])
        else:
            warning("Account %s is already existed." % account_item['name'])

    info("Test accounts are created.")

def create_test_month_stat(driver):
    try:
        filename = 'testdata/month_stats.csv'
        stat_file = open(filename, 'r')
        stat_reader = csv.DictReader(stat_file)
    except Exception():
        error("CSV file %s read failed." % filename)
        return

    for stat in stat_reader:
        try:
            driver.get_account(name=stat['account'])
        except NotFindItemError:
            warning("Account %s is not existed." % stat['account'])
            continue

        driver.create_account_stat_month(
                stat['month'], stat['account'], stat['amount'], stat['adjust'],
                stat['interest_income'], stat['invest_income'], stat['normal_income'],
                stat['normal_outcome'], stat['transfer'])

    info("Test month statistics are created.")

def init_database(driver):
    # 创建账户和账户分组
    create_test_account(driver)
    # 创建账单条目
    create_test_bill(driver)
    create_test_transfer(driver)
    # 创建账户月统计信息
    # 日期、账户、余额、调整额、利息收入、投资收入、常规收入（>0）、常规支出（>0）、转账
    create_test_month_stat(driver)

def check_database(driver):
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
            info("amount: %f, inout_type: %s, billing_date: %s, billing_time: %s, comments: %s" %
                    (bill.amount, bill.inout_type, bill.billing_date,
                        bill.billing_time, bill.comments))

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

    db_driver = DatabaseDriver()

    ins = ask("Sign in (1) or sign up (2): ")
    if ins == '1':
        db_driver.login()
    elif ins == '2':
        db_driver.create_user()
    else:
        error("Wrong input.")
        exit()

    init_database(db_driver)

    # check_database(db_driver)

    #  db_driver.month_stat_sumup("2020-10")
    #  db_driver.month_stat_sumup("2020-11")
    db_driver.account_stat_sumup("工商银行储蓄卡", "2020-10")

    db.close()
