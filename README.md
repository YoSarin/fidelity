# Fidelity tool
This python script gathers information about shares you've got in last year and outputs nice XLSX sheet with information useful for your tax proclamation (in CZ only)

## Use at your own risk
I am not responsible for your use of outputs of this script. If you want to use it for taxation purposes, you are doing so **on your own risk**.

## Usage
Script is CLI tool, you need to have ```python2.7``` installed. All the requirements are in ```requirements.txt``` file, install them via pip (```pip install -r requirements.txt --user```).
```
$ ./fidelity.py -h
usage: fidelity.py [-h] [--password] [--username USERNAME]
                   [--accountID ACCOUNTID] [--securityID SECURITYID]
                   {generate_xls,simulate_sell} ...

Fetch your data from fidelity and show them in CSV/other usefull formats
needed to tax proclamation

positional arguments:
  {generate_xls,simulate_sell}
    generate_xls        Will generate xlsx file in same folder where script is
                        located
    simulate_sell       Show how much money will you have to pay if you decide
                        to sell your lots

optional arguments:
  -h, --help            show this help message and exit
  --password            Will show password prompt, even when you have your
                        password stored in env variable (FIDELITY_PASSWORD)
  --username USERNAME   Fidelity username (you can setup env variable instead
                        - FIDELITY_USERNAME)
  --accountID ACCOUNTID
                        Fidelity accountID (you can setup env variable instead
                        - FIDELITY_ACCOUNT_ID); check
                        fidelity_account_id_security_id.png to see where to
                        find it
  --securityID SECURITYID
                        Fidelity securityID (you can setup env variable
                        instead - FIDELITY_SECURITY_ID); check
                        fidelity_account_id_security_id.png to see where to
                        find it

$ ./fidelity.py generate_xls -h
usage: fidelity.py generate_xls [-h] [--year YEAR]
                                [--gross_income GROSS_INCOME]
                                [--total_premium TOTAL_PREMIUM] [--english]

optional arguments:
  -h, --help            show this help message and exit
  --year YEAR           Year about which do you care. Default is last year
                        (2017)
  --gross_income GROSS_INCOME
                        Gross income per given year
  --total_premium TOTAL_PREMIUM
                        Total premiums written per given year (Úhrn
                        povinného pojistného)
  --english             If you want to generate xls in english, add this
                        switch

$ ./fidelity.py simulate_sell -h
usage: fidelity.py simulate_sell [-h] [--expected_price EXPECTED_PRICE]
                                 [--expected_czk_usd EXPECTED_CZK_USD]
                                 [--expected_additional_stocks EXPECTED_ADDITIONAL_STOCKS]
                                 [--date DATE]

optional arguments:
  -h, --help            show this help message and exit
  --expected_price EXPECTED_PRICE
                        Expected price of shares at the moment of sell
  --expected_czk_usd EXPECTED_CZK_USD
                        Expected CZK/USD exchange rate at the moment of sell
  --expected_additional_stocks EXPECTED_ADDITIONAL_STOCKS
                        if you expect additional stocks to have at the time of
                        sell, specify the amount here (they'll be counted into
                        shares that needs to be taxed)
  --date DATE           Expected date of sell
```
## Where to get the AccountID and SecurityID?
![Image showing where to gather these fields](fidelity_account_id_security_id.png)
## Example
```./fidelity.py --generate_xls --gross_income 123456 --total_premium 123456```
## Translation
Output is partially localized, not all strings are covered. Any help appreciated.
