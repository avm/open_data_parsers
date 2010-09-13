from BeautifulSoup import BeautifulSoup as bs
import urllib2
import simplejson as json
import logging
logging.basicConfig(level=logging.INFO)

baseUrl = 'http://www.gost.ru/wps/portal/pages.TechCom'
portalBase = 'http://webportalsrv.gost.ru'
output = 'committees.json'

def get_url(url):
    u = urllib2.urlopen(url)
    body = u.read()
    u.close()
    logging.info('fetched url: %s' % url)
    return body

def get_soup(url):
    return bs(get_url(url))

homepage = get_soup(baseUrl)
# this URL is loaded the first time over
listUrl = homepage.html.body.find('iframe')['src']
# It will get us the first 30 committees. After that, we have
# to browse through pages by adding '?Start=X' to the URL.
# (I noticed this in a wireshark capture.)

committees = []

while True:
    if len(committees) == 0:
        listframe = get_soup(listUrl)
    else:
        listframe = get_soup(listUrl +
                '&Start=%d' % (len(committees) - 1))
    gotNew = False
    for tr in listframe.findAll('tr'):
        if not tr.tr and tr.a and tr.a.string.isdigit():
            gotNew = True
            number = int(tr.a.string)
            name = tr.span.string
            url = tr.a['href']
            if url.startswith('/'):
                url = portalBase + url
            logging.info('adding committee %d: %s' % (number, name))
            committees.append({
                'number': number,
                'name': name,
                'url': url})
    if not gotNew: break



# vim: set et ts=4 sw=4 :
