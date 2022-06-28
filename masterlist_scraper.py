import json
import os
import random
import time
from datetime import datetime

import bibtexparser
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from journal_title_scraper import *
from vpn import *

# Set directory and import journal list
directory = os.path.dirname(__file__)
journal_list = clean_data()["title_url"]

# Start VPN Service (choose high performance service for initial scrape)
expressvpn(directory, "UK - London")

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36"
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(f"user-agent={USER_AGENT}")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_extension("./extension_1_38_6_0.crx")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)
chrome_options.add_experimental_option(
    "prefs",
    {
        "download.default_directory": directory,  # Change default directory for downloads
        "download.prompt_for_download": False,  # To auto download the file
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,  # It will not show PDF directly in chrome
        "credentials_enable_service": False,  # gets rid of password saver popup
        "profile.password_manager_enabled": False,  # gets rid of password saver popup
    },
)
throttle = 0
driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

driver.execute_script(
    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
)

# load input file to specify where the loop should start
with open("start.json", "r") as input_file:
    data = json.load(input_file)

journal_start = data["journal_start"]
issue_start = data["issue_start"]

for journal in journal_list[journal_start : len(journal_list)]:

    scrape_start = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    page_loaded = False

    while not page_loaded:
        # Retrieving journal data
        driver.get(journal)
        time.sleep(10)
        driver.maximize_window()

        try:
            WebDriverWait(driver, 20).until(
                expected_conditions.presence_of_element_located(
                    (By.CLASS_NAME, "facets-container")
                )
            )
            print("passed")
            rotated = "False"
            page_loaded = True
        except:
            print("Failed to access journal page")

            # Connect to new server
            expressvpn(directory, vpn_list(directory))
            rotated = "True"

    try:
        WebDriverWait(driver, 20).until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, r"//button[@id='onetrust-accept-btn-handler']")
            )
        )

        driver.find_element(
            By.XPATH, r".//button[@id='onetrust-accept-btn-handler']"
        ).click()
        print("cookies accepted")
    except:
        print("No cookies, continue")

    time.sleep(10)

    random.seed(time.time())
    issue_url_list = []
    # issue_url_df=pd.DataFrame()

    click = driver.find_elements(
        By.XPATH, r".//dl[@class='facet accordion']//dl//dt//a"
    )
    # expand the decade drawers one by one
    for element in click:
        time.sleep(5)
        element.click()

    time.sleep(10)

    # captures the year elements within the decade
    decade_List = driver.find_elements(By.XPATH, r".//dd//ul//li")

    # captures the issues of the year element and records the issue url
    for element in decade_List:
        year_list = element.find_elements(By.XPATH, r".//ul//li//a")
        temp = element.get_attribute("data-year")
        if temp == None:
            continue
        for item in year_list:
            issue_url = item.get_attribute("href")
            print(issue_url)
            issue_url_list.append(issue_url)

            # Creating a tracker file
            # url_item=pd.DataFrame({'url':[issue_url],'scraped':[0],'Journal':[journal]})
            # issue_url_df=issue_url_df.concat(issue_url_df,url_item)

    # issue_url_df.to_csv("issue_url_df.csv")

    # loops through a dataframe of issue urls and captures metadata per issue
    for issue_url in issue_url_list[issue_start : len(issue_url_list)]:
        time.sleep(5 * random.random())
        driver.get(issue_url)

        try:
            # Download Citations

            WebDriverWait(driver, 30).until(
                expected_conditions.element_to_be_clickable(
                    (
                        By.XPATH,
                        r".//toc-view-pharos-checkbox[@id='select_all_citations']/span[@slot='label']",
                    )
                )
            ).click()
            WebDriverWait(driver, 30).until(
                expected_conditions.element_to_be_clickable((By.ID, "export-bulk-drop"))
            ).click()

            time.sleep(10)

            # download_metadata=driver.find_element(By.XPATH,r".//toc-view-pharos-dropdown-menu-item[@class='bibtex_bulk_export export_citations']")
            download_metadata = driver.find_element(
                By.XPATH,
                r"//*[@id='bulk-citation-dropdown']/toc-view-pharos-dropdown-menu-item[5]",
            )
            print(download_metadata.size)

            driver.implicitly_wait(5)

            ActionChains(driver).move_to_element(download_metadata).perform()

            driver.implicitly_wait(10)
            # WebDriverWait(driver,30).until(expected_conditions.element_to_be_clickable((By.XPATH,r"//*[@id='bulk-citation-dropdown']/toc-view-pharos-dropdown-menu-item[5]"))).click()
            driver.execute_script("arguments[0].click();", download_metadata)

        except Exception as e:
            print(e)
            input()

        old_name = os.path.join(directory, "citations.txt")
        new_name = os.path.join(directory, issue_url.split("/")[-1] + ".txt")

        # Wait for download to complete
        count = 0
        while not os.path.isfile(old_name) and count <= 10:
            time.sleep(1)
            count += 1

        os.rename(old_name, new_name)

        time.sleep(2)

        with open(new_name) as bibtex_file:
            convert = bibtexparser.load(bibtex_file)

        with open("Metadata.json", "r") as input_json_file:
            metadata = json.load(input_json_file)

        for entry in convert.entries:
            metadata.append(entry)

        with open("Metadata.json", "w") as output_json_file:
            json.dump(metadata, output_json_file, indent=4, sort_keys=True)

        os.remove(new_name)

        # Update tracker file to pin new start location
        if len(issue_url_list) == issue_start + 1:
            issue_start = 0
        else:
            issue_start = issue_start + 1
        data["issue_start"] = issue_start
        with open("start.json", "w") as input_file:
            json.dump(data, input_file)

    scrape_end = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    # Append log file
    with open("scraper_log.txt", "a+") as log:
        log.write("\n")
        log.write("\nJournal: " + journal)
        log.write("\nNumber of Issues scraped: " + str(len(issue_url_list)))
        log.write("\nRotated IP: " + rotated)
        log.write("\nStart time: " + scrape_start)
        log.write("\nEnd time: " + scrape_end)

    # Update tracker file to pin new start location
    journal_start = journal_start + 1
    data["journal_start"] = journal_start
    with open("start.json", "w") as input_file:
        json.dump(data, input_file)
