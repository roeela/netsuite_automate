import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page.goto("https://ibase1.sharepoint.com/sites/hub/il/SitePages/New-Hire-Checklist.aspx")
    page.get_by_role("button", name="App launcher").click()
    page.get_by_role("searchbox", name="Find Microsoft 365 apps").click()
    page.get_by_role("searchbox", name="Search all your Microsoft 365").fill("netsuite")
    with page.expect_popup() as page1_info:
        page.get_by_role("listitem", name="Netsuite will be opened in new tab", exact=True).click()
    page1 = page1_info.value
    page1.goto("https://4619195.app.netsuite.com/app/center/card.nl?sc=-46&whence=")
    page1.get_by_role("link", name="Track Time").click()
    page1.get_by_role("textbox", name="Date *").dblclick()
    page1.get_by_role("textbox", name="Date *").press("Home")
    page1.get_by_role("textbox", name="Date *").press("Shift+End")
    page1.get_by_role("textbox", name="Date *").fill("31/8/2025")
    with page1.expect_popup() as page2_info:
        page1.get_by_role("link", name="Calculate").click()
    page2 = page2_info.value
    page2.get_by_role("textbox", name="Start Time").click()
    page2.get_by_role("textbox", name="Start Time").fill("07:30")
    page2.get_by_role("textbox", name="Start Time").press("Tab")
    page2.get_by_role("textbox", name="End time").fill("17:00")
    page2.get_by_role("textbox", name="End time").press("Tab")
    page2.get_by_role("button", name="Save").click()
    page2.close()
    page1.locator("#parent_actionbuttons_customer_fs span").click()
    page1.locator("#customer_popup_list").click()
    page1.locator("#inner_popup_div").get_by_role("link", name="PRJ13058 Meta Platforms :").click()
    page1.locator("#parent_actionbuttons_casetaskevent_fs span").click()
    page1.locator("#casetaskevent_popup_list").click()
    page1.get_by_role("link", name="Standard Time (Project Task)").click()
    page1.locator("#btn_multibutton_submitter").click()
    page1.get_by_role("button", name="OK").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
