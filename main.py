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
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException


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
        driver.get('https://global.americanexpress.com/login')
        login_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'eliloUserID'))
        )

        send_keys_slow(login_input, login)
        send_keys_slow(driver.find_element_by_id('eliloPassword'), password)

        try:
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '#consentContainer input'))
            ).click()
        except TimeoutException:
            pass

        btn = driver.find_element_by_id('loginSubmit')
        btn.click()
        WebDriverWait(driver, 10).until(EC.staleness_of(btn))
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//h2[text()="Total balance"]'))
        )
        driver.get('https://global.americanexpress.com/offers/eligible')
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//span[text()="Amex Offers"]'))
        )

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'offer-category-menu'))
            )
        except TimeoutException as e:
            alert_xpath = '//section[@class="offers-list"]//div[contains(@class, "alert-dialog")]//p/span'
            notice = None
            try:
                notice = driver.find_element_by_xpath(alert_xpath)
            except NoSuchElementException:
                print('Notice not found')
                pass

            if not notice or notice.text != 'You currently have no available Offers. Please try again later.':
                if notice:
                    print('Unexpected notice text: "%s"' % notice.text)
                raise e

        offers = driver.find_elements_by_xpath('//section[@class="offers-list"]/section/div[@data-rowtype="offer"][.//button/span[text()="Save to Card"]]')

        if offers:
            print('Found offers: %d' % len(offers))

            driver.execute_script('return document.getElementById("lpButtonDiv").remove();')

            for offer in offers:
                details = offer.find_elements_by_xpath('.//div[contains(concat(" ", @class, " "), " offer-info ")]/p')
                bonus = details[0].text
                merchant = details[1].text

                print('%s: %s... ' % (merchant, bonus), end='')

                try:
                    element = driver.find_element_by_css_selector('#consentContainer #sprite-ContinueButton_EN')
                    if element.is_displayed():
                        element.click()
                except NoSuchElementException:
                    pass

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
