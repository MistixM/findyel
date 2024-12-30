from utils.check_site import get_page_speed_number

from DrissionPage import ChromiumPage

driver = ChromiumPage()

speed = get_page_speed_number('https://pagespeed.web.dev/analysis/http-letsremotivate-com/ekopitrhu9?form_factor=mobile', driver)

print(speed['mobile'])