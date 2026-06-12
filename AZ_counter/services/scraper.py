from playwright.sync_api import sync_playwright
from playwright.sync_api import Error as PlaywrightError

class ScraperError(Exception): pass
class NetworkError(ScraperError): pass
class AuthError(ScraperError): pass

LOGIN_URL = "https://auth.sberclass.ru/auth/realms/EduPowerKeycloak/protocol/openid-connect/auth?response_type=code&client_id=edupower&scope=openid%20profile%20email&redirect_uri=https://beta.sberclass.ru/services/auth/login/oauth2/code/edupower?returnTo%3Dhttps://beta.sberclass.ru/dashboard/"

class MarksScraper:
    def scrape(self, login: str, password: str, trim_num: int = None, screen_show: bool = False) -> dict:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless= not screen_show)
                page = browser.new_page()

                try:
                    page.goto(LOGIN_URL)
                except PlaywrightError:
                    raise NetworkError("Не удалось подключиться к сайту")

                self._login(page, login, password)

                self._go_to_marks(page)

                if trim_num is None:
                    trim_num = self._detect_trim(page)
                else:
                    trim_num -= 1

                marks = self._collect_marks(page, trim_num)

            finally:
                if browser:
                    browser.close()

        return marks

    @staticmethod
    def _login(page, login: str, password: str):
        page.get_by_placeholder("Логин").fill(login)
        page.get_by_placeholder("Пароль").fill(password)
        page.get_by_role("button", name="Войти", exact=True).click()

        try:
            page.locator("text=Не удалось войти в систему.").wait_for(state="visible", timeout=4000)
            raise AuthError("Не удалось войти")
        except PlaywrightError:
            pass

    @staticmethod
    def _go_to_marks(page):
        page.get_by_role("button").and_(page.locator(".primal-menu-btn")).click()
        page.locator('[href="/final-marks"]').click()
        page.wait_for_selector('[data-testid="FinalMarks.table-container"]', timeout=20000)

    @staticmethod
    def _detect_trim(page) -> int:
        rows = page.locator('div[style*="margin-left: 8px"]').all()
        for row in range(len(rows)):
            res = rows[row].locator('[data-testid*="table-cell"]').nth(0).inner_text().strip()
            if res.isdigit():
                res2 = rows[row].locator('[data-testid*="table-cell"]').nth(1).inner_text().strip()
                if res2 != "—":
                    return 1
            else:
                try:
                    float(res)
                    return 0
                except ValueError:
                    pass
        return 0

    @staticmethod
    def _collect_marks(page, trim_num:int) -> dict:
        rows = page.locator('div[style*="margin-left: 8px"]').all()
        marks = {}

        for row in rows:
            sub_name = row.locator('div[style*="min-width: 164px"]').inner_text().strip()
            cell = row.locator('[data-testid*="table-cell"]').nth(trim_num)
            marks[sub_name] = [[], ""]

            if cell.inner_text().strip() != "—":
                cell.click()
                page.wait_for_selector('.grade-block')
                for mar in page.locator('.grade-block').all_inner_texts():
                    marks[sub_name][0].append(mar.replace('\n', ''))

                skips = page.get_by_test_id("FinalMarks.period-duration-widget").inner_text()
                marks[sub_name][1] = (skips.split("·")[-1]).split()[1]
            else:
                continue
        return marks