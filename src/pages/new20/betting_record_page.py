import allure
import requests
import re
from configparser import ConfigParser
from src.pages.new20.base_page import BasePage
from playwright.sync_api import Page

class BettingRecordPage(BasePage):
    def __init__(self, page: Page, config):
        super().__init__(page, config)

        site = config.get('DEFAULT', 'site')
        base_url = config.get(site, 'base_url')
        self.url = f"https://{base_url}/#/BettingRecord"

    @allure.step("抓取第一筆注單賠率")
    def extract_record_odd(self):
        return self.page.locator('xpath=(//li[contains(., "@")]//span[preceding-sibling::text()[contains(., "@")]])[1]').inner_text().strip()

    @allure.step("抓取第一筆注單可贏金額")
    def extract_record_payout(self):
        return self.page.locator('td.rt_betval').nth(1).inner_text().strip()

    @allure.step("抓取第一筆注單單號")
    def extract_record_ticket(self):
        element = self.page.locator('li:has-text("單號")').first
        element.wait_for(state='visible', timeout=5000)
        text = element.inner_text().strip()
        return text.split(":")[-1].strip()

    @staticmethod
    @allure.step("取得管端驗證")
    def get_agent_session(config: ConfigParser):
        base_url = config.get('agent', 'base_url')
        username = config.get('agent', 'username')
        password = config.get('agent', 'password')

        session = requests.Session()
        session.verify =False
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        })
        login_url = f"{base_url}/Home/Login"
        response_get = session.get(login_url)
        token = r'name=__RequestVerificationToken type=hidden value=([a-zA-Z0-9_-]+)'
        match = re.search(token, response_get.text)

        if not match:
            raise Exception("無法從HTML中擷取Token")
        verification_token = match.group(1)
        payload = {
            "__RequestVerificationToken": verification_token,
            "txtac": username,
            "txtpd": password
        }
        auth_url = "https://ag.supers168.com/Home/Authenticate"
        response = session.post(auth_url, data=payload)

        try:
            result = response.json()
            if result.get("status") == 1:
                return session
            else:
                raise Exception(f"登入失敗: {result.get('msg')}")
        except ValueError:
            raise Exception(f"回傳異常: {response.text}")

    @staticmethod
    @allure.step("取得控端驗證")
    def get_controller_session(config: ConfigParser):
        base_url = config.get('admin', 'base_url')
        username = config.get('admin', 'username')
        password = config.get('admin', 'password')

        session = requests.Session()
        payload = {
            "username": username,
            "password": password
        }
        login_url = f"{base_url}/api/users/authenticate"
        response = session.post(login_url, json=payload, allow_redirects=False, verify=False)
        if response.status_code != 200:
            raise Exception(f"登入失敗, {response.text}")
        return session