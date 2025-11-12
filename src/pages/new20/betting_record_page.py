import allure
from src.pages.new20.base_page import BasePage
from playwright.sync_api import Page

class BettingRecordPage(BasePage):
    def __init__(self, page: Page, config):
        super().__init__(page, config)

        site = config.get('DEFAULT', 'site')
        base_url = config.get(site, 'base_url')
        self.url = f"https://{base_url}/#/BettingRecord"

    @allure.step("抓取第一筆注單賠率")
    def get_record_odd(self):
        return self.page.locator('span.oddColor').nth(1).inner_text().strip()

    @allure.step("抓取第一筆注單可贏金額")
    def get_record_payout(self):
        return self.page.locator('td.rt_betval').nth(1).inner_text().strip()