#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xlsxwriter
from translator import _, setLang
from lots import Source
from enum import Enum

def CreateXLS(opened, closed, filename, grossIncome, totalPremium):
    setLang('cs_cz')
    wb = xlsxwriter.Workbook(filename + '.xlsx')
    ws = wb.add_worksheet()

    f = FormatLibrary(wb)

    ws.set_column('A:A', 45)
    ws.set_column('B:Z', 25)

    # formats

    # table == Employee income ==
    ws.write('A1', _('Employee income'))

    ws.write('A3', _("Source"))
    ws.write('A4', _("Wage (Skype Czech Republic)"))
    ws.write('A5', _("Stock awards (bonuses - shares)"))
    ws.write('A6', _("ESPP (preferential purchase of employee shares)"))
    ws.write('A7', _("Total"), f.F(Format.Result))

    ws.write('B3', _('Gross income'))
    ws.write('B4', grossIncome, f.F(Format.CZK))
    ws.write('B5', "TODO:Count awards sum", f.F(Format.Green, Format.CZK))
    ws.write('B6', "TODO:Count ESPP sum", f.F(Format.Blue, Format.CZK))
    ws.write('B7', "=SUM(B4:B6)", f.F(Format.Result, Format.CZK))

    ws.write('C3', _('Total premiums written'))
    ws.write('C4', totalPremium, f.F(Format.CZK))
    ws.write('C5', 0, f.F(Format.Green, Format.CZK))
    ws.write('C6', 0, f.F(Format.Blue, Format.CZK))
    ws.write('C7', "=SUM(C4:C6)",  f.F(Format.Result, Format.CZK))

    ws.write('D3', _('Total'))
    ws.write('D4', '=SUM(B4:C4)', f.F(Format.CZK))
    ws.write('D5', '=SUM(B5:C5)', f.F(Format.Green, Format.CZK))
    ws.write('D6', '=SUM(B6:C6)', f.F(Format.Blue, Format.CZK))
    ws.write('D7', "=SUM(D4:D6)",  f.F(Format.Gray, Format.Result, Format.DoubleBox, Format.CZK, Format.Bold))

    row = 9
    for source in Source.List():
        if source == Source.DIVIDEND:
            continue
        lots = opened.FilterBySource(source).lots
        ws.merge_range("B%s:%s%s" % (row + 0 + 1, chr(ord('A') + len(lots)), row + 0 + 1), _(source), f.F(Format.Top, Format.Right, Format.Left, Format.CenterText))
        ws.write(row+1, 0, _(u"Přepočty měn a zisků"))
        ws.write(row+2, 0, _(u"Počet akcií"))
        ws.write(row+3, 0, _(u"Obchodní cena akcie (USD)"))
        ws.write(row+4, 0, _(u"Nákupní cena akcie (USD)"))
        ws.write(row+5, 0, _(u"Příjem v USD"))
        ws.write(row+6, 0, _(u"Strženo na US daních"))
        ws.write(row+7, 0, _(u"Datum"))
        ws.write(row+8, 0, _(u"Použitý kurz CZK/USD"))
        ws.write(row+9, 0, _(u"Příjem v Kč"))
        col = 1
        colLetter = chr(ord('A') + col)
        for lot in reversed(lots):
            border = None
            if col == 1:
                border = Format.Left
            elif col == (1 + len(lots) - 1):
                border = Format.Right
            colLetter = chr(ord('A') + col)

            ws.write(row+1, col, _("Stock") + " - " + str(lot.source) + " - " + _(lot.acquisitionDate.strftime("%B")), f.F(border))
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

        row += 11

    dividentsInMonths = ["March", "June", "September", "December"]
    ws.merge_range("B%s:%s%s" % (row + 0 + 1, chr(ord('A') + len(dividentsInMonths) + 1), row + 0 + 1), _(Source.DIVIDEND), f.F(Format.Top, Format.Right, Format.Left, Format.CenterText))
    ws.write(row+1, 0, _(u"Přepočty měn a zisků"))
    ws.write(row+2, 0, _(u"Příjem v USD"))
    ws.write(row+3, 0, _(u"Strženo na US daních"))
    ws.write(row+4, 0, _(u"Datum"))
    ws.write(row+5, 0, _(u"Použitý kurz CZK/USD"))
    ws.write(row+6, 0, _(u"Strženo na US daních (CZK)"))
    ws.write(row+7, 0, _(u"Příjem v Kč (před US zdaněním)"))

    col = 1
    for month in dividentsInMonths:
        border = None
        if col == 1:
            border = Format.Left
        if col == (1 + len(dividentsInMonths) - 1):
            border = Format.LightRight
        colLetter = chr(ord('A') + col)

        ws.write(row+1, col, _(Source.DIVIDEND) + " - " + _(month), f.F(border))
        ws.write(row+2, col, _("FILL IN"), f.F(Format.USD, border))
        ws.write(row+3, col, _("FILL IN"), f.F(Format.USD, border))
        ws.write(row+4, col, _("FILL IN"), f.F(Format.Date, border))
        ws.write(row+5, col, _("FILL IN"), f.F(Format.CZK_USD, border))
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

    wb.close()

class Format(Enum):
    Blue = "blue"
    Green = "green"
    Gray = "gray"
    Yellow = "yellow"
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
        Format.Gray: { "bg_color": "#999999", "pattern": 1,"font_color": "#ffffff" },
        Format.Bold: { 'bold': True },
        Format.CZK: {'num_format': u'# ### ##0.00 Kč'},
        Format.USD: {'num_format': u'$# ### ##0.00'},
        Format.CZK_USD: {'num_format': u'# ### ##0.00'},
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
