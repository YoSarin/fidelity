#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xlsxwriter
from enum import Enum
from copy import copy, deepcopy

from lib.translator import _, setLang
from lib.lots import Source

def groupByDate(lots):
    output = {}
    for lot in lots:
        if lot.acquisitionDate in output and round(lot.pricePaid, 2) == round(output[lot.acquisitionDate].pricePaid, 2):
            output[lot.acquisitionDate].quantity += lot.quantity
        elif lot.acquisitionDate in output:
            print(lot.csv())
            print(output[lot.acquisitionDate].csv())
            raise Exception("Two acquision at same date (%s), with different price per share (%s != %s)" % (lot.acquisitionDate, lot.pricePaid, output[lot.acquisitionDate].pricePaid))
        else:
            output[lot.acquisitionDate] = deepcopy(lot)

    return sorted([output[date] for date in output], key = lambda x: x.acquisitionDate.strftime("%Y-%m-%d"))

def CreateXLS(boughtOpen, boughtClosed, sold, filename, grossIncome, totalPremium):
    setLang('cs_cz')
    wb = xlsxwriter.Workbook(filename + '.xlsx')
    ws = wb.add_worksheet()

    f = FormatLibrary(wb)

    ws.set_column('A:A', 45)
    ws.set_column('B:ZZ', 25)

    # formats

    # table == Employee income ==
    ws.write('A1', _('Employee income'))

    ws.write('A3', _("Source"))
    ws.write('A4', _("Wage (Skype Czech Republic)"))
    ws.write('A5', _("Stock awards (bonuses - shares)"))
    ws.write('A6', _("ESPP (preferential purchase of employee shares)"))
    ws.write('A7', _("Dividents granted"))
    ws.write('A8', _("Stocks sell"))
    ws.write('A9', _("Total"), f.F(Format.Result))

    ws.write('B3', _('Gross income'))
    ws.write('B4', grossIncome, f.F(Format.CZK))
    ws.write('B5', "TODO:Count awards sum", f.F(Format.Green, Format.CZK))
    ws.write('B6', "TODO:Count ESPP sum", f.F(Format.Blue, Format.CZK))
    ws.write('B7', "TODO:Count Dividents sum", f.F(Format.Yellow, Format.CZK))
    ws.write('B8', "TODO:Count Stock sell sum", f.F(Format.Orange, Format.CZK))
    ws.write('B9', "=SUM(B4:B8)", f.F(Format.Result, Format.CZK))

    ws.write('C3', _('Total premiums written'))
    ws.write('C4', totalPremium, f.F(Format.CZK))
    ws.write('C5', 0, f.F(Format.Green, Format.CZK))
    ws.write('C6', 0, f.F(Format.Blue, Format.CZK))
    ws.write('C7', 0, f.F(Format.Yellow, Format.CZK))
    ws.write('C8', 0, f.F(Format.Orange, Format.CZK))
    ws.write('C9', "=SUM(C4:C8)",  f.F(Format.Result, Format.CZK))

    ws.write('D3', _('Total'))
    ws.write('D4', '=SUM(B4:C4)', f.F(Format.CZK))
    ws.write('D5', '=SUM(B5:C5)', f.F(Format.Green, Format.CZK))
    ws.write('D6', '=SUM(B6:C6)', f.F(Format.Blue, Format.CZK))
    ws.write('D7', '=SUM(B7:C7)', f.F(Format.Yellow, Format.CZK))
    ws.write('D8', '=SUM(B8:C8)', f.F(Format.Orange, Format.CZK))
    ws.write('D9', "=SUM(D4:D8)",  f.F(Format.Gray, Format.Result, Format.DoubleBox, Format.CZK, Format.Bold))

    row = 11
    for source in Source.List():
        lots = groupByDate(boughtOpen.FilterBySource(source).lots + boughtClosed.FilterBySource(source).lots)
        if source != Source.DIVIDEND:
            row = SharesRows(lots, source, ws, f, row)
        else:
            row = DividentsRows(lots, source, ws, f, row)

    row = SoldSharesRows(sold.lots, source, ws, f, row)

    wb.close()

