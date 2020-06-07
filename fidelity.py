#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import getpass
import traceback
from datetime import datetime
from lib.data_source import *
from lib.clean_cache import *


try:
    username = os.environ['FIDELITY_USERNAME'] if 'FIDELITY_USERNAME' in os.environ else ''
    password = os.environ['FIDELITY_PASSWORD'] if 'FIDELITY_PASSWORD' in os.environ else ''
    accountID = os.environ['FIDELITY_ACCOUNT_ID'] if 'FIDELITY_ACCOUNT_ID' in os.environ else ''
    securityID = os.environ['FIDELITY_SECURITY_ID'] if 'FIDELITY_SECURITY_ID' in os.environ else ''

    lastYear = datetime.today().year - 1
    parser = argparse.ArgumentParser(description="Fetch your data from fidelity and show them in CSV/other usefull formats needed to tax proclamation")
    subparsers = parser.add_subparsers(dest="action")

    dataSubParser = subparsers.add_parser('fetch_data', help='will download json data from the fidelity (currently broken)')
    dataSubParser.add_argument('--password', action='store_true', help='Will show password prompt, even when you have your password stored in env variable (FIDELITY_PASSWORD)')
    dataSubParser.add_argument('--username', help=('Fidelity username (you can setup env variable instead - FIDELITY_USERNAME)'), default=username, required=(not username))
    dataSubParser.add_argument('--accountID', help=('Fidelity accountID (you can setup env variable instead - FIDELITY_ACCOUNT_ID); check fidelity_account_id_security_id.png to see where to find it'), default=accountID, required=(not accountID))
    dataSubParser.add_argument('--securityID', help=('Fidelity securityID (you can setup env variable instead - FIDELITY_SECURITY_ID); check fidelity_account_id_security_id.png to see where to find it'), default=securityID, required=(not securityID))
    dataSubParser.add_argument('--reload', help=('You want to reload all the data (including stock price and currency exchange rate)?'), action="store_true")
    

    xlsSubParser = subparsers.add_parser('generate_xls', help='Will generate xlsx file in same folder where script is located')
    xlsSubParser.add_argument('--year', type=int, help=('Year about which do you care. Default is last year (%s)' % lastYear), default=lastYear)
    xlsSubParser.add_argument('--gross_income', type=int, help=('Gross income per given year'))
    xlsSubParser.add_argument('--total_premium', type=int, help=('Total premiums written per given year (Úhrn povinného pojistného)'))
    xlsSubParser.add_argument('--english', action='store_true', help=('If you want to generate xls in english, add this switch'))

    sellSubParser = subparsers.add_parser('simulate_sell', help="Show how much money will you have to pay if you decide to sell your lots")
    sellSubParser.add_argument('--expected_price', type=float, help="Expected price of shares at the moment of sell")
    sellSubParser.add_argument('--expected_czk_usd', type=float, help="Expected CZK/USD exchange rate at the moment of sell")
    sellSubParser.add_argument('--expected_additional_stocks', type=float, help="if you expect additional stocks to have at the time of sell, specify the amount here (they'll be counted into shares that needs to be taxed)", default=0)
    sellSubParser.add_argument('--date', type=lambda d: datetime.strptime(d, '%Y-%m-%d'), help="Expected date of sell", default=datetime.now().strftime("%Y-%m-%d"))

    testSubParser = subparsers.add_parser('csv')
    testSubParser.add_argument('--year', type=int, help=('Year about which do you care. Default is last year (%s)' % lastYear), default=lastYear)
    
    testSubParser = subparsers.add_parser('test')

    args = parser.parse_args()

    if args.action == "test":
        print "nothing to do"
    else:
        cleanCache()

        if (args.action == "generate_xls"):
            open, closed = fetchData()

            from tasks.create_xls import CreateXLS
            CreateXLS(open.BoughtInYear(args.year), closed.BoughtInYear(args.year), closed.SoldInYear(args.year), "taxes_" + str(args.year), args.gross_income, args.total_premium)
        elif args.action == "simulate_sell":
            open, closed = fetchData()

            from tasks.sell_simulator import SellSimulator
            from lib.lots import Lot
            expectedPrice = args.expected_price if args.expected_price else Lot.CurrentMSFTPrice()
            SellSimulator(open, expectedPrice, args.date, args.expected_additional_stocks)
            Lot.SaveCoursesCache()
        elif args.action == "fetch_data":    
            if args.reload:
                cleanCache(true)
            if (args.password or not password):
                password = getpass.getpass(prompt=("Fidelity password for user %s: " % username))
            reloadCacheFromFidelity(args.username, password, args.accountID, args.securityID)
        elif args.action == "csv":
            open, closed = fetchData()
            print "\n".join(open.BoughtInYear(args.year).csv() + closed.BoughtInYear(args.year).csv())
            print "\n".join(closed.SoldInYear(args.year).csv())

except ValueError as e:
    print "Troubles with fetching data - maybe too many attemps? Give fidelity a rest ;)"
    print traceback.print_exc()
except KeyboardInterrupt:
    print "You cancelled an op"
