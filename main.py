import json
import time 
import os

from DrissionPage import ChromiumPage
from DrissionPage import ChromiumOptions

from utils.check_site import check_site
from utils.drop_sheet import drop_info

from configparser import ConfigParser

config = ConfigParser()
config.read('constants/crucial.ini')

def main():
    scrap_linkedin()


def scrap_apollo():
    
    for index in range(1, 100):
        # Get url from constants
        url = f'https://app.apollo.io/#/companies?organizationNumEmployeesRanges[]=11%2C20&page={index}&sortAscending=false&sortByField=%5Bnone%5D'

        # Create driver
        driver = ChromiumPage()
        driver.get(url)

        apply_cookies(driver, 'cookies')

        # Get all companies children
        companies = driver.ele('.zp_tFLCQ').children()

        # Go through all companies
        for company in companies:
            # Get each cell
            cells = company.eles('.zp_KtrQp')
            if len(cells) <= 2:
                continue
            
            # And locate link that has website
            links = cells[2].eles('.zp_uzcP0')

            # Go through all links that contains website
            for link in links:
                
                link_childs = link.children()

                for child in link_childs:
                    
                    # Parse attribute aria-label (if it's website, proceed)
                    if child.attr('aria-label') == 'website':
                        link = child.attr('href')

                        website_stat = check_site(link)

                        if website_stat:
                            print(website_stat)

                        try:
                            drop_info(website_stat)
                        except Exception as e:
                            print(f"Error while adding data to sheet: {e}")
                            pass


    driver.close()

def scrap_linkedin():
    for index in range(int(config['Var']['last_index']), 100):
        parsed_web_file = os.path.join(os.path.dirname(__file__), '..', 'constants', 'parsed_websites.json')
        config['Var']['last_index'] = str(index)
        
        with open('constants/crucial.ini', 'w') as f:
            config.write(f)
        
        if os.path.exists(parsed_web_file):
            try:
                with open(parsed_web_file, 'r') as f:
                    parsed_websites = json.load(f)

                    if not isinstance(parsed_websites, list):
                        parsed_websites = []
            except json.JSONDecodeError:
                parsed_websites = []
        else:
            parsed_websites = []


        url = f'https://www.linkedin.com/sales/search/company?page={index}&query=(filters%3AList((type%3AANNUAL_REVENUE%2CrangeValue%3A(min%3A1%2Cmax%3A5)%2CselectedSubFilter%3AUSD)%2C(type%3ACOMPANY_HEADCOUNT%2Cvalues%3AList((id%3AC%2Ctext%3A11-50%2CselectionType%3AINCLUDED)))%2C(type%3AREGION%2Cvalues%3AList((id%3A103644278%2Ctext%3AUnited%2520States%2CselectionType%3AINCLUDED)))%2C(type%3ANUM_OF_FOLLOWERS%2Cvalues%3AList((id%3ANFR4%2Ctext%3A1001-5000%2CselectionType%3AINCLUDED)))%2C(type%3ATECHNOLOGIES_USED%2Cvalues%3AList((id%3A1194%2Ctext%3AElementor%2CselectionType%3AINCLUDED)))))&sessionId=AdI8dPOWRfawHWCqXOnU9A%3D%3D&viewAllFilters=true'
        
        options = ChromiumOptions()
        options.set_argument("--force-device-scale-factor=1")
        driver = ChromiumPage(options)
        driver.get(url)

        apply_cookies(driver, 'linkedin_cookie')

        time.sleep(7)
        
        company_bunch = driver.ele('.artdeco-list background-color-white _border-search-results_1igybl')
        companies = company_bunch.children()

        company_links = []

        for company in companies:
            try:
                link = company.ele('.ember-view').link
            except Exception:
                continue
            
            company_links.append(link)

            driver.ele('#search-results-container').scroll.down(500)

            time.sleep(0.3)

        for url in company_links:
            time.sleep(5)

            company_tab = driver.new_tab(url)

            try:
                website_link = company_tab.ele('.ember-view artdeco-button view-website-link artdeco-button--2 artdeco-button--secondary artdeco-button--muted _block-size-button_ma5xyq').link
            except:
                company_tab.close()
                continue

            if website_link in parsed_websites:
                print(f"Website {website_link} already parsed")
                continue

            website_stat = check_site(website_link, driver)

            if website_stat:
                print(item['status'] for item in website_stat)

            print(website_stat)

            try:
                drop_info(website_stat)
            except Exception as e:
                print(f"Error while adding data to sheet: {e}")
                pass
            
            company_tab.close()

    driver.close()

def apply_cookies(driver, cookie_name):
    # Open cookie file and go through the all cookies
    with open(f'constants/{cookie_name}.json', 'r') as f:
        cookies = json.load(f)
        
        for cookie in cookies:
            if cookie.get('sameSite') not in ['None', 'Lax', 'Strict']:
                cookie['sameSite'] = 'Lax'
            
            # Add it via driver method
            driver.set.cookies(cookie)

    # Refresh to apply changes
    driver.refresh()

if __name__ == '__main__':
    main()
    