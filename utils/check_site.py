import requests
import json
import os
import time

from bs4 import BeautifulSoup

from constants.config import PAGE_SPEED_KEY

# from DrissionPage import ChromiumPage

from utils.encode import encode_text

def check_site(url: str, driver=None): 
    parsed_web_file = os.path.join(os.path.dirname(__file__), '..', 'constants', 'parsed_websites.json')

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

    try:
        if url in parsed_websites:
            print(f"Website {url} already parsed")
            return
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)

    except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
        print(f"Error caused by {e}")

        parsed_websites.append(url)
        
        with open(parsed_web_file, "w") as f:
            json.dump(parsed_websites, f, indent=4)

        return [{"website": url, 
                 "status": "Has errors", 
                 "broken_links": "N/A",  
                 "sitemap_links": "N/A",
                 "page_speed": "N/A",
                 "seo_report": "N/A"}]
    
    # Elementor indicators
    elementor_indicators = [
        'elementor',
        'elementor-widget',
        'elementor-element'
    ]

    # Check if response was successful 
    if response.status_code != 200:
        with open(parsed_web_file, "w") as f:
            json.dump(parsed_websites, f, indent=4)

        return False

    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all elements with class containing elementor
    elementor_classes = []
    for element in soup.find_all(id=True)[:20]:
        if any(ind in element['id'].lower() for ind in elementor_indicators):
            elementor_classes.append(element['id'])
    
    # If no elementor IDs found, check classes
    if not elementor_classes:
        for element in soup.find_all(class_=True)[:20]:
            elementor_classes.extend([c for c in element['class'] if any(ind in c.lower() for ind in elementor_indicators)])

    if elementor_classes:
        sitemap_links = count_sitemap_links(url)
        page_speed = check_page_speed_v2(url, driver)

        # speed_results = get_page_speed_number(page_speed, driver)

        desktop_page_speed = check_page_speed(url, "desktop")

        if (sitemap_links and sitemap_links != "N/A") and desktop_page_speed and page_speed: 
            if desktop_page_speed <= 60 and int(sitemap_links) >= 20:
                parsed_websites.append(url)
                
                with open(parsed_web_file, "w") as f:
                    json.dump(parsed_websites, f, indent=4)

                mobile_page_speed = check_page_speed(url, "mobile")

                return [{"website": url, 
                        "status": "Live", 
                        "broken_links": check_broken_links(url), 
                        "sitemap_links": sitemap_links,
                        #  "seo_report": check_seo_v2(url, driver),
                        "page_speed": page_speed,
                        "mobile": mobile_page_speed,
                        "desktop": desktop_page_speed
                        }]
            else:
                print(desktop_page_speed, sitemap_links)

                parsed_websites.append(url)

                with open(parsed_web_file, "w") as f:
                    json.dump(parsed_websites, f, indent=4)
        else:
            try:
                return f"Sitemap: {sitemap_links}; Page Speed URL: {page_speed[:5]}; Page Index: {desktop_page_speed}"
            except Exception:
                pass
            
def check_page_speed(url: str, strategy='desktop'):
    # Call PageSpeed API
    api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={PAGE_SPEED_KEY}&strategy={strategy}"

    try:
        response = requests.get(api_url)
    except Exception:
        return None
    
    if response.status_code == 200:
        data = response.json()

        performance = int(data['lighthouseResult']['categories']['performance']['score'] * 100)

        return performance
    
    else:
        print(f"PageSpeed API error: {response.status_code}")
        return


def check_page_speed_v2(url: str, driver):
    site_url = 'https://pagespeed.web.dev/'

    page_speed_insight = driver.new_tab(site_url)

    try:
        url_input = page_speed_insight.ele('tag:input', index=1)
        button = page_speed_insight.ele('.VfPpkd-LgbsSe VfPpkd-LgbsSe-OWXEXe-k8QpJ VfPpkd-LgbsSe-OWXEXe-dgl2Hf nCP5yc AjY5Oe DuMIQc LQeN7 c659ib')

        url_input.input(url)

        time.sleep(0.2)

        button.click()
    except Exception:
        return

    try:
        while True:
            if "form_factor" in page_speed_insight.url:
                result_url = page_speed_insight.url
                page_speed_insight.close()

                return result_url
            
            time.sleep(0.5)
    except Exception as e:
        print(e)

        page_speed_insight.close()
        return


def get_page_speed_number(report_url: str, driver):
    page_speed_insight = driver.new_tab(report_url)

    while True:
        time.sleep(0.4)

        html_content = page_speed_insight.html

        if "Something went wrong" in html_content:
            return None

        try:
            error_tag = page_speed_insight.ele('.lh-gauge__percentage lh-gauge--error')

            if error_tag:
                return None
            
        except Exception:
            pass

        try:
            scores_tags = page_speed_insight.eles('.lh-exp-gauge__percentage')
            

            if scores_tags[0] and scores_tags[1]:
                break
                
            # if error_tag:
            #     return None

        except Exception:
            pass

    scores = {"mobile": int(scores_tags[0].text), 
              "desktop": int(scores_tags[1].text)}

    page_speed_insight.close()

    return scores

