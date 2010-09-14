#/usr/bin/python
# -*- encoding: utf-8 -*-

from BeautifulSoup import BeautifulSoup as bs
import urllib2
import os.path
import hashlib
import simplejson as json
import logging
logging.basicConfig(level=logging.INFO)

baseUrl = 'http://www.gost.ru/wps/portal/pages.TechCom'
portalBase = 'http://webportalsrv.gost.ru'
output = 'committees.json'

def get_url(url):
    hash = hashlib.sha1(url).hexdigest()
    hashfile = os.path.join('cache', hash)
    try:
        u = file(hashfile)
        logging.info('using URL cache')
        cached = True
    except IOError:
        u = urllib2.urlopen(url)
        cached = False
    body = u.read()
    u.close()
    logging.info('fetched url: %s' % url)
    if not cached:
        try:
            file(hashfile, 'w').write(body)
        except IOError:
            pass
    return body

def get_soup(url):
    return bs(get_url(url))

def cachefile(name, mode = 'r'):
    path = os.path.join('cache', name)
    return file(path, mode)

try:
    committees = json.load(cachefile('committees'))
except IOError:
    committees = []

    homepage = get_soup(baseUrl)
    # this URL is loaded the first time over
    listUrl = homepage.html.body.find('iframe')['src']
    # It will get us the first 30 committees. After that, we have
    # to browse through pages by adding '?Start=X' to the URL.
    # (I noticed this in a wireshark capture.)

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

    json.dump(committees, cachefile('committees', 'w'))

def flatText(node):
    text = ''.join(node.findAll(text=True)).strip()
    while text.endswith('&nbsp;'):
        text = text[:-6].rstrip()
    return text

def tableToTuples(table):
    rows = []
    for tr in table.findAll('tr', recursive=False):
        row = tuple(flatText(td) for td in tr.findAll('td', recursive=False))
        rows.append(row)
    return rows

def extractTables(node):
    divsTables = node.findAll(('div', 'table'))
    tables = []
    while divsTables:
        div = divsTables.pop(0)
        table = divsTables.pop(0)
        header = flatText(div)
        contents = tableToTuples(table)
        tables.append((header, contents))
    return tables

i = 0
for c in committees:
    logging.info('%d/%d complete' % (i, len(committees)))
    i += 1
    attributes = {}
    c['attributes'] = attributes
    soup = get_soup(c['url'])
    for tr in soup.table.findAll('tr', recursive=False):
        nameTd, valueTd = tr.findAll('td', recursive = False)
        name = flatText(nameTd)
        assert name
        if name in (
            u"Область деятельности ТК",
            u"Соответствующая международная организация по стандартизации"):
            value = extractTables(valueTd)
        else:
            value = flatText(valueTd)
        if name == u"№ приказа":
            value = value.split('\n')
        attributes[name] = value

json.dump(committees, file('output', 'w'))

# vim: set et ts=4 sw=4 :
