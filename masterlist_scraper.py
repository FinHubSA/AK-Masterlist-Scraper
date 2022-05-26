import json
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
from selenium.webdriver.support.select import Select


with open(r'inputs.json', 'r') as input_file:
    input_deets = json.load(input_file)

# Journal page URL
URL = input_deets['journal_URL']
directory = input_deets['directory']

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

driver.get(URL)
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
#cols=['year', 'month', 'volume', 'issue','issue_url','Jstor_issue_text','journal', 'pivot_url', 'no_docs']
#data=pd.DataFrame(columns=cols)

cols=['year','Jstor_issue_text','Journal','stable_url','authors','title','issue_url','pages']
masterlist=pd.DataFrame(columns=cols)

cols2=['year','issue_url','Jstor_issue_text','Journal']
data=pd.DataFrame(columns=cols2)


click=driver.find_elements(By.XPATH,r".//dl[@class='facet accordion']//dl//dt//a")
# expand the drawers one by one, sometimes it doesn't work if you bulk click
for element in click:
    time.sleep(5)
    element.click()
# let everything settle
time.sleep(10)

decade_List=driver.find_elements(By.XPATH,r".//dd//ul//li")

for element in decade_List:
    year_list=element.find_elements(By.XPATH,r".//ul//li//a")
    temp=element.get_attribute('data-year')
    if temp==None:
        continue
    for item in year_list:
        issue_url=item.get_attribute('href')
        Jstor_issue_text=item.text
        data=data.append(pd.Series([int(temp), issue_url, Jstor_issue_text, input_deets["journal_name"]], index=data.columns), ignore_index=True )

for ind in data.index:
    time.sleep(5*random.random())     
    driver.get(data['issue_url'][ind])
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
        
    # Download Citations
    time.sleep(20)
    checkbox=driver.find_element(By.CLASS_NAME, "select_all_citations")
    checkbox.find_element(By.XPATH,r".//span[@slot='label']").click()

    dropdown = driver.find_element(By.ID,"export-bulk-drop").click()
    input()
    
    #dropdown=driver.find_element(By.CLASS_NAME,"bibtex_bulk_export export_citations")
    dropdown.find_element(By.CLASS_NAME,"dropdown-menu-item__button").click()
    
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

#data.to_excel(input_deets['pivots'], index=False)
masterlist.to_excel(directory+"/"+input_deets['journal_name']+"_master.xlsx")
