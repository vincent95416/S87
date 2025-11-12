import allure
from time import sleep
from src.pages.spg.base_page import BasePage
from playwright.sync_api import Page, expect

class LobbyPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    @allure.step("切換遊戲菜單")
    def select_game(self, game_name: str) -> None:
        game_label = self.page.get_by_text(f'{game_name}')
        game_label.click()
        sleep(1)
        expect(game_label).to_have_class('is-active')

    @allure.step("擷取賠率")
    def extract_odd(self) -> float:
        odd = self.page.locator('.odd.pl-\\[8px\\]').first
        odd.wait_for()
        odd_string = odd.inner_text().strip()
        odd_value = float(odd_string)
        return odd_value

    @allure.step("切換為香港盤(不含本金)")
    def switch_principal(self) -> None:
        self.page.locator("div.el-select__selected-item:has-text('歐洲盤')").click()
        self.page.get_by_text("香港盤", exact=True).click()

    @allure.step("下注第一個注項")
    def bet(self) -> str:
        self.page.locator('.odd.pl-\\[8px\\]').first.click(force=True)
        self.page.locator('div.bet-action').wait_for(state='visible', timeout=1000)
        self.page.get_by_text("確認下注").dblclick()
        self.page.get_by_text("最低").wait_for(state='hidden', timeout=1000)
        self.page.get_by_text("投注成功").wait_for(state='visible', timeout=10000)
        odd_string = self.page.locator('span.font-semibold.text-base.leading-4').inner_text().strip()
        betting_odd = odd_string.replace("@","")
        # betting_payout = self.page.locator('div.infoItemVal').nth(1).inner_text().strip()
        return betting_odd

    @allure.step("擷取注單賠率")
    def get_record(self):
        self.page.get_by_text("注單紀錄").click()
        self.page.locator("button.is-active:has-text('未結算')").wait_for(state='visible', timeout=1000)
        odd_string = self.page.locator('span.font-semibold.text-[14px].leading-3.text-[--b-7].whitespace-nowrap').inner_text().strip()
        betting_odd = odd_string.replace("@", "")
        return betting_odd