from datetime import datetime
import requests
from enum import Enum
import json
import os.path

class Source(Enum):
    ALL = "all"
    AWARD = "Award"
    ESPP = "ESPP"
    DIVIDEND = "Dividend"
    UNKNOWN = "Unknown"

    @staticmethod
    def List():
        return [Source.AWARD, Source.ESPP, Source.DIVIDEND]

class Lot:
    _currentMSFTPrice = None
    _cachedCourses = {}
    _cachedCoursesFile = "./data/courses.cache"
    _cachedStockPrices = None
    _cachedStockPriceFile = "./data/stocks.cache"

    def __init__(self, data):
        self.acquisitionDate = datetime.strptime(data["acquisitionDate"], "%b/%d/%Y")
        self.quantity = float(data["quantity"].replace(",", "."))
        self._czkUsdAtAcquisitionDate = None
        self.source = Source.UNKNOWN
        if "shareSource" in data:
            if data["shareSource"] == "ESPP":
                self.source = Source.ESPP
            elif data["shareSource"] == "DO":
                self.source = Source.AWARD
            else:
                self.source = Source.DIVIDEND
        else:
            fmv = Lot.MSFTPriceAtDate(datetime.strptime(data["acquisitionDate"], "%b/%d/%Y"))*self.quantity
            cost = float(data["costBasis"]["basisAmount"].replace(",", ""))
            ratio = round(cost/fmv, 1)
            if ratio == 0.9:
                self.source = Source.ESPP
            elif self.acquisitionDate.month in [3, 6, 9, 12] and 5 < self.acquisitionDate.day < 25:
                # dividends comes at march, june, september and december, somewhat around middle of the month
                self.source = Source.DIVIDEND
            else:
                # awards are granted at february, may, august and november, last day of month. When there are hollidays at the end of the month, they will come first working day after that
                self.source = Source.AWARD

            # print self.acquisitionDate, self.quantity, ratio, self.source.value

        if self.isESPP():
            self.pricePaid = float(data["costBasis"]["basisAmount"].replace(",", ""))/self.quantity
            self.priceReal = 100 * (self.pricePaid / 90)
        elif self.isAward() or self.isBoughtByDivident():
            self.pricePaid = 0
            self.priceReal = float(data["costBasis"]["basisAmount"].replace(",", ""))/self.quantity

    @staticmethod
    def Headers():
        return ["type", "acquisitionDate", "pricePaid", "priceReal", "quantity", "source", "czkUsdAtAcquisitionDate"]

    @staticmethod
    def CZK_price_at_date(date, otherCurrency="USD"):
        strDate = date.strftime("%d.%m.%Y")
        if not Lot._cachedCourses:
            if os.path.isfile(Lot._cachedCoursesFile):
                with open(Lot._cachedCoursesFile) as file:
                    Lot._cachedCourses = json.loads(file.read())

        if strDate not in Lot._cachedCourses:
            url = "http://www.cnb.cz/cs/financni_trhy/devizovy_trh/kurzy_devizoveho_trhu/denni_kurz.txt?date=%s" % strDate
            courses = requests.get(url)

            for dayCourse in courses.text.split('\n'):
                fields = dayCourse.split('|')
                if len(fields) < 5:
                    continue
                if (fields[3] == otherCurrency):
                    Lot._cachedCourses[strDate] = float(fields[4].replace(",","."))

        if strDate in Lot._cachedCourses:
            return Lot._cachedCourses[strDate]

        raise Exception("Currency %s not found in %s" % (otherCurrency, url))

    @staticmethod
    def SaveCoursesCache():
        with open(Lot._cachedCoursesFile, "w") as file:
            file.write(json.dumps(Lot._cachedCourses))

    @staticmethod
    def CurrentMSFTPrice():
        if Lot._currentMSFTPrice == None:
            lastDate = sorted(Lot.MSFTPrices().keys())[-1]
            Lot._currentMSFTPrice = float(Lot.MSFTPrices()[lastDate])
        return Lot._currentMSFTPrice

    @staticmethod
    def MSFTPriceAtDate(date):
        return Lot.MSFTPrices()[date.strftime("%Y-%m-%d")]

    @staticmethod
    def MSFTPrices():
        if not Lot._cachedStockPrices:
            if not os.path.isfile(Lot._cachedStockPriceFile):
                url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&outputsize=full&apikey=W3RCAR8GFCZPPJI6"
                stockData = json.loads(requests.get(url).content)
                with open(Lot._cachedStockPriceFile, "w") as file:
                    values = dict([(key, float(stockData["Time Series (Daily)"][key]["4. close"])) for key in stockData["Time Series (Daily)"]])
                    file.write(json.dumps(values))
                    Lot._cachedStockPrices = values
            else:
                with open(Lot._cachedStockPriceFile, "r") as file:
                    Lot._cachedStockPrices = json.loads(file.read())
        return Lot._cachedStockPrices


    def TaxesIfSold(self, sellingPrice, sellingCZKCourse, sellingDate, minimalYearsToAvoidTaxes, tax):
        yougestFreesellersDate = sellingDate.replace(year = sellingDate.year - minimalYearsToAvoidTaxes)
        if self.acquisitionDate < yougestFreesellersDate:
            return 0
        return tax*self.quantity*(sellingPrice*sellingCZKCourse - self.priceReal*self.czkUsdAtAcquisitionDate())


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
        return self._csv("open")

    def _csv(self, type):
        fields = [
            type,
            self.acquisitionDate.date().isoformat(),
            str(self.pricePaid),
            str(self.priceReal),
            str(self.quantity) ,
            self.source.value,
            str(self.czkUsdAtAcquisitionDate())
        ]

        return ";".join(fields)

