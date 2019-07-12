import urllib.request
from bs4 import BeautifulSoup
import csv


def getReply(ticker):
    prefix = 'http://www.sec.gov/cgi-bin/browse-edgar?CIK='
    suffix = '&Find=Search&owner=exclude&action=getcompany'
    ticker_lengths = [1, 2, 3, 4, 5, 10]

    if len(ticker) not in ticker_lengths:
        raise ValueError("Invalid Ticker Length")
    else:
        soup = BeautifulSoup(urllib.request.urlopen(prefix + ticker + suffix).read().decode(), 'html.parser')

        table = soup.find_all('table')[2]

        #Stores all the 13F forms links on the page
        links = []

        for rows in table.find_all('tr'):
            cells = rows.find_all('td')
            if len(cells) > 0 and cells[0].get_text().split('-')[0] == '13F':
                links.append(cells[1].find('a')['href'].split('-index.htm')[0] + '.txt')

        if len(links) == 0:
            raise ValueError("No 13F forms available")
        else:
            #returns most recent link and CIK
            return links[0], ticker

def parseXML(link):
    values = []

    baseURL = 'https://www.sec.gov'
    response = urllib.request.urlopen(baseURL + link[0]).read().decode('utf-8')

    xml = BeautifulSoup(response, 'xml')

    report = xml.find('formData').find('reportType').string

    if xml.find('informationTable') == None:
        for data in xml.find('formData').find('signatureBlock'):
            if data != '\n':
                values.append(data.string)
    else:
        for infotable in xml.find('informationTable').find_all('infoTable'):
            infotable = infotable.find_all(string=True)
            infotable = [info for info in infotable if info != '\n']
            values.append(infotable)

    return values, report, link[1]


def createTSV(XML):
    if isinstance(XML[0], list):
        columnsHR = ['nameOfIssuer', 'titleOfClass', 'cusip', 'value', 'sshPrnamt', 'sshPrnamtType', 'investmentDiscretion', 'Sole', 'Shared', 'None']
        columnsCR =['nameOfIssuer', 'titleOfClass', 'cusip', 'value', 'sshPrnamt', 'sshPrnamtType', 'investmentDiscretion', 'otherManager', 'Sole', 'Shared', 'None']
        columnsNT = ['name', 'title', 'signature', 'city', 'stateOrCountry', 'signatureDate']

        with open(XML[2]+'.tsv', 'w') as tsvfile:
            writer = csv.writer(tsvfile, delimiter='\t')
            if XML[1] == '13F NOTICE':
                writer.writerow(columnsNT)
                writer.writerow(XML[0])
            if XML[1] == '13F HOLDINGS REPORT':
                writer.writerow(columnsHR)
                for value in XML[0]:
                    writer.writerow(value)
            if XML[1] == '13F COMBINATION REPORT':
                writer.writerow(columnsCR)
                for value in XML[0]:
                    writer.writerow(value)
        return
    else:
        raise ValueError("No XML to write to file")

print("Testing 13F-HR")
createTSV(parseXML(getReply('0001166559')))

print("Testing 13F-HR Combination Report")
createTSV(parseXML(getReply('0001163648')))

print("Testing 13F-NT")
createTSV(parseXML(getReply('0001728584')))

#Error handling tests
# print("Testing invalid ticker length")
# createTSV(parseXML(getReply('0001148')))
#
# print("Testing ticker with no 13F forms")
# createTSV(parseXML(getReply('0000874235')))
