import allure
from new20.pages.base_page import BasePage
from playwright.sync_api import Page

class BettingRecordPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.url = "https://queen168.net/#/BettingRecord"
    @allure.step("抓取第一筆注單賠率")
    def get_record_odd(self):
        return self.page.locator('span.oddColor').nth(1).inner_text().strip()
    @allure.step("抓取第一筆注單可贏金額")
    def get_record_payout(self):
        return self.page.locator('td.rt_betval').nth(1).inner_text().strip()