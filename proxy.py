import requests
from lxml.html import fromstring
from itertools import cycle
import traceback

def get_proxies():

    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    
    # return proxies
    for i in parser.xpath('//tbody/tr'):
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            #Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)

    return(proxies)

proxies = get_proxies()

proxy_pool = cycle(proxies)
url = 'https://httpbin.org/ip'
newIP = ""

while newIP == "":
    for i in proxy_pool:

            #Get a proxy from the pool
            proxy = next(proxy_pool)
            #print("Request #%d"%i)
            try:
                response = requests.get(url,proxies={"http": proxy, "https": proxy})
                newIP = i
                print(newIP)
            except:
                #Most free proxies will often get connection errors. You will have retry the entire request using another proxy to work. 
                print("Skipping. Connnection error")
