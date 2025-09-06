Record




1
import re
2
from playwright.sync_api import Playwright, sync_playwright, expect
3
​
4
​
5
def run(playwright: Playwright) -> None:
6
    browser = playwright.chromium.launch(headless=False)
7
    context = browser.new_context()
8
    page.goto("https://ibase1.sharepoint.com/sites/hub/il")
9
    page.get_by_role("button", name="App launcher").click()
10
    with page.expect_popup() as page1_info:
11
        page.get_by_role("listitem", name="Netsuite will be opened in new tab", exact=True).click()
12
    page1 = page1_info.value
13
    page1.goto("https://4619195.app.netsuite.com/app/center/card.nl?sc=-46&whence=")
14
    page1.get_by_role("link", name="Home").click()
15
    page1.get_by_role("link", name="Track Time").click()
16
    page1.locator("#next").click()
17
    with page1.expect_popup() as page2_info:
18
        page1.get_by_role("link", name="Calculate").click()
19
    page2 = page2_info.value
20
    page2.get_by_role("textbox", name="Start Time").click()
21
    page2.get_by_role("textbox", name="Start Time").fill("07:30")
22
    page2.get_by_role("textbox", name="Start Time").press("Tab")
23
    page2.get_by_role("textbox", name="End time").fill("16:30")
24
    page2.get_by_role("textbox", name="End time").press("Tab")
25
    page2.get_by_role("button", name="Save").click()
26
    page2.close()
27
    page1.locator("#parent_actionbuttons_customer_fs span").click()
28
    page1.locator("#customer_popup_list").click()
29
    page1.get_by_role("link", name="PRJ13058 Meta Platforms :").click()
30
    page1.locator("#parent_actionbuttons_casetaskevent_fs span").click()
31
    page1.locator("#casetaskevent_popup_list").click()
32
    page1.get_by_role("link", name="Standard Time (Project Task)").click()
33
    page1.locator("#btn_secondarymultibutton_submitter").click()
34
    page1.get_by_role("link", name=":00").click()
35
    with page1.expect_popup() as page3_info:
36
        page1.get_by_role("link", name="Calculate").click()
37
    page3 = page3_info.value
38
    page3.get_by_role("textbox", name="End time").dblclick()
39
    page3.get_by_role("textbox", name="End time").press("Home")
40
    page3.get_by_role("textbox", name="End time").press("Shift+End")
41
    page3.get_by_role("textbox", name="End time").fill("07:30")
42
    page3.get_by_role("textbox", name="End time").press("Tab")
43
    page3.get_by_role("button", name="Save").click()
44
    page3.close()
45
    page1.locator("#btn_secondarymultibutton_submitter").click()
46
    page1.get_by_role("link", name="Pick").click()
47
    page1.get_by_role("link", name="7", exact=True).click()
48
    with page1.expect_popup() as page4_info:
49
        page1.get_by_role("link", name="Calculate").click()
50
    page4 = page4_info.value
51
    page4.get_by_role("textbox", name="Start Time").click()
52
    page4.get_by_role("textbox", name="Start Time").fill("07:30")
53
    page4.get_by_role("textbox", name="Start Time").press("Tab")
54
    page4.get_by_role("textbox", name="End time").fill("16:30")
