import urllib2
import json
import threading
import time
import csv
import re
from threading import Event, Thread

def call_repeatedly(interval, func, *args):
    stopped = Event()
    def loop():
        while not stopped.wait(interval): # the first call is in `interval` secs
            func(*args)
    Thread(target=loop).start()    
    return stopped.set

class HLOC(object):
    def __init__(self, h = 0, l= 0, o = 0, c = 0, v = 0, t = ''):
        self.h = h
        self.l = l
        self.o = o
        self.c = c
        self.v = v
        self.t = t

    def __repr__(self):
        return 'HLOC(%.1f, %.1f, %.1f, %.1f, %d, %s)' % (self.h, self.l, self.o, self.c, self.v, self.t)

def loadMainContracts():
    f = urllib2.urlopen('http://data.eastmoney.com/futures/js/FData.js')
    strdata = f.read()
    newContract = re.compile(r"newContract: '\w*'")
    strcontracts = re.findall(newContract, strdata)
    return [strc[14: len(strc) - 1] for strc in strcontracts]

def parseData(hlocs, contract):
    #print('parseData ...')
    if len(hlocs) < 2:
        #print('not enough hlocs')
        return

    last = hlocs[-1]
    lastbutone = hlocs[-2]

    volumelast = last.v
    volumelastbutone = float(lastbutone.v)

    if volumelast <= 0 or volumelastbutone <= 0:
        return

    closelast = last.c
    closelastbutone = lastbutone.c

    volumerate = volumelast / volumelastbutone
    closerate = abs(closelast - closelastbutone) / closelastbutone
    
    if volumerate > 2 or closerate > 0.004:
        print('heavy volume %5.1f close rate %.3f time %s contract %s' % (volumerate, closerate, last.t, contract))

def loadData(contract):
    #print('loadData ... ', contract)
    f = urllib2.urlopen('http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesMinLine?symbol=' + contract)
    #f = urllib2.urlopen('http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesMinLine5d?symbol=' + contract)
    strdata = f.read()
    hlocs = None
    try:
        hlocs = json.loads(strdata)
    except:
        print('json error ', contract)
        print('strdata ', strdata)
        pass


    if hlocs == None:
        #print 'hlocs is none'
        return None

    def in_trading_time(hloc):
        if len(hloc) < 4:
            return False
        t = hloc[4]
        ts = t.split(':')
        h = int(ts[0])
        m = int(ts[1])
        if h == 10 and (15 <= m and m <= 29):
            return False
        if h == 11 and m == 30:
            return False
        if h == 15 and m == 0:
            return False
        if 15 <= h and h <= 20:
            return False
        return True

    #print('len of hlocs ', len(hlocs))
    hlocs = filter(in_trading_time, hlocs)
    #print('len of hlocs ', len(hlocs))

    hlocs = [HLOC(float(hloc[0]), float(hloc[0]), float(hloc[0]), float(hloc[0]), int(hloc[2]), hloc[4]) for hloc in hlocs]
    return hlocs

def convert(hlocs):
    #print len(hlocs)
    h, l, o, c, v = 0, 0, 0, 0, 0
    prices = [hloc.c for hloc in hlocs]
    volume = [hloc.v for hloc in hlocs]
    h = max(prices)
    l = min(prices)
    o = prices[0]
    c = prices[-1]
    v = sum(volume)
    return HLOC(h, l, o, c, v, hlocs[0].t)

def convert1minto15min(hlocs):
    index = len(hlocs) / 15
    if len(hlocs) % 15 > 0:
        index += 1

    return [convert(hlocs[i * 15:(i + 1) * 15]) for i in range(index)]

def test_convert1minto15min():
    hlocs = loadData('BU1606')
    print convert1minto15min(hlocs)

def parseHistoryData(contracts):
    #contracts = ['l1605']
    for c in contracts:
        #print 'parse ' + c
        hlocs = loadData(c)
        if hlocs is None:
            continue
        hlocs = convert1minto15min(hlocs)
        #print hlocs
        for i in range(len(hlocs)):
            parseData(hlocs[0:i], c)

def onTimer(contracts):
    #contracts = ['l1605']
    print '---------------' + time.ctime()
    for c in contracts:
        #print 'parse ' + c
        hlocs = loadData(c)
        if hlocs is None:
            continue
        hlocs = convert1minto15min(hlocs)
        parseData(hlocs, c)

def saveCSV(contracts):
    for c in contracts:
        hlocs = loadData(c)
        if hlocs == None:
            continue
        hlocs = convert1minto15min(hlocs)
        
        with open(c + '.csv', 'wb') as f:
            f.write('Date,Open,High,Low,Close,Volume,OpenInterest\r\n')
            for hloc in hlocs:
                if hloc.v > 0:
                    f.write('2016-2-1,%s:00,%.1f,%.1f,%.1f,%.1f,%d,0\r\n' % (hloc.t, hloc.o, hloc.h, hloc.l, hloc.c, hloc.v))

contracts = loadMainContracts()
#saveCSV(contracts)
call_repeatedly(60, onTimer, contracts)
onTimer(contracts)
#test_convert1minto15min()
#parseHistoryData(contracts)
