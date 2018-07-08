from datetime import datetime
import requests
from enum import Enum
import json

class Source(Enum):
    ALL = "all"
    AWARD = "Award"
    ESPP = "ESPP"
    DIVIDEND = "Dividend"

    @staticmethod
    def List():
        return [Source.AWARD, Source.ESPP, Source.DIVIDEND]

class Lot:
    def __init__(self, data):
        self.acquisitionDate = datetime.strptime(data["acquisitionDate"], "%b/%d/%Y")
        self.quantity = float(data["quantity"].replace(",", "."))
        self._czkUsdAtAcquisitionDate = None
        if "shareSource" in data:
            if data["shareSource"] == "ESPP":
                self.source = Source.ESPP
            elif data["shareSource"] == "DO":
                self.source = Source.AWARD
            else:
                self.source = Source.DIVIDEND

        if self.isESPP():
            self.pricePaid = float(data["costBasisShare"]["basisPerShare"].replace(",", "."))
            self.priceReal = 100 * (self.pricePaid / 90)
        elif self.isAward() or self.isBoughtByDivident():
            self.pricePaid = 0
            self.priceReal = float(data["costBasisShare"]["basisPerShare"].replace(",", "."))

    @staticmethod
    def Headers():
        return ["acquisitionDate", "pricePaid", "priceReal", "quantity", "source", "czkUsdAtAcquisitionDate"]

    @staticmethod
    def CZK_price_at_date(date, otherCurrency="USD"):
        url = "http://www.cnb.cz/cs/financni_trhy/devizovy_trh/kurzy_devizoveho_trhu/denni_kurz.txt?date=%s" % date.strftime("%d.%m.%Y")
        courses = requests.get(url)

        for dayCourse in courses.content.split("\n"):
            fields = dayCourse.split('|')
            if len(fields) < 5:
                continue
            if (fields[3] == otherCurrency):
                return float(fields[4].replace(",","."))

        raise Exception("Currency %s not found in %s" % (otherCurrency, url))

    @staticmethod
    def CurrentMSFTPrice():
        url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&apikey=W3RCAR8GFCZPPJI6"
        stockData = json.loads(requests.get(url).content)
        lastDate = sorted(stockData["Time Series (Daily)"].keys())[-1]
        return float(stockData["Time Series (Daily)"][lastDate]["4. close"])

    def TaxesIfSold(self, sellingPrice, sellingDate, minimalYearsToAvoidTaxes, tax):
        yougestFreesellersDate = sellingDate.replace(year = sellingDate.year - minimalYearsToAvoidTaxes)
        if self.acquisitionDate < yougestFreesellersDate:
            return 0
        return tax*(sellingPrice - self.priceReal)


    def czkUsdAtAcquisitionDate(self):
        if self._czkUsdAtAcquisitionDate == None:
            self._czkUsdAtAcquisitionDate = Lot.CZK_price_at_date(self.acquisitionDate, "USD")
        return self._czkUsdAtAcquisitionDate

    def isESPP(self):
        return self.isFromSource(Source.ESPP)

    def isAward(self):
        return self.isFromSource(Source.AWARD)

    def isBoughtByDivident(self):
        return self.isFromSource(Source.DIVIDEND)

    def isFromSource(self, source):
        if source == Source.ALL:
            return True
        elif source == self.source:
            return True
        return False

    def csv(self):
        fields = [
            self.acquisitionDate.date().isoformat(),
            str(self.pricePaid),
            str(self.priceReal),
            str(self.quantity) ,
            self.source,
            str(self.czkUsdAtAcquisitionDate())
        ]

        return ";".join(fields)

class ClosedLot(Lot):
    def __init__(self, data):
        Lot.__init__(self, data)

class Lots:
    def __init__(self, data, closed=False):
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], Lot):
            self.lots = data
        elif closed:
            self.lots = [ClosedLot(row) for row in data]
        else:
            self.lots = [Lot(row) for row in data]

    def FilterByYear(self, year):
        return Lots([lot for lot in self.lots if lot.acquisitionDate.year == year])

    def FilterBySource(self, source):
        return Lots([lot for lot in self.lots if lot.isFromSource(source)])

    def TaxesIfSold(self, sellingPrice, sellingDate, minimalYearsToAvoidTaxes, tax, czkCourse, additionalStocks=0):
        totalTaxes = (additionalStocks*sellingPrice - additionalStocks*Lot.CurrentMSFTPrice())*tax
        totalTotal = additionalStocks*sellingPrice
        quantity = additionalStocks
        print "%s\t%s\t%s\t%s" % (
            "{:10s}".format("Quantity (pcs)"),
            "{:20s}".format("Selling price (czk)"),
            "{:13s}".format("Taxes (czk)"),
            "{:22s}".format("Gain after sell (czk)"),
        )
        if additionalStocks > 0:
            print "%s\t%s\t%s\t%s" % (
                "{:10.0f}".format(quantity),
                "{:17.2f}".format(totalTotal*czkCourse),
                "{:10.2f}".format(totalTaxes*czkCourse),
                "{:19.2f}".format((totalTotal-totalTaxes)*czkCourse),
            )
        for lot in self.lots:
            total = lot.quantity * sellingPrice
            taxes = lot.TaxesIfSold(sellingPrice, sellingDate, minimalYearsToAvoidTaxes, tax)
            print "%s\t%s\t%s\t%s" % (
                "{:10.0f}".format(lot.quantity),
                "{:17.2f}".format(total*czkCourse),
                "{:10.2f}".format(taxes*czkCourse),
                "{:19.2f}".format((total-taxes)*czkCourse),
            )
            totalTotal += total
            totalTaxes += taxes
            quantity += lot.quantity
        print
        print "%s\t%s\t%s\t%s" % (
            "{:10.0f}".format(quantity),
            "{:17.2f}".format(totalTotal*czkCourse),
            "{:10.2f}".format(totalTaxes*czkCourse),
            "{:19.2f}".format((totalTotal-totalTaxes)*czkCourse),
        )

    def csv(self):
        out = []
        out.append(";".join(Lot.Headers()))
        for lot in self.lots:
            out.append(lot.csv())
        return out

class ClosedLots(Lots):
    def __init__(self, data):
        Lots.__init__(self, data, True)
