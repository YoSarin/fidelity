import requests
from lib.lots import Lots, ClosedLots
import json
import os.path

def fetchData(username, password, accountID, securityID):
    cachedFileName = "./fidelity.cache"
    openData = None
    closedData = None
    if os.path.isfile(cachedFileName):
        with open(cachedFileName) as file:
            data = json.loads(file.read())
            openData = data["openLots"]
            closedData = data["closedLots"]
    else:
        with requests.Session() as s:
            hp = s.get("https://nb.fidelity.com/public/nb/worldwide/home")
            login = s.post(
                "https://login.fidelity.com/ftgw/Fas/Fidelity/PWI/Login/Response/dj.chf.ra/",
                data={"username": username, "password": password}
            )
            openLotsRaw = s.post(
                "https://netbenefitsww.fidelity.com/mybenefitsww/stockplans/api/account/%s//openLots" % accountID,
                data={
                    "currencyFormat":"USD_FORMAT",
                    "URI":"OPEN_LOTS",
                    "securityID": securityID,
                    "symbol": "MSFT",
                    "securityDescription": "MICROSOFT+CORP"
                }).content
            closedLotsRaw = s.post(
                "https://netbenefitsww.fidelity.com/mybenefitsww/stockplans/api/account/%s//closedLots" % accountID,
                data={
                    "currencyFormat":"USD_FORMAT",
                    "URI":"CLOSED_LOTS",
                    "securityID": securityID,
                    "symbol": "MSFT",
                    "securityDescription": "MICROSOFT+CORP"
                }).content

            openData = (json.loads(openLotsRaw))["data"]["openLotsRecords"]
            closedData = (json.loads(openLotsRaw))["data"]["openLotsRecords"]

            data = {"openLots":openData, "closedLots":closedData}
            with open(cachedFileName, "w") as file:
                file.write(json.dumps(data))

    openLots = Lots(openData)
    closedLots = ClosedLots(closedData)

    return (openLots, closedLots)