def columnName(col):
    lenght, remainder = divmod(col, ord('Z') - ord('A') + 1)
    if lenght > 0:
        return columnName(lenght - 1) + chr(ord('A') + remainder)
    return chr(ord('A') + remainder)

def SoldSharesRows(lots, source, ws, f, startingRow):
    row = startingRow
    ws.merge_range("B%s:%s%s" % (row + 0 + 1, columnName(len(lots)), row + 0 + 1), _("Stocks sell"), f.F(Format.Top, Format.Right, Format.Left, Format.CenterText))
    ws.write(row+1, 0, _("Přepočty měn a zisků"))
    ws.write(row+2, 0, _("Počet akcií"))
    ws.write(row+3, 0, _("Nákupní cena akcie (USD)"))
    ws.write(row+4, 0, _("Prodejní cena akcie (USD)"))
    ws.write(row+5, 0, _("Příjem v USD"))
    ws.write(row+6, 0, _("Datum prodeje"))
    ws.write(row+7, 0, _("Datum nákupu"))
    ws.write(row+8, 0, _("Je danitelné"))
    ws.write(row+9, 0, _("Použitý kurz CZK/USD"))
    ws.write(row+10, 0, _("Zisk v Kč"))
    col = 1
    colLetter = columnName(col)
    for lot in lots:
        border = None
        if col == 1:
            border = Format.Left
        elif col == (1 + len(lots) - 1):
            border = Format.Right
        colLetter = columnName(col)

        ws.write(row+1, col, _("Stock sell") + " - " + _(lot.sellDate.strftime("%B")), f.F(border))
        ws.write(row+2, col, lot.quantity, f.F(border))
        ws.write(row+3, col, lot.priceReal, f.F(Format.USD, border))
        ws.write(row+4, col, lot.sellPrice, f.F(Format.USD, border))
        ws.write(row+5, col, "=%s%s*(%s%s-%s%s)" % (colLetter, row+2+1, colLetter, row+4+1, colLetter, row+3+1), f.F(Format.USD, border))
        ws.write(row+6, col, lot.sellDate, f.F(Format.Date, border))
        ws.write(row+7, col, lot.acquisitionDate, f.F(Format.Date, border))
        ws.write(row+8, col, lot.TaxApplicable(), f.F(Format.Date, border))
        ws.write(row+9, col, lot.czkUsdAtSellDate(), f.F(Format.CZK_USD, border))
        finalFormat = f.F(Format.Orange, Format.CZK, Format.Result, Format.Bottom, border)
        ws.write(row+10, col, "=%s%s*%s%s" % (colLetter, row+5+1, colLetter, row+9+1), finalFormat)
        col += 1

    rangePrice = "B%s:%s%s" % (row+10+1, colLetter, row+10+1)
    rangeTaxable = "B%s:%s%s" % (row+8+1, colLetter, row+8+1)
    ws.write('B8', "=SUMIF(%s, TRUE, %s)" % (rangeTaxable, rangePrice), f.F(Format.Orange, Format.CZK))

    return row + 13


