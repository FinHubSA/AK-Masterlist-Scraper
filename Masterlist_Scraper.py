import json
from pathlib import Path
import time
import random
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from json import JSONDecoder
from stem import Signal
from stem.control import Controller
import requests
from datetime import datetime
import re
from ast import Not
import os.path

from recaptcha_solver import recaptcha_solver, delay
from connection_controllers.gen_connection_controller import GenConnectionController
from recaptcha_solver import recaptcha_solver
from temp_storage import storage


# Set the storage location
directory = storage.createTempStorage()

# Define function that rotates IP using Tor <--do not use this now...it does not work well
def rotateIP():
        print ("Rotating IP")
        with Controller.from_port(port = 9051) as controller:
          controller.authenticate()
          controller.signal(Signal.NEWNYM)
          
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

while True:
    print("new driver started")
    # Select a random User Agent and set proxy
    USER_AGENT_LIST = ['Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
                    ]

    USER_AGENT = random.choice(USER_AGENT_LIST)   
    PROXY = "http://127.0.0.1:8118"

    chrome_options = webdriver.ChromeOptions()

    # Add chrome options
    curdir = Path.cwd().joinpath("BrowserProfile")
    #chrome_options.add_argument(f"--proxy-server=%s" % PROXY)
    chrome_options.add_argument(f"user-agent={USER_AGENT}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option("prefs", {
    "download.default_directory": directory, #Change default directory for downloads
    "download.prompt_for_download": False, #To auto download the file
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True, #It will not show PDF directly in chrome
    "credentials_enable_service": False, # gets rid of password saver popup
    "profile.password_manager_enabled": False #gets rid of password saver popup
    })

    driver = webdriver.Chrome(ChromeDriverManager().install(), options = chrome_options)  

    web_session = GenConnectionController(driver, "https://www.jstor.org")
    current_url = driver.current_url

    # load input file to specify where the loop should start
    with open("start.json","r") as input_file:
        data = json.load(input_file)
    
    start = data['start']

    for x in range(start,200):

        #log start time
        start_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

        # Article page URL
        URL = f"https://www.jstor.org/stable/{x}"
        driver.get(current_url + "stable/" + URL.split("/")[-1])

        try:
            WebDriverWait(driver,20).until(expected_conditions.presence_of_element_located((By.XPATH, r"//main[@id='content']/div/div[@class='error']")))
            print("[ERR] Error 404: Page not found")
            
            # Update tracker file to pin new start location
            start = x+1
            data["start"] = start
            with open("start.json","w") as input_file:
                json.dump(data, input_file)
            error=True
        except:
            # Accept the cookies
            try:
                WebDriverWait(driver,20).until(expected_conditions.element_to_be_clickable((By.XPATH, r"//button[@id='onetrust-accept-btn-handler']")))
                driver.find_element(By.XPATH,r".//button[@id='onetrust-accept-btn-handler']").click()
                print('cookies accepted')
            except:
                print("continue, there aren't any cookies")

            # Check for error message
            try: 
                WebDriverWait(driver,20).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, "error-message")))
                print("[ERR] Article page not loading, error message and possible reCAPTCHA")
                driver.find_element(By.XPATH, r".//content-viewer-pharos-link[@aria-label='Clicking this link will refresh the page.']").click()           
            except:
                print("No error, continue")

            # Check if page has loaded
            try:
                WebDriverWait(driver,20).until(expected_conditions.presence_of_element_located((By.XPATH, r"//div[@data-qa='stable-url']")))
                print("page exists")
                reCAPTCHA_start=""
                reCAPTCHA_end=""
                recaptcha_log=""
                error=False
            except:
                print("reCAPTCHA needs to be Resolved")    
                try:
                    # Check for reCAPTCHA and Resolve
                    WebDriverWait(driver,20).until(expected_conditions.presence_of_element_located((By.XPATH, "/html/body/div[4]/div[4]/iframe")))
                    
                    print("Calling reCAPTCHA solver")
                    
                    # Declare log variables
                    reCAPTCHA_start=datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

                    # Calling reCAPTCHA solver
                    recaptcha_solver(driver)
                    print("returned to program")

                    # Declare log variables
                    reCAPTCHA_end=datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

                    WebDriverWait(driver,20).until(expected_conditions.presence_of_element_located((By.XPATH, r"//div[@data-qa='stable-url']")))
                    error=False
                except:
                    print("[ERR] Unkown error has occured: restarting driver")

                    #append log file
                    with open('scraperlog.txt','a+') as log:
                        log.write('\n')
                        log.write('\nfor URL: ' + URL)
                        log.write('\nreCAPTCHA could not be solved and article not scraped: restarted driver') 
                        log.write('\nscraper started at: ' + start_time)
                        log.write('\nscraper ended at: ' + '')
                        log.write('\nreCAPTCHA started at: ' + reCAPTCHA_start)
                        log.write('\nreCAPTCHA ended at: ' + reCAPTCHA_end)
                    break
            
        if error==False:

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
                    print(author_class)
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
                WebDriverWait(driver,20).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, "summary-paragraph")))
                print("summary found")
                word = driver.find_element(By.XPATH, r"//div[@class='turn-away-content__article-information']/pharos-heading]").text
                print(word)
                abstract = driver.find_element(By.CLASS_NAME,"summary-paragraph").text
                print(abstract)


                if driver.find_element(By.XPATH, r"//div[@class='turn-away-content__article-information']/pharos-heading]").text=="Abstract":
                    abstract = driver.find_element(By.CLASS_NAME,"summary-paragraph").text
                    print("abstract found")
                else:
                    print("No article abstract found")
                    abstract=None
                print(abstract)
            except:
                print("No summary paragraph found.")
                abstract=None

            # 4) Lable article as open access
            # some articles are opensource and can be freely accessed via JSTOR
            open_access=""
            try:  
                WebDriverWait(driver,20).until(expected_conditions.presence_of_element_located((By.XPATH, r"//div[@id='metadata-info-tab-contents']/div/div/div/div/span/span/span")))
                print("Article is Open Access")
                open_access=True
            except:
                print("Article is not Open Access")
                open_access=False

            # 5) Retrieve References
            ref=""
            try:
                time.sleep(5)
                driver.find_element(By.ID, r"reference-tab").click()
                time.sleep(2)
                WebDriverWait(driver,20).until(expected_conditions.presence_of_element_located((By.ID, 'reference-tab-contents')))
                ref=driver.find_element(By.XPATH,r"//div[@id='references']/div/div/ul").text
                print('references scraped')
            except Exception as e: 
                print(e)
                print('no references in contents')  
        
            
             # 6) Retrieve author affiliations
            affiliations=""
            try:
                WebDriverWait(driver, 20).until(
                        expected_conditions.presence_of_element_located((By.CLASS_NAME, 'contrib-group'))
                        ) 
                author_info=driver.find_element(By.XPATH,r".//div[@class='contrib-group']//div//span")
                count=0
                for item in author_info:
                    if (count%2) == 0:
                        affiliations=affiliations+item.text+' - '
                    else:
                        affiliations=affiliations+item.text+'. '
                    count+=1
                print(affiliations)
            except:
                print('no author affiliation') 
           
            
            #7) Download PDF
            # Construct file name
            url = os.path.join(directory,URL.split("/")[-1] + ".pdf")
            doi = os.path.join(directory,"10.2307." + URL.split("/")[-1] + ".pdf")

            if not os.path.isfile(doi): 

                try:
                    print('finding pdf download')
                    WebDriverWait(driver,10).until(expected_conditions.presence_of_element_located((By.ID, "metadata-info-tab")))
                except:    
                    if WebDriverWait(driver,10).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, "error-message"))):
                        print("Article page not loading, possible reCAPTCHA")
                    
                        driver.find_element(By.XPATH, r".//content-viewer-pharos-link[@aria-label='Clicking this link will refresh the page.']").click()
                    
                    print("Calling reCAPTCHA solver")
                    recaptcha_solver(driver)

                #click download
                driver.find_element(by = By.XPATH, value = r".//mfe-download-pharos-button[@data-sc='but click:pdf download']").click()
                print("clicked on download")

                # bypass t&c (in some case t&c are different, I need to test to find another case again)
                try:
                    WebDriverWait(driver, 10).until(
                        expected_conditions.presence_of_element_located((By.ID, 'content-viewer-container'))
                        ) 
                    driver.find_element(by = By.XPATH, value = r".//mfe-download-pharos-button[@data-qa='accept-terms-and-conditions-button']").click()
                except:
                    print("no t&c")

                #need to allow time for download to complete and return to initial page
                time.sleep(30+random.random())

                #rename the pdf file to DOI
                storage.renameFile(url,doi)
            else:
                continue

            # Add variables to python dictionary
            metadata = jsmetadatalist[3]
            metadata['Author Name'] = author
            metadata['Abstract'] = abstract
            metadata['References'] = ref
            metadata['Affiliations'] = affiliations
            metadata['Open Access'] = open_access
            metadata['URL'] = URL
            metadata['Downloaded']="True"
            
            # Update metadata file
            with open('Metadata.json',"r") as file:
                data = json.load(file)

            data.append(metadata)

            with open('Metadata.json',"w") as file:
                data = json.dump(data,file,indent=4,sort_keys=True)      

            # Update tracker file to pin new start location
            with open("start.json","r") as input_file:
                data = json.load(input_file)
            
            start = x+1
            data["start"] = start
            with open("start.json","w") as input_file:
                json.dump(data, input_file)

            # # step 5: delete temp storage folder on local computer --> needs work <--
            # if storage.countFiles(directory)==15:
            #     print("deleting downloads")
            #     storage.deleteTempStorage(directory)
            # else:
            #     # try to handle the error: most likely a reCAPTCHA came up and download could not complete
            #     print("restart the driver")                           
            
            # Declare log variables
            end_time=datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

            #append log file
            with open('scraperlog.txt','a+') as log:
                log.write('\n')
                log.write('\nfor URL: ' + URL)
                log.write('\ndriver was not restarted') 
                log.write('\nscraper started at: ' + start_time)
                log.write('\nscraper ended at: ' + end_time)
                log.write('\nreCAPTCHA started at: ' + reCAPTCHA_start)
                log.write('\nreCAPTCHA ended at: ' + reCAPTCHA_end)

    driver.close()
    delay()




