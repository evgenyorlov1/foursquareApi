from twisted.web.client import Agent
from twisted.internet import reactor, defer
from twisted.internet.protocol import Protocol
from twisted.internet.defer import Deferred


import sys
import csv
import urllib
import json
import os
import urllib2


client_id = "3BC4S3TVG0WAPTERYZ5WJ1Q35ME1GZR13XXFVOQN5CXNJXIJ"
client_secret = "XM4RDX4LVNK3TUOKXS1SAOPHND44FH3HRPYVQLGXIJNVKFK4"
url = "https://api.foursquare.com/v2/venues/search?"
version = 20150101
head_row = ['klsg_category', 'klsg_id', 'klsg_name',
            'fsq_id', 'fsq_name', 'fsq_address', 'fsq_latitude',
            'fsq_longitude', 'distance', 'fsq_category',
            'checkins_count', 'users_count']
category_mapping_file = 'category_mapping.csv' #file with categories
category_mapping = {}

MAXCALLS = 5000
lines = 0
progress = 0


class ResourcePrinter(Protocol):
    def __init__(self, finished, row):
        self.finished = finished
        self.row = row
    def dataReceived(self, data):
        res = []
        data = json.loads(data)
        if (len(data['response']['venues']) == 0):
            res.append(str(self.row[0])) #klsg_category
            res.append(str(self.row[1])) #klsg_id
            res.append(str(self.row[2]))
            res.append('none') #fsq_i
            res.append('') #fsq_name
            res.append('') #fsq_address
            res.append('') #fsq_long,
            res.append('') #fsq_lat
            res.append('') #fsq_distance
            res.append('') #fsq_category
            res.append('') #fsq_checkins_count
            res.append('') #fsq_users_count
            output(res)
        else:
            res.append(str(self.row[0])) #klsg_category   can't be taken from response
            res.append(str(self.row[1])) #klsg_id     can't be taken from response
            res.append(str(self.row[2])) #klsg_id     can't be taken from response
            res.append(data['response']['venues'][0]['id']) #fsq_i
            res.append(data['response']['venues'][0]['name']) #fsq_name
            try:
                res.append(data['response']['venues'][0]['location']['address']) #fsq_address
            except:
                res.append('') #sometimes foursquare returns no address
            res.append(data['response']['venues'][0]['location']['lng']) #fsq_long
            res.append(data['response']['venues'][0]['location']['lat']) #fsq_lat
            res.append(data['response']['venues'][0]['location']['distance']) #fsq_distance
            res.append(data['response']['venues'][0]['categories'][0]['name']) #fsq_category
            res.append(data['response']['venues'][0]['stats']['checkinsCount']) #fsq_checkins_count
            res.append(data['response']['venues'][0]['stats']['usersCount']) #fsq_users_count
            output(res)
    def connectionLost(self, reason):
        self.finished.callback(None)


def main():
    rows = input()
    deferred_calls = [foursquareApi(row) for row in list(rows)]
    d = defer.gatherResults(deferred_calls, consumeErrors=True)
    d.addCallback(Succeed)
    d.addErrback(Faild)
    d.addBoth(Shutdown)

    reactor.run()


def Faild(ignored):
    print "Faild to execute request"


def Succeed(ignored):
    pass


def Shutdown(ignored):
    reactor.stop()


def Response(data, row):
    finished = Deferred()
    data.deliverBody(ResourcePrinter(finished, row))
    return finished


def in_category_mapping(category):
    #checks if input category is in category_mapping
    global category_mapping
    if category in category_mapping:
        return True
    else:
        return False


def input():
    global lines, category_mapping_file, category_mapping
    try:
        with open(sys.argv[1], 'r') as data:
            reader = csv.reader(data)
            next(reader, None)
            for row in reader:
                lines += 1
                yield row
    except Exception:
        print "Reading error", sys.exc_info()

    try:
        with open(category_mapping_file, 'r') as data:
            reader = csv.reader(data, delimiter=';')
            next(reader, None)
            for row in reader:
                a = row[0]
                b = row[1]
                category_mapping.update(a = b)
    except Exception:
        print "Can't load " + category_mapping_file, sys.exc_info()

def foursquareApi(row):
    global version, client_id, client_secret, url, MAXCALLS
    MAXCALLS -= 1
    if(MAXCALLS > 0):
        entry = in_category_mapping(row[0])
        ll = ",".join([str(row[3]), str(row[4])])
        query = str(row[2])
        if(entry):
            #there is entry
            categoryId = category_mapping[row[0]] #take from mapping
            params = urllib.urlencode({"v": version,"client_id": client_id, "limit": 1,
                "client_secret": client_secret, "ll": ll, "query": query, "categoryId": categoryId,
                "intent": "checkin"})
        else:
            #there is NOT entry
            params = urllib.urlencode({"v": version,"client_id": client_id, "limit": 1,
                "client_secret": client_secret, "ll": ll, "query": query,
                    "intent": "match"})
        agent = Agent(reactor)
        request = agent.request('GET', url + params)
        request.addCallback(Response, row)
        request.addErrback(Faild)
    else:
        sys.exit(0)
    return request


def output(res):
    if(os.path.isfile(sys.argv[2])):
        #if file exists, just append to it
        try:
            with open(sys.argv[2], 'a') as outputFile:
                wr = csv.writer(outputFile, delimiter = ';', quoting = csv.QUOTE_ALL) #csv.QUOTE_ALL because switched to ; separator and files have '.
                wr.writerow(res)
        except Exception:
            print "output error", sys.exc_info()
    else:
        #if file doesn't exists, create it, add header and output
        try:
            with open(sys.argv[2], 'w') as outputFile:
                wr = csv.writer(outputFile, delimiter = ';', quoting = csv.QUOTE_ALL) #csv.QUOTE_ALL because switched to ; separator and files have '.
                wr.writerow(head_row)
                wr.writerow(res)
        except Exception:
            print "output error", sys.exc_info()


if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf8')
    main()
