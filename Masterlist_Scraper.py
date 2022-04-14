import json
import os
import sys
from pathlib import Path
import time
import pandas as pd
import random
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from json import JSONDecoder
import stem.process
from stem import Signal
from stem.control import Controller
import requests
from datetime import datetime
import re
from recaptcha_solver import recaptcha_solver

# Improve the scraper by making it more human like. This includes:
# - Random time intervals between clicking on objects
# - Accessing other web-pages between the website you are scraping
# - Randomising the search pattern


# Define function that decodes the javascript text file
def extract_json_objects(text, decoder=JSONDecoder()):
    pos = 0
    while True:
        match = text.find('{', pos)
        if match == -1:
            break
        try:
            result, index = decoder.raw_decode(text[match:])
            yield result
            pos = match + index
        except ValueError:
            pos = match + 1

# Select a random User Agent
USER_AGENT_LIST = ['Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
                ]

USER_AGENT = random.choice(USER_AGENT_LIST)   

chrome_options = webdriver.ChromeOptions()

# Define Proxy: Could add some work here to rotate Proxy if we get stick
#PROXY = '102.182.190.209:47210'

# Add chrome options
#chrome_options.add_argument('--proxy-server=%s' % PROXY)
chrome_options.add_argument(f"user-agent={USER_AGENT}")
chrome_options.add_extension("./extension_1_38_6_0.crx")
chrome_options.add_extension("./extension_busters.crx")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

throttle=0

driver = webdriver.Chrome(ChromeDriverManager().install(), options = chrome_options)

# load input file to specify where the loop should start
with open("start.json","r") as input_file:
    data = json.load(input_file)

start = data['start']

# Article page URL
for x in range(start,50000000):

    URL = f"https://www.jstor.org/stable/{x}"
    driver.get(URL)
    error_404 = False
    
    try:
        # Check for reCAPTCHA and Resolve
        WebDriverWait(driver,20).until(expected_conditions.presence_of_element_located((By.XPATH, "/html/body/div[4]/div[4]/iframe")))
        print("reCAPTCHA needs to be Resolved")
        print("Calling reCAPTCHA solver")
        recaptcha_solver(driver)
    except:
        try:
            url_class_list = ["stable-url","stable_url"]
            
            for url_class in url_class_list:
                WebDriverWait(driver,20).until(expected_conditions.presence_of_element_located((By.ID, r"//div[@data-qa='stable-url']")))
            print("page exists")
        except:
            try:
                WebDriverWait(driver,20).until(expected_conditions.presence_of_element_located((By.XPATH, r"//main[@id='content']/div/div[@class='error']")))
                print("Error 404: Page not found")
                
                # Update tracker file to pin new start location
                start = x+1
                data["start"] = start
                with open("start.json","w") as input_file:
                    json.dump(data, input_file)

                error_404=True
                # fix the handling of the error to make it automatic
            except:  
                print("Error has occured: Resolve to page: " + URL)
                input()
                # Fix the recaptchas

    if error_404==False:
    # Accept the cookies
        try:
            WebDriverWait(driver, 20).until(expected_conditions.element_to_be_clickable((By.XPATH, r"//button[@id='onetrust-accept-btn-handler']")))
            driver.find_element(By.XPATH,r".//button[@id='onetrust-accept-btn-handler']").click()
            print('cookies accepted')
        except:
            print("Please accept cookies else continue if there aren't any")


        # Retrieve the metadata

        # 1) Retrieve the javascript metadata
        jsmetadata = driver.find_element(By.XPATH,r".//script[@data-analytics-provider='ga']").get_attribute("text")

        jsmetadatalist = []
        for result in extract_json_objects(jsmetadata):
            jsmetadatalist.append(result)

        print(jsmetadatalist[3])

        # 2) Retrieve the Authors (adjust this section)
        author = ""
        author_class_list = ["author-font","author","contrib"]
        for author_class in author_class_list:
            try:
                WebDriverWait(driver,10).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, author_class)))
                print("author name found")
                author = driver.find_element(By.CLASS_NAME,author_class).text
                print(author)
            except:
                continue    

        # 3) Retrieve the abstract if there is one
        # some articles are rather reviews or comments or replies and will not have abstracts
        abstract=""
        try:
            WebDriverWait(driver,10).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, "summary-paragraph")))
            print("abstract found")
            abstract = driver.find_element(By.CLASS_NAME,"summary-paragraph").text
            print(abstract)
        except:
            abstract=None

        # 4) Store pdf link if article is opensource
        # some articles are opensource and can be freely accessed via JSTOR --> we could download these in this section of code <--
        open_access=""
        try:  
            WebDriverWait(driver,30).until(expected_conditions.presence_of_element_located((By.XPATH, r"//div[@id='metadata-info-tab-contents']/div/div/div/div/span/span/span")))
            print("Article is Open Access")
            open_access=True
        except:
            print("not Open Access")
            open_access=False

        # 5) Retrieve References
        ref=""
        try:
            time.sleep(5)
            driver.find_element(By.ID, r"reference-tab").click()
            time.sleep(2)
            WebDriverWait(driver,30).until(expected_conditions.presence_of_element_located((By.ID, 'reference-tab-contents')))
            ref=driver.find_element(By.XPATH,r"//div[@id='references']/div/div/ul").text
            print('references scraped')
        except Exception as e: 
            print(e)
            print('no references in contents')  
    
        
        # Add variables to python dictionary
        metadata = jsmetadatalist[3]
        metadata['Author Name'] = author
        metadata['Abstract'] = abstract
        metadata['References'] = ref
        metadata['Open Access'] = open_access
        metadata['URL'] = URL

        
        with open('Metadata.json',"r") as file:
            data = json.load(file)

        data.append(metadata)

        with open('Metadata.json',"w") as file:
            data = json.dump(data,file)      