class ClosedLot(Lot):
    def __init__(self, data):
        Lot.__init__(self, data)
        self.sellDate = datetime.strptime(data["holdingPeriodDate"], "%b/%d/%Y")
        self.sellPrice = float(data["proceeds"]["proceeds"].replace(",", ""))/self.quantity
        self._czkUsdAtSellDate = None

    def czkUsdAtSellDate(self):
        if self._czkUsdAtSellDate == None:
            self._czkUsdAtSellDate = Lot.CZK_price_at_date(self.sellDate, "USD")
        return self._czkUsdAtSellDate

    def TaxApplicable(self):
        return (self.acquisitionDate >= self.sellDate.replace(year = self.sellDate.year - 3))

    def csv(self):
        return self._csv("closed")

class Lots:
    def __init__(self, data, closed=False):
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], Lot):
            self.lots = data
        elif closed:
            self.lots = [ClosedLot(row) for row in data]
        else:
            self.lots = [Lot(row) for row in data]

    def BoughtInYear(self, year):
        return Lots([lot for lot in self.lots if lot.acquisitionDate.year == year])

    def FilterBySource(self, source):
        return Lots([lot for lot in self.lots if lot.isFromSource(source)])

    def TaxesIfSold(self, sellingPrice, sellingDate, minimalYearsToAvoidTaxes, tax, czkCourse, additionalStocks=0):
        totalTaxes = (additionalStocks*sellingPrice - additionalStocks*Lot.CurrentMSFTPrice())*tax*czkCourse
        totalTotal = additionalStocks*sellingPrice * czkCourse
        totalAcquisitionPrice = additionalStocks*Lot.CurrentMSFTPrice()*czkCourse
        quantity = additionalStocks
        avgBuyPrice = 0
        print("%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
            "{:10s}".format("Acq. date"),
            "{:10s}".format("Quantity (pcs)"),
            "{:20s}".format("Selling price (czk)"),
            "{:20s}".format("Buy/sell diff (czk)"),
            "{:13s}".format("Taxes (czk)"),
            "{:30s}".format("Income after taxation (czk)"),
            "{:20s}".format("Buy/Sell"),
        ))
        if additionalStocks > 0:
            print("%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
                "{:10s}".format("N/A"),
                "{:10.0f}".format(quantity),
                "{:17.2f}".format(totalTotal),
                "{:17.2f}".format(totalTotal - totalAcquisitionPrice),
                "{:10.2f}".format(totalTaxes),
                "{:27.2f}".format((totalTotal-totalTaxes)),
                "{:7.2f}/{:.2f}".format(sellingPrice, sellingPrice),
            ))
            avgBuyPrice = sellingPrice
        for lot in self.lots:
            total = lot.quantity * sellingPrice * czkCourse
            taxes = lot.TaxesIfSold(sellingPrice, czkCourse, sellingDate, minimalYearsToAvoidTaxes, tax)
            acquisition = lot.quantity * lot.priceReal * lot.czkUsdAtAcquisitionDate()
            print("%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
                "{:10s}".format(lot.acquisitionDate.strftime("%Y-%m-%d")),
                "{:10.0f}".format(lot.quantity),
                "{:17.2f}".format(total),
                "{:17.2f}".format(total - acquisition),
                "{:10.2f}".format(taxes),
                "{:27.2f}".format((total-taxes)),
                "{:7.2f}/{:.2f}".format(lot.priceReal, sellingPrice),
            ))

            avgBuyPrice = ((avgBuyPrice*quantity) + (lot.priceReal*lot.quantity))/(quantity+lot.quantity)

            totalTotal += total
            totalTaxes += taxes
            totalAcquisitionPrice += acquisition
            quantity += lot.quantity
        print()
        print("%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
            "{:10s}".format("-"),
            "{:10.0f}".format(quantity),
            "{:17.2f}".format(totalTotal),
            "{:17.2f}".format(totalTotal - totalAcquisitionPrice),
            "{:10.2f}".format(totalTaxes),
            "{:27.2f}".format((totalTotal-totalTaxes)),
            "{:7.2f}/{:.2f}".format(avgBuyPrice, sellingPrice),
        ))

    def csv(self):
        out = []
        out.append(";".join(Lot.Headers()))
        for lot in self.lots:
            out.append(lot.csv())
        return out

class ClosedLots(Lots):
    def __init__(self, data):
        Lots.__init__(self, data, True)

    def SoldInYear(self, year):
        return ClosedLots([lot for lot in self.lots if lot.sellDate.year == year])