def SharesRows(lots, source, ws, f, startingRow):
    row = startingRow
    ws.merge_range("B%s:%s%s" % (row + 0 + 1, chr(ord('A') + len(lots)), row + 0 + 1), _(source.value), f.F(Format.Top, Format.Right, Format.Left, Format.CenterText))
    ws.write(row+1, 0, _("Přepočty měn a zisků"))
    ws.write(row+2, 0, _("Počet akcií"))
    ws.write(row+3, 0, _("Obchodní cena akcie (USD)"))
    ws.write(row+4, 0, _("Nákupní cena akcie (USD)"))
    ws.write(row+5, 0, _("Příjem v USD"))
    ws.write(row+6, 0, _("Strženo na US daních"))
    ws.write(row+7, 0, _("Datum"))
    ws.write(row+8, 0, _("Použitý kurz CZK/USD"))
    ws.write(row+9, 0, _("Příjem v Kč"))
    col = 1
    colLetter = columnName(col)
    for lot in lots:
        border = None
        if col == 1:
            border = Format.Left
        elif col == (1 + len(lots) - 1):
            border = Format.Right
        colLetter = columnName(col)

        ws.write(row+1, col, _("Stock") + " - " + str(lot.source.value) + " - " + _(lot.acquisitionDate.strftime("%B")), f.F(border))
        ws.write(row+2, col, lot.quantity, f.F(border))
        ws.write(row+3, col, lot.priceReal, f.F(Format.USD, border))
        ws.write(row+4, col, lot.pricePaid, f.F(Format.USD, border))
        ws.write(row+5, col, "=%s%s*(%s%s-%s%s)" % (colLetter, row+2+1, colLetter, row+3+1, colLetter, row+4+1), f.F(Format.USD, border))
        ws.write(row+6, col, 0, f.F(Format.USD, border))
        ws.write(row+7, col, lot.acquisitionDate, f.F(Format.Date, border))
        ws.write(row+8, col, lot.czkUsdAtAcquisitionDate(), f.F(Format.CZK_USD, border))
        finalFormat = f.F(Format.Green, Format.CZK, Format.Result, Format.Bottom, border)
        if source == Source.ESPP:
            finalFormat = f.F(Format.Blue, Format.CZK, Format.Result, Format.Bottom, border)
        ws.write(row+9, col, "=%s%s*%s%s" % (colLetter, row+5+1, colLetter, row+8+1), finalFormat)
        col += 1

    range = "B%s:%s%s" % (row+9+1, colLetter, row+9+1)
    if source == Source.ESPP:
        ws.write('B6', "=SUM(%s)" % range, f.F(Format.Blue, Format.CZK))
    else:
        ws.write('B5', "=SUM(%s)" % range, f.F(Format.Green, Format.CZK))

    return row + 11

