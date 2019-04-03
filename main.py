import time
from os import environ

import telegram
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


def quit(prompt: str):
    print(prompt)
    sleep = int(environ.get('RESTART_DELAY', 0))
    if sleep > 0:
        time.sleep(sleep)
        exit(1)
    exit(0)


def notify(offer_info: str):
    token = environ.get('TELEGRAM_TOKEN')
    if not token:
        return
    chat_id = environ.get('TELEGRAM_CHAT_ID')
    if not chat_id:
        return
    bot = telegram.Bot(token)
    bot.send_message(chat_id=chat_id, text='AMEX offer saved — ' + offer_info, disable_web_page_preview=True,
                     parse_mode=telegram.ParseMode.MARKDOWN)


if __name__ == '__main__':
    login = environ['LOGIN']
    password = environ['PASSWORD']
    host = environ.get('SELENIUM_HOST', 'selenium')

    driver = webdriver.Remote(command_executor='http://%s:4444/wd/hub' % host,
                              desired_capabilities=DesiredCapabilities.CHROME)
    driver.get('https://www.americanexpress.com/uk/')
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, 'login-user'))
    ).send_keys(login)
    driver.find_element_by_id('login-password').send_keys(password)

    try:
        driver.find_element_by_css_selector('#consentContainer input').click()
    except:
        pass

    driver.find_element_by_id('login-submit').click()
    time.sleep(1)
    driver.get('https://global.americanexpress.com/offers/eligible')
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//span[text()="Amex Offers"]'))
    )

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'offer-category-menu'))
    )

    offers = driver.find_elements_by_xpath('//section[@class="offers-list"]/section/div[@role="heading"]')

    print('Found offers: %d' % len(offers))

    for offer in offers:
        details = offer.find_elements_by_xpath('.//div[contains(concat(" ", @class, " "), " offer-info ")]/p')
        bonus = details[0].text
        merchant = details[1].text

        print('%s: %s... ' % (merchant, bonus), end='')

        btn = offer.find_element_by_xpath('.//button[@type="button"][./span]')
        btn.click()
        WebDriverWait(driver, 15).until(EC.staleness_of(btn))
        print('saved')

        notify('%s: %s ' % (merchant, bonus))

    quit('Finished')
