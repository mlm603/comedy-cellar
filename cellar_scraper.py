# import libraries
from __future__ import print_function
from datetime import datetime
import pytz
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
from pandas import DataFrame
from dim_shows import dim_shows
import os
import psycopg2
import sys
import logging
import json_log_formatter
import traceback

formatter = json_log_formatter.JSONFormatter()
json_handler = logging.FileHandler(filename='var/log/email-logs.json')
json_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(json_handler)
logger.setLevel(logging.INFO)

pd.set_option('mode.chained_assignment', None)

LOCAL_DATABASE_URL = "postgresql://localhost/cellar_scraper"

local_conn = psycopg2.connect(LOCAL_DATABASE_URL)
local_cursor = local_conn.cursor()

#define location dictionary for show_id
location_dict = {
        "MacDougal Street": "MCD",
        "Village Underground": "VU",
        "Fat Black Pussycat": "FBP"
    }

#get timestamp of snapshot
snapshot_timestamp = datetime.now(pytz.timezone('US/Eastern'))
print (snapshot_timestamp)
snapshot_date_string = str(snapshot_timestamp.date()).replace("-","_")

# set up logging file to record all data collected and any errors
logging.basicConfig(filename='cellar_scraper.log',level=logging.DEBUG)

#set url
cc_url = 'https://www.comedycellar.com/line-up/'

# use selenium/geckodriver to open chrome
# ChromeDriverManager makes sure latest chromedriver is used
browser = webdriver.Chrome(ChromeDriverManager().install())

# phrases captured as comedian_names to exclude from results
comedian_name_blacklist = ["MORE TO BE ANNOUNCED", "All Proceeds Of This Show go to: The Bronx Freedom Fund", "This Week At The Comedy Cellar", "Comedians From the Seth Meyers Show with Ryan Reiss"]

try:
    #navigate to url
    browser.get(cc_url)

    #grab all inner HTML
    innerHTML = browser.execute_script("return document.body.innerHTML")

    # parse the html using beautiful soup and store in variable 'soup'
    soup = BeautifulSoup(innerHTML, 'html.parser')

    new_values = []
    showtime_ids = []

    """
    Get most recent show snapshots 
    """

    for day in range(len(soup.find('form', attrs = {'id':'filter-lineup-shows-form'}).findAll('li'))):
        WebDriverWait(browser, 500).until(EC.visibility_of_element_located((By.ID, "dk_container__date")))
        dropdown = browser.find_element_by_id('dk_container__date')
        dropdown.click()
        #hide p elements and clearfix div because they obscure dropdown menu
        el = browser.find_elements_by_tag_name("p")
        for p in range(len(el)):
            browser.execute_script("arguments[0].style.visibility='hidden'", el[p])
        clearfix_el = browser.find_element_by_xpath("//div[@class='shows-container']/div[@class='clearfix']")
        browser.execute_script("arguments[0].style.visibility='hidden'", clearfix_el)
        date_li = browser.find_element_by_id('dk_container__date').find_elements_by_tag_name("li")[day]
        date_li.click()
        
        #grab all inner HTML
        innerHTML = browser.execute_script("return document.body.innerHTML")

        # parse the html using beautiful soup and store in variable 'soup'
        soup = BeautifulSoup(innerHTML, 'html.parser')

        #get show date/day_of_week
        show_date_raw = soup.find('div', attrs = {'class':'show-search-title'})
        show_day_of_week = show_date_raw.find('span', attrs = {'class':'white'}).text.lstrip()
        show_date = show_date_raw.text[len(show_day_of_week) + 2:-2].lstrip()
        for show in soup.findAll('div', attrs = {'class':'show'}):
            #combine show date and time into single timestamp
            show_time_raw = show.find('span', attrs = {'class':'show-time'}).text
            show_time_end = show_time_raw.find('show')
            show_time = show_time_raw[:show_time_end - 1].lstrip()
            show_datetime_agg = show_date + ' ' + show_time
            show_timestamp = datetime.strptime(show_datetime_agg, '%B %d, %Y %I:%M %p')
            show_timestamp_code = datetime.strftime(show_timestamp, '%Y%m%d%H%M')
            #get location
            location_start = show_time_raw.find('|') + 2
            location = show_time_raw[location_start:-7].lstrip()
            if location in ["MacDougal Street", "Village Underground", "Fat Black Pussycat"]:
                location = location
            else:
                location = "Fat Black Pussycat"
            location_code = location_dict[location]
            showtime_id = location_code + show_timestamp_code
            showtime_ids.append(showtime_id)
            for comedian in show.findAll('div', attrs = {'class':'comedian-block-desc'}):
                for name in comedian.findAll('span', attrs = {'class':'comedian-block-desc-name'}):
                    raw_name = name.text
                    if 'MC for this show:' in raw_name:
                        comedian_name = raw_name[18:].lstrip().replace("\t", "")
                        is_mc = True
                    else:
                        comedian_name = raw_name.lstrip().replace("\t", "")
                        is_mc = False
                if comedian_name not in comedian_name_blacklist:
                    if len(comedian_name) > 50:
                        logger.info("long comedian name: " + comedian_name, extra={'status': 'Error'})
                        comedian_name = comedian_name[:50]
                    raw_comedian = comedian.text
                    start_description = raw_comedian.find(comedian_name) + len(comedian_name)
                    raw_comedian_description = raw_comedian[start_description:].lstrip()
                    if 'View Website' in raw_comedian_description:
                        comedian_description = raw_comedian_description[:-13].lstrip().replace("\t", "")
                    else:
                        comedian_description = raw_comedian_description.lstrip().replace("\t", "")

                    comedian_description = comedian_description[:255]
                    
                    comedian_value = [
                                        showtime_id
                                        , snapshot_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')
                                        , show_day_of_week
                                        , show_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')
                                        , location
                                        , is_mc
                                        , comedian_name
                                        , comedian_description
                                        , True #is_most_recent_timestamp should always be true when this runs
                                    ]

                    new_values.append(comedian_value) 

    logger.info("Finished scraping shows")

    """
    Update is_most_recent_timestamp flags in existing 
    """

    local_cursor.execute("""
                        SELECT *
                        FROM fact_shows;
                    """)
    fact_shows_old = DataFrame(local_cursor.fetchall())
    fact_shows_old.columns = [desc[0] for desc in local_cursor.description]

    #where existing showtime_id is in showtime_ids
    #set is_most_recent_snapshot to FALSE

    showtime_ids = "', '".join(showtime_ids)

    local_cursor.execute("""
                        UPDATE fact_shows
                        SET is_most_recent_snapshot = FALSE 
                        WHERE showtime_id IN ('
                    """ + showtime_ids + "');")

    local_conn.commit()

    new_values_df = pd.DataFrame(new_values, columns=['showtime_id', 'snapshot_timestamp', 'show_day_of_week', 'show_timestamp', 'location', 'is_mc', 'comedian_name', 'comedian_description', 'is_most_recent_snapshot'])

    # store the scraped data in a CSV with the current date in the file name
    new_filename = 'fact_shows/' + snapshot_date_string + '.csv'
    new_values_df.to_csv(new_filename, index = False, header = False)
    
    # copy the CSV to the local fact_shows table
    sys.stdin = open(new_filename)
    local_cursor.copy_expert("COPY fact_shows FROM STDIN WITH (FORMAT CSV)", sys.stdin)

    local_conn.commit()

    logger.info("Appended new data to fact_shows")

    local_cursor.close()
    local_conn.close()

    browser.quit()
    
    dim_shows(snapshot_date_string)
except Exception as e:
    logger.info(e, exc_info=True, extra={'status': 'Error'})



