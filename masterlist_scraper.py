import json
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import os
import bibtexparser
from journal_title_scraper import *
  

# Set directory and import journal list (wait for input from Alex to finalise this)
directory = os.path.dirname(__file__)
journal_list=clean_data()['title_url']


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
chrome_options = webdriver.ChromeOptions()
# ------ #
# uncomment the below if you dont want the google chrome browser UI to show up.
# not reccommended
#chrome_options.add_argument('--headless')

chrome_options.add_argument(f"user-agent={USER_AGENT}")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_extension("./extension_1_38_6_0.crx")
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
throttle=0
driver = webdriver.Chrome(ChromeDriverManager().install(), options = chrome_options)

driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

for journal in journal_list:

    driver.get(journal)
    try:
        WebDriverWait(driver,20).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, "facets-container")))
        print("passed")
        time.sleep(5)
        WebDriverWait(driver, 20).until(
            expected_conditions.element_to_be_clickable((By.XPATH, r"//button[@id='onetrust-accept-btn-handler']"))
        )

        driver.find_element(By.XPATH,r".//button[@id='onetrust-accept-btn-handler']").click()
        print('cookies accepted')
    except:
        print("Failed to access journal page")
        raise
        
    time.sleep(10)

    random.seed(time.time())
    issue_url_list = list()

    click=driver.find_elements(By.XPATH,r".//dl[@class='facet accordion']//dl//dt//a")
    # expand the decade drawers one by one
    for element in click:
        time.sleep(5)
        element.click()
    time.sleep(10)

    # captures the year elements within the decade 
    decade_List=driver.find_elements(By.XPATH,r".//dd//ul//li")

    # captures the issues of the year element and records the issue url
    for element in decade_List:
        year_list=element.find_elements(By.XPATH,r".//ul//li//a")
        temp=element.get_attribute('data-year')
        if temp==None:
            continue
        for item in year_list:
            issue_url=item.get_attribute('href')
            issue_url_list.append(issue_url)

    # loops through a dataframe of issue urls and captures metadata per issue
    for issue_url in issue_url_list:
        time.sleep(5*random.random())     
        driver.get(issue_url)

        # Download Citations
        time.sleep(10)

        WebDriverWait(driver,30).until(expected_conditions.element_to_be_clickable((By.XPATH,r".//toc-view-pharos-checkbox[@id='select_all_citations']/span[@slot='label']"))).click()
        WebDriverWait(driver,30).until(expected_conditions.element_to_be_clickable((By.ID,"export-bulk-drop"))).click()
        WebDriverWait(driver,30).until(expected_conditions.element_to_be_clickable((By.XPATH,r".//toc-view-pharos-dropdown-menu-item[@class='bibtex_bulk_export export_citations']"))).click()

        time.sleep(10)

        old_name=os.path.join(directory,'citations.txt')
        new_name=os.path.join(directory,issue_url.split("/")[-1]+'.txt')
        os.rename(old_name,new_name)

        time.sleep(10)

        with open(new_name) as bibtex_file:
            convert=bibtexparser.load(bibtex_file)
        
        with open("Metadata.json","r") as input_json_file:
            metadata=json.load(input_json_file)

        for entry in convert.entries:
            metadata.append(entry)

        with open("Metadata.json", "w") as output_json_file:
            json.dump(metadata,output_json_file,indent=4,sort_keys=True)

        os.remove(new_name)

    #     try:
    #         WebDriverWait(driver,20).until(expected_conditions.presence_of_element_located((By.ID, "bulk_citation_export_form")))
    #     except:
    #         print("Timed out: manually resolve the page to"+ data['issue_url'])
    #         print("Press enter to continue after page completely loads")
    #         input()
    #         throttle+=(random.random()*5)
    #     time.sleep(5+throttle)
    #     #data['pivot_url'][ind]=driver.find_element(By.XPATH,r".//div[@class='citation-export-section']//div[@class='stable']").text

    #     temp={'year': None, 'Jstor_issue_text': None, 'Journal': None, 'stable_url' : None, 'authors' : None, 'title' : None, 'issue_url' : None, 'pages' : None}
    #     time.sleep(30)
    #     all_docs=driver.find_elements(By.XPATH,r".//ol[@class='toc-export-list']//div[@class='toc-content-wrapper']")
    #     for item in all_docs:
    #         try:
    #             temp['stable_url'] = item.find_element(By.XPATH,r".//div[@class='stable']").text
    #         except:
    #             print("invalid case")
    #             continue
    #         temp['title'] = item.find_element(By.XPATH,r".//toc-view-pharos-link[@data-qa='content title']").text
    #         temp['issue_url']=data['issue_url'][ind]
    #         temp2=item.text.split('\n')[0].split('p.')
    #         if len(temp2)>1:
    #             temp['pages']=temp2[-1].split(')')[0]
    #         print(temp2)
    #         try:
    #             temp['authors']= item.find_element(By.XPATH,r".//div[@class='contrib']").text
    #         except:
    #             temp['authors']=None
    #             print('no authors')
    #         temp['year']=data['year'][ind]
    #         temp['Jstor_issue_text']=data['Jstor_issue_text'][ind]
    #         temp['Journal']=data['Journal'][ind]
    #         masterlist=masterlist.append(temp, ignore_index=True)

        # data['no_docs'][ind]=len(all_docs)
        # issue_data=driver.find_element(By.XPATH,r".//h1//div[@class='issue']").text.split(',')
        # print(issue_data)
        # print(len(all_docs))
        # try:
        #     data['volume'][ind]=int(issue_data[0].split()[1])
        #     data['issue'][ind]=issue_data[1].split()[1].replace('/','-')
        #     data['month'][ind]=issue_data[2].split()[0]
        # except:
        #     print('No issue or month metadata. Possibly is supplement, index or special issue')

    #.to_excel(input_deets['pivots'], index=False)
    #masterlist.to_excel(directory+"/"+input_deets['journal_name']+"_master.xlsx")
