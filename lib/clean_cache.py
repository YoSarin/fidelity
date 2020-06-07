from lots import *
from datetime import datetime

def cleanCache(force = False):
    cacheFiles = [Lot._cachedCoursesFile, Lot._cachedStockPriceFile]
    now = datetime.now()
    for filename in cacheFiles:
        if (not os.path.exists(filename)):
            continue
        modificationTime = datetime.fromtimestamp(os.path.getmtime(filename))
        age = (now - modificationTime)
        if force or age.days > 1:
            os.remove(filename)
