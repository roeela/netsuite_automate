import asyncio
from playwright.async_api import async_playwright


from datetime import datetime


async def run():
    user_data_dir = r"G:\Toee\netsuite_automate\browsing_profile"
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

        # Netsuite opens in a new popup
        popup_task = context.wait_for_event("page")
        await page_qtest_portal.get_by_role("listitem", name="Netsuite will be opened in").click()
        page_netsuite = await popup_task

        # Navigate inside netsuite
        # goto "track time"
        await page_netsuite.get_by_role("link", name="Track Time").click()

        # test some dates
        example_dates = [datetime(2025, 7, 23), datetime(2025, 8, 15), datetime(2025, 9, 27)]
        for sample_date in example_dates:
            date_str = sample_date.strftime("%d/%m/%Y")
            await page_netsuite.get_by_role("textbox", name="Date *").fill(date_str)

        # Timesheet entry opens in a new popup
        popup_task2 = context.wait_for_event("page")
        await page_netsuite.get_by_role("link", name="Calculate").click()
        page_timespan_entry = await popup_task2

        # Fill in the time fields
        await page_timespan_entry.get_by_role("textbox", name="Start Time").fill("07:30")
        await page_timespan_entry.get_by_role("textbox", name="Start Time").press("Tab")
        await page_timespan_entry.get_by_role("textbox", name="End time").fill("17:30")
        await page_timespan_entry.get_by_role("button", name="Save").click()

        # Pause so you can inspect the browser before it closes
        input("Press ENTER to close...")

        # Cleanup
        await page_timespan_entry.close()
        await context.close()

# Run the async main function
asyncio.run(run())
