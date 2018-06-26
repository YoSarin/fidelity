#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import getpass
import traceback
from datetime import datetime
from lib.data_source import *


try:
    username = os.environ['FIDELITY_USERNAME'] if 'FIDELITY_USERNAME' in os.environ else ''
    password = os.environ['FIDELITY_PASSWORD'] if 'FIDELITY_PASSWORD' in os.environ else ''
    accountID = os.environ['FIDELITY_ACCOUNT_ID'] if 'FIDELITY_ACCOUNT_ID' in os.environ else ''
    securityID = os.environ['FIDELITY_SECURITY_ID'] if 'FIDELITY_SECURITY_ID' in os.environ else ''

    lastYear = datetime.today().year - 1
    parser = argparse.ArgumentParser(description="Fetch your data from fidelity and show them in CSV/other usefull formats needed to tax proclamation")
    parser.add_argument('--year', type=int, help=('Year about which do you care. Default is last year (%s)' % lastYear), default=lastYear)
    parser.add_argument('--gross_income', type=int, help=('Gross income per given year'))
    parser.add_argument('--total_premium', type=int, help=('Total premiums written per given year (Úhrn povinného pojistného)'))
    parser.add_argument('--generate_xls', action='store_true')
    parser.add_argument('--english', action='store_true', help=('If you want to generate xls in english, add this switch'))
    parser.add_argument('--password', action='store_true', help='Will show password prompt, even when you have your password stored in env variable (FIDELITY_PASSWORD)')
    parser.add_argument('--username', help=('Fidelity username (you can setup env variable instead - FIDELITY_USERNAME)'), default=username, required=(not username))
    parser.add_argument('--accountID', help=('Fidelity accountID (you can setup env variable instead - FIDELITY_ACCOUNT_ID); check fidelity_account_id_security_id.png to see where to find it'), default=accountID, required=(not accountID))
    parser.add_argument('--securityID', help=('Fidelity securityID (you can setup env variable instead - FIDELITY_SECURITY_ID); check fidelity_account_id_security_id.png to see where to find it'), default=securityID, required=(not securityID))
    args = parser.parse_args()

    if (args.password or not password):
        password = getpass.getpass(prompt=("Fidelity password for user %s: " % username))

    open, closed = fetchData(args.username, password, args.accountID, args.securityID)

    if (args.generate_xls):
        from lib.taxes import CreateXLS
        CreateXLS(open.FilterByYear(args.year), closed.FilterByYear(args.year), "taxes_" + str(args.year), args.gross_income, args.total_premium)

    else:
        print "\n".join(open.FilterByYear(args.year).csv())
        print closed
except ValueError as e:
    print "Troubles with fetching data - maybe too many attemps? Give fidelity a rest ;)"
    print traceback.print_exc()
except KeyboardInterrupt:
    print "You cancelled an op"
