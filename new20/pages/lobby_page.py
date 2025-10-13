import allure
from new20.pages.base_page import BasePage
from playwright.sync_api import Page, expect
from concurrent.futures import Future
from new20.pages.betting_record_page import BettingRecordPage

class LobbyPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    @allure.step("導航至lobby page")
    def navigate_to_betting_records(self) -> BettingRecordPage:
        """這個同步回調函數會設置 Future 的結果。"""
        def handle_new_page(future: Future):
            def on_page(new_page):
                if not future.done():
                    print(f"✅ 擷取到新頁面: {new_page.url}")
                    future.set_result(new_page)

            return on_page
        # 1. 建立一個同步的等待任務
        future = Future()
        # new20. 註冊事件監聽器，當新頁面出現時，會自動設定 future 的結果
        on_page_handler = handle_new_page(future)
        self.page.context.on("page", on_page_handler)
        try:
            self.page.get_by_text("投注記錄").wait_for()
            self.page.get_by_text("投注記錄").click()
            record_page = future.result(timeout=10)
            record_page.wait_for_load_state("networkidle", timeout=5000)

            betting_record_page = BettingRecordPage(record_page)
        except TimeoutError:
            raise Exception("事件處理器超時")
        finally:
            self.page.context.remove_listener("page", on_page_handler)
        return betting_record_page

    @allure.step("切換遊戲菜單")
    def select_game(self, game_name: str) -> None:
        self.page.locator(f'.cat-name:has-text("{game_name}")').wait_for(state='visible', timeout=5000)
        self.page.locator(f'.cat-name:has-text("{game_name}")').click()
        target = self.page.locator('.leftArrow')
        expect(target).to_have_text(game_name)

    @allure.step("擷取賠率")
    def extract_odd(self) -> float:
        odd = self.page.locator('.Odd').first
        odd.wait_for()
        odd_string = odd.inner_text().strip()
        odd_value = float(odd_string)
        return odd_value

    @allure.step("切換為不含本金")
    def switch_principal(self) -> None:
        self.page.locator("div.dropDown.el-dropdown").first.click()
        self.page.get_by_text("不含本金", exact=True).click()

    @allure.step("下注第一個注項")
    def bet(self) -> tuple[str, str]:
        self.page.locator('.Odd').first.click(force=True)
        self.page.locator('div.cardHeaderRow').wait_for(state='visible', timeout=1000)
        self.page.locator('.submitBtn:has-text(" 確認下注 ")').dblclick()
        self.page.locator('div.chipsBar').wait_for(state='hidden', timeout=1000)
        self.page.locator('.submitBtn:has-text(" 確認下注 ")').click()
        self.page.get_by_text(" 交易成功 ").wait_for(state='visible', timeout=10000)
        betting_odd = self.page.locator('div.playBetOdd').inner_text().strip()
        betting_payout = self.page.locator('div.infoItemVal').nth(1).inner_text().strip()
        return betting_odd, betting_payout