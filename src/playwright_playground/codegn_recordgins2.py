import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page.goto("https://ibase1.sharepoint.com/sites/hub/il")
    page.get_by_role("button", name="App launcher").click()
    with page.expect_popup() as page1_info:
        page.get_by_role("listitem", name="Netsuite will be opened in new tab", exact=True).click()
    page1 = page1_info.value
    page1.goto("https://4619195.app.netsuite.com/app/center/card.nl?sc=-46&whence=")
    page1.get_by_role("link", name="Track Time").click()
    page1.get_by_role("textbox", name="Date *").click()
    page1.get_by_role("textbox", name="Date *").click()
    page1.get_by_role("link", name="Home").click()
    page1.get_by_role("link", name="Weekly Timesheet").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
