import requests
from lib.lots import Lots, ClosedLots
import json
import os.path

openLotsFileName = "data/open_lots.json"
closedLotsFileName = "data/closed_lots.json"

def fetchData():
    openData = closedData = None
    with open(openLotsFileName, "r") as file: 
        openData = Lots(json.load(file)["openLots"])
        
    with open(closedLotsFileName, "r") as file: 
        closedData = ClosedLots(json.load(file)["data"]["closedLotsRecords"])

    return (openData, closedData)

def reloadCacheFromFidelity(username, password, accountID, securityID):
    with requests.Session() as s:
        hp = s.get("https://nb.fidelity.com/public/nb/worldwide/home")
        loginInit = s.get("https://login.fidelity.com/ftgw/Fas/Fidelity/PWI/Login/Init/dj.chf.ra")

        login = s.post(
            "https://login.fidelity.com/ftgw/Fas/Fidelity/PWI/Login/Response/dj.chf.ra/",
            data={"username": username, "password": password, "SavedIdInd": "N"},
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            }
        )

        if login.status_code != 200:
            print("Login failed!") 
            return False

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

        # basic sanity check, that we have json data
        openData = (json.loads(openLotsRaw))
        with open(openLotsFileName, "w") as file:
            file.write(openLotsRaw)

        # basic sanity check, that we have json data
        closedData = (json.loads(closedLotsRaw))
        with open(closedLotsFileName, "w") as file:
            file.write(closedLotsRaw)
