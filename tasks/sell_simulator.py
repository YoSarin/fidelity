#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
from lib.lots import Lot

def SellSimulator(lots, sellingPrice, sellingDate, expectedAdditionalStocks):
    tax = 0.15
    minimalYearsToAvoidTaxes = 3
    czk_usd = Lot.CZK_price_at_date(datetime.now())
    lots.TaxesIfSold(sellingPrice, sellingDate, minimalYearsToAvoidTaxes, tax, czk_usd, expectedAdditionalStocks)
