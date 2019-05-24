import time
from os import environ
from os.path import isdir
from traceback import print_exc, format_exc

import telegram
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException


def notify(message: str):
    token = environ.get('TELEGRAM_TOKEN')
    if not token:
        return
    chat_id = environ.get('TELEGRAM_CHAT_ID')
    if not chat_id:
        return
    bot = telegram.Bot(token)
    bot.send_message(chat_id=chat_id, text=message, disable_web_page_preview=True,
                     parse_mode=telegram.ParseMode.MARKDOWN)


def send_keys_slow(el, text, delay=0.1):
    for c in text:
        el.send_keys(c)
        time.sleep(delay)


def do_magic():
    login = environ['LOGIN']
    password = environ['PASSWORD']
    host = environ.get('SELENIUM_HOST', 'selenium')

    driver = webdriver.Remote(command_executor='http://%s:4444/wd/hub' % host,
                              desired_capabilities=DesiredCapabilities.CHROME)
    try:
        driver.set_window_size(1440, 900)
        driver.get('https://www.americanexpress.com/uk/')
        login_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'login-user'))
        )

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '#consentContainer input'))
        ).click()

        send_keys_slow(login_input, login)
        send_keys_slow(driver.find_element_by_id('login-password'), password)

        btn = driver.find_element_by_id('login-submit')
        btn.click()
        WebDriverWait(driver, 10).until(EC.staleness_of(btn))
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//h2[text()="Total balance"]'))
        )
        driver.get('https://global.americanexpress.com/offers/eligible')
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//span[text()="Amex Offers"]'))
        )

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'offer-category-menu'))
        )

        offers = driver.find_elements_by_xpath('//section[@class="offers-list"]/section/div[@data-rowtype="offer"][.//button/span[text()="Save to Card"]]')

        if offers:
            print('Found offers: %d' % len(offers))

            driver.execute_script('return document.getElementById("lpButtonDiv").remove();')

            for offer in offers:
                details = offer.find_elements_by_xpath('.//div[contains(concat(" ", @class, " "), " offer-info ")]/p')
                bonus = details[0].text
                merchant = details[1].text

                print('%s: %s... ' % (merchant, bonus), end='')

                btn = offer.find_element_by_xpath('.//button[@type="button"][./span]')
                btn.click()
                WebDriverWait(driver, 15).until(EC.staleness_of(btn))
                print('saved')

                notify('AMEX offer saved — %s: %s ' % (merchant, bonus))
    except WebDriverException:
        print_exc()
        notify('Exception from AmEx saver: \n```\n' + format_exc() + '\n```')
        if isdir('./screenshots'):
            filename = './screenshots/%d.png' % time.time()
            driver.save_screenshot(filename)
            print('Got exception! Screenshot saved to %s' % filename)
    finally:
        driver.quit()


if __name__ == '__main__':
    while True:
        do_magic()
        sleep = int(environ.get('RESTART_DELAY', 0))
        if sleep > 0:
            time.sleep(sleep)
        else:
            break
