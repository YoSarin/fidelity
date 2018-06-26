import requests
from lib.lots import Lots, ClosedLots
import json

def fetchData(username, password, accountID, securityID):
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
            })
        closedLotsRaw = s.post(
            "https://netbenefitsww.fidelity.com/mybenefitsww/stockplans/api/account/%s//closedLots" % accountID,
            data={
                "currencyFormat":"USD_FORMAT",
                "URI":"CLOSED_LOTS",
                "securityID": securityID,
                "symbol": "MSFT",
                "securityDescription": "MICROSOFT+CORP"
            })

        openLots = Lots((json.loads(openLotsRaw.content))["data"]["openLotsRecords"])
        closedLots = ClosedLots((json.loads(closedLotsRaw.content))["data"]["closedLotsRecords"])

        return (openLots, closedLots)
