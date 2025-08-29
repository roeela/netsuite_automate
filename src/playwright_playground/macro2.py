import asyncio
from playwright.async_api import async_playwright

async def run():
    user_data_dir = r"G:\Toee\playwright_sutff\browsing_profile"
    landing_page_url = "https://ibase1.sharepoint.com/sites/hub/il/SitePages/New-Hire-Checklist.aspx"

    async with async_playwright() as p:
        # Launch persistent browser context (keeps your login session)
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--start-maximized"]
        )

        # Use existing page if available, else create new
        page_qtest_portal = context.pages[0] if context.pages else await context.new_page()

        # Go to landing page
        await page_qtest_portal.goto(landing_page_url)

        # Click the "App launcher" button
        await page_qtest_portal.get_by_role("button", name="App launcher").click()

        # Wait for the first popup triggered by clicking the Netsuite list item
        async with page_qtest_portal.expect_popup() as popup_info:
            await page_qtest_portal.get_by_role("listitem", name="Netsuite will be opened in").click()
        page_netsuite = await popup_info.value

        # Navigate inside netsuite
        # goto "track time"
        await page_netsuite.get_by_role("link", name="Track Time").click() 
        # click the date picker
        await page_netsuite.get_by_role("link", name="Pick").click() 
        # select a day of month
        await page_netsuite.get_by_role("link", name="31").nth(1).click()

        # Wait for the second popup triggered by clicking "Calculate"
        async with page_netsuite.expect_popup() as popup_info2:
            await page_netsuite.get_by_role("link", name="Calculate").click()
        page_timespan_entry = await popup_info2.value

        # Fill in the time fields in the second popup
        await page_timespan_entry.get_by_role("textbox", name="Start Time").fill("07:30")
        await page_timespan_entry.get_by_role("textbox", name="Start Time").press("Tab")
        await page_timespan_entry.get_by_role("textbox", name="End time").fill("17:30")
        await page_timespan_entry.get_by_role("button", name="Save").click()

        # Pause so you can inspect the browser before it closes
        input("Press ENTER to close...")

        # Close the last page and the context (browser)
        await page_timespan_entry.close()
        await context.close()

# Run the async main function
asyncio.run(run())