def DividentsRows(lots, source, ws, f, startingRow):
    row = startingRow
    ws.merge_range("B%s:%s%s" % (row + 0 + 1, chr(ord('A') + len(lots) + 1), row + 0 + 1), _(Source.DIVIDEND.value), f.F(Format.Top, Format.Right, Format.Left, Format.CenterText))
    ws.write(row+1, 0, _("Přepočty měn a zisků"))
    ws.write(row+2, 0, _("Příjem v USD"))
    ws.write(row+3, 0, _("Strženo na US daních"))
    ws.write(row+4, 0, _("Datum"))
    ws.write(row+5, 0, _("Použitý kurz CZK/USD"))
    ws.write(row+6, 0, _("Strženo na US daních (CZK)"))
    ws.write(row+7, 0, _("Příjem v Kč (před US zdaněním)"))

    col = 1
    colLetter = columnName(col)
    for lot in lots:
        border = None
        if col == 1:
            border = Format.Left
        if col == (1 + len(lots) - 1):
            border = Format.LightRight
        colLetter = columnName(col)

        ws.write(row+1, col, _("Stock") + " - " + str(lot.source.value) + " - " + _(lot.acquisitionDate.strftime("%B")), f.F(border))
        ws.write(row+2, col, _((100/85)*(lot.quantity*(lot.priceReal - lot.pricePaid))), f.F(Format.USD, border)) # 15% taxes were already paid upfront
        ws.write(row+3, col, "=%s%s*0.15" % (colLetter, row+2+1), f.F(Format.USD, border))
        ws.write(row+4, col, _(lot.acquisitionDate), f.F(Format.Date, border))
        ws.write(row+5, col, _(lot.czkUsdAtAcquisitionDate()), f.F(Format.CZK_USD, border))
        ws.write(row+6, col, "=%s%s*%s%s" % (colLetter, row+3+1, colLetter, row+5+1), f.F(Format.CZK, border))
        finalFormat = f.F(Format.Yellow, Format.CZK, Format.Result, Format.Bottom, border)
        ws.write(row+7, col, "=%s%s*%s%s" % (colLetter, row+2+1, colLetter, row+5+1), finalFormat)
        col += 1

        ws.write(row+1, col, _("Total"), f.F(Format.Right, Format.Yellow))
        ws.write(row+2, col, "=SUM(B%s:%s%s)" % (row+2+1, colLetter, row+2+1), f.F(Format.USD, Format.Right, Format.Yellow))
        ws.write(row+3, col, "=SUM(B%s:%s%s)" % (row+3+1, colLetter, row+3+1), f.F(Format.USD, Format.Right, Format.Yellow))
        ws.write(row+4, col, "", f.F(Format.Date, Format.Right, Format.Yellow))
        ws.write(row+5, col, "", f.F(Format.CZK_USD, Format.Right, Format.Yellow))
        ws.write(row+6, col, "=SUM(B%s:%s%s)" % (row+6+1, colLetter, row+6+1), f.F(Format.CZK, Format.Right, Format.Yellow))
        finalFormat = f.F(Format.Yellow, Format.CZK, Format.Result, Format.Bottom, Format.Right)
        ws.write(row+7, col, "=SUM(B%s:%s%s)" % (row+7+1, colLetter, row+7+1), finalFormat)

    range = "B%s:%s%s" % (row+7+1, colLetter, row+7+1)
    ws.write('B7', "=SUM(%s)" % (range), f.F(Format.Yellow, Format.CZK))

    return row + 9

class Format(Enum):
    Blue = "blue"
    Green = "green"
    Gray = "gray"
    Yellow = "yellow"
    Orange = "orange"
    Bold = "bold"
    CZK = "czk"
    USD = "usd"
    CZK_USD = "czk_usd"
    Date = "date"
    DoubleBox = "double_box"
    Result = "result"
    Top = "top"
    Left = "left"
    Bottom = "bottom"
    Right = "right"
    LightRight = "light_right"
    CenterText = "centerText"

class FormatLibrary:
    values = {
        Format.Blue: {'pattern': 1, 'bg_color': '#C0C0E0', 'font_color': '#000070'},
        Format.Green: {'pattern': 1, 'bg_color': '#C0E0C0', 'font_color': '#007000'},
        Format.Yellow: {'pattern': 1, 'bg_color': '#FFFF99', 'font_color': '#666600'},
        Format.Orange: {'pattern': 1, 'bg_color': '#FF9922', 'font_color': '#666600'},
        Format.Gray: { "bg_color": "#999999", "pattern": 1,"font_color": "#ffffff" },
        Format.Bold: { 'bold': True },
        Format.CZK: {'num_format': '# ### ##0.00 Kč'},
        Format.USD: {'num_format': '$# ### ##0.00'},
        Format.CZK_USD: {'num_format': '# ### ##0.00'},
        Format.Date: {'num_format': 'yyyy-mm-dd'},
        Format.DoubleBox: {'border': 6},
        Format.Result: {'top': 1},
        Format.Top : {'top' : 2 },
        Format.Left : {'left' : 2 },
        Format.Bottom : {'bottom' : 2 },
        Format.Right : {'right' : 2 },
        Format.LightRight : {'right' : 1 },
        Format.CenterText: { 'align' : 'center' }
    }

    def __init__(self, wb):
        self.wb = wb

    def F(self, *values):
        setup = {}
        for item in values:
            if item == None:
                continue
            if item in FormatLibrary.values:
                setup.update(FormatLibrary.values[item])
            elif isinstance(item, dict):
                setup.update(item)

        return self.wb.add_format(setup)