def check_seo_v2(url: str, driver):
    site_url = f'https://thehoth.websiteauditserver.com/process-embedded.inc?type=pdf&uid=46847&behaviour=new_tab&template=0&domain={encode_text(url)}&first_name=John&email=john%40example.com'
    
    seo_checker = driver.new_tab(site_url)

    while True:
        try:
            alert = seo_checker.ele('.alert alert-danger alert-dismissible fade in m-t-20 m-b-20')

            if alert:
                seo_checker.close()
                non_pdf_link = seo_checker.url

                return non_pdf_link
            
            if "download" in seo_checker.url:
                statistic_url = seo_checker.url
                seo_checker.close()

                return statistic_url
        
            time.sleep(0.5)
        except Exception as e:
            print(e)
            seo_checker.close()
            return False

def check_responsive(url: str):
    response = requests.get(url)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all style tags and external stylesheets
    style_tags = soup.find_all('style')
    css_links = soup.find_all('link', {'rel': 'stylesheet'})
    
    # Check inline styles
    for style in style_tags:
        if '@media' in style.text:
            return "Responsive"
            
    # Check external stylesheets
    for link in css_links:
        try:
            css_url = link.get('href')
            if not css_url.startswith('http'):
                css_url = url.rstrip('/') + '/' + css_url.lstrip('/')
            css_response = requests.get(css_url)
            if '@media' in css_response.text:
                return "Responsive"
        except:
            continue
    
    return "Not responsive"

def check_accessibility(url: str):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    images = soup.find_all('img')
    missing_alt = [img for img in images if not img.get('alt')]

    headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

    if missing_alt:
        return "Missing alt attribute"
    
    if not headers or not any(h.name == 'h1' for h in headers):
        return "Missing H1 tag or missing headers structure"
    
    return "Passed"

def check_seo(url: str):
    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')

    meta_description = soup.find('meta', {'name': 'description'})
    
    # Check for robots.txt
    robots_url = f"{url.rstrip('/')}/robots.txt"
    has_robots = False
    try:
        robots_response = requests.get(robots_url)
        if robots_response.status_code == 200:
            has_robots = True
    except:
        pass

    # Check for sitemap.xml
    has_sitemap = False
    sitemap_urls = [f"{url.rstrip('/')}/sitemap.xml", 
                    f"{url.rstrip('/')}/sitemap_index.xml", 
                    f"{url.rstrip('/')}/page-sitemap.xml", 
                    f"{url.rstrip('/')}/wp-sitemap-posts-page-1.xml"]

    for sitemap_url in sitemap_urls:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"}
            sitemap_response = requests.get(sitemap_url, headers=headers)

            if sitemap_response.status_code == 200:
                has_sitemap = True
        except:
            continue

    if has_robots:
        robots_content = robots_response.text
        if 'sitemap:' in robots_content.lower():
                has_sitemap = True

    # If not robots.txt or sitemap.xml, return missing
    if not has_robots or not has_sitemap:
        missing = []
        if not has_robots:
            missing.append("robots.txt")
        if not has_sitemap:
            missing.append("sitemap")
        return f"Missing {' or '.join(missing)}"
    
    # If not meta description, return missing
    if not meta_description:
        return "Missing meta description"
    
    # If not title, return missing
    title = soup.title.string if soup.title else None
    if not title or len(title) > 60:
        return "Title is missing or too long"
    
    return "Passed"

def check_security(url: str):
    response = requests.get(url)
    headers = response.headers

    missing_headers = []
    if "Content-Security-Policy" not in headers:
        missing_headers.append("Content-Security-Policy")
    
    if "X-Content-Type-Options" not in headers:
        missing_headers.append("X-Content-Type-Options")
    
    if "X-Frame-Options" not in headers:
        missing_headers.append("X-Frame-Options")
    
    if "X-XSS-Protection" not in headers:
        missing_headers.append("X-XSS-Protection")
    
    if "Referrer-Policy" not in headers:
        missing_headers.append("Referrer-Policy")
    

    return f"Missing security headers: {', '.join(missing_headers)}" if missing_headers else "Passed"

def check_broken_links(url: str):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = [a.get('href') for a in soup.find('body').find_all('a', href=True)][:10]

    broken_links = []

    for link in links:
        try:
            r = requests.get(link, timeout=5)
            if r.status_code >= 400:
                broken_links.append(link)
        except:
            broken_links.append(link)

    return f"Found: {len(broken_links)} broken links" if broken_links else "Passed"

def check_media_format(url: str):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    images = soup.find_all('img')

    outdated_formats = ('.bmp', '.tiff', '.tif', '.cur', '.ico')
    outdated_images = []
    
    for img in images:
        src = img.get('src')
        if src:
            if any(format in src.lower() for format in outdated_formats):
                outdated_images.append(src)

    return f"Found: {len(outdated_images)} outdated images" if outdated_images else "Passed"

def count_sitemap_links(url: str):
    sitemap_urls = [f"{url.rstrip('/')}/page-sitemap.xml",
                    f"{url.rstrip('/')}/wp-sitemap-posts-page-1.xml"]
    
    for sitemap_url in sitemap_urls:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"}
            response = requests.get(sitemap_url, headers=headers)

        except Exception as e:
            print(f"Can't check sitemap for {url}: {e}")
            return "N/A"

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'xml')

        urls = []

        for url in soup.find_all('url'):
            loc = url.find('loc').text if url.find('loc') else None
            if loc:
                urls.append(loc)
            
        return len(urls)
    
    else:
        print(response.status_code)
        
        return "N/A"
 

