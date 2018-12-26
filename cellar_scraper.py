# import libraries
from datetime import datetime
import pytz
import logging
##import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

#define location dictionary for show_id
location_dict = {
        "MacDougal Street": "MCD",
        "Village Underground": "VU",
        "Fat Black Pussycat": "FBP"
    }

#get timestamp of snapshot
snapshot_timestamp = datetime.now(pytz.timezone('US/Eastern'))
print (snapshot_timestamp)

#set up logging file to record all data collected and any errors
logging.basicConfig(filename='cellar_scraper.log',level=logging.DEBUG)

#set url
cc_url = 'https://www.comedycellar.com/line-up/'

#use selenium/geckodriver to open firefox
browser = webdriver.Firefox()
#navigate to url
browser.get(cc_url)

#grab all inner HTML
innerHTML = browser.execute_script("return document.body.innerHTML")

# parse the html using beautiful soup and store in variable 'soup'
soup = BeautifulSoup(innerHTML, 'html.parser')

# get useful info out of html
#initialize array that will hold show objects
details = []

for day in range(len(soup.find('form', attrs = {'id':'filter-lineup-shows-form'}).findAll('li'))):
    WebDriverWait(browser, 5000).until(EC.visibility_of_element_located((By.ID, "dk_container__date")))
    dropdown = browser.find_element_by_id('dk_container__date')
    dropdown.click()
##    jsExec = (JavascriptExecutor) driver
##    jsExec.executeScript("document.getElementById('dk_container__date').scrollDown += 100")
##    scroll_depth = 5000 * day
##    browser.execute_script("document.getElementById('dk_container__date').scrollDown += " + str(scroll_depth)) 
##    dropdown.send_keys(Keys.DOWN)
##    dropdown.send_keys(Keys.ENTER)
    date_li = browser.find_element_by_id('dk_container__date').find_elements_by_tag_name("li")[day]
    date_li.click()
    
    #grab all inner HTML
    innerHTML = browser.execute_script("return document.body.innerHTML")

    # parse the html using beautiful soup and store in variable 'soup'
    soup = BeautifulSoup(innerHTML, 'html.parser')

    #get show date/day_of_week
    show_date_raw = soup.find('div', attrs = {'class':'show-search-title'})
    show_day_of_week = show_date_raw.find('span', attrs = {'class':'white'}).text.lstrip()
    print(show_day_of_week)
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
            continue
        else:
            location = "Fat Black Pussycat"
        location_code = location_dict[location]
        showtime_id = location_code + show_timestamp_code
        for comedian in show.findAll('div', attrs = {'class':'comedian-block-desc'}):               
            #initialize show object
            show_comedian_dets = {}
            show_comedian_dets['show_day_of_week'] = show_day_of_week
            show_comedian_dets['show_timestamp'] = show_timestamp
            show_comedian_dets['showtime_id'] = showtime_id
            show_comedian_dets['location'] = location
            for name in comedian.findAll('span', attrs = {'class':'comedian-block-desc-name'}):
                raw_name = name.text
                if 'MC for this show:' in raw_name:
                    comedian_name = raw_name[18:].lstrip().replace("\t", "")
                    show_comedian_dets['is_mc'] = True
                else:
                    comedian_name = raw_name.lstrip().replace("\t", "")
                    show_comedian_dets['is_mc'] = False
                show_comedian_dets['comedian_name'] = comedian_name
            raw_comedian = comedian.text
            start_description = raw_comedian.find(comedian_name) + len(comedian_name)
            raw_comedian_description = raw_comedian[start_description:].lstrip()
            if 'View Website' in raw_comedian_description:
                comedian_description = raw_comedian_description[:-13].lstrip().replace("\t", "")
            else:
                comedian_description = raw_comedian_description.lstrip().replace("\t", "")
            show_comedian_dets['comedian_description'] = comedian_description
            show_comedian_dets["snapshot_timestamp"] = snapshot_timestamp
            details.append(show_comedian_dets)

##print(details)
#close browser
browser.quit()
