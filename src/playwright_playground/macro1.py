import asyncio
from playwright.async_api import async_playwright

async def run():
    user_data_dir = r"G:\Toee\playwright_sutff\browsing_profile"
    landing_page_url = "https://ibase1.sharepoint.com/sites/hub/il/SitePages/New-Hire-Checklist.aspx"

    async with async_playwright() as p:
        # Launch persistent context (this is a BrowserContext)
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--start-maximized"]
        )

        # Get the first page or create a new one
        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate and interact
        await page.goto(landing_page_url)
        await page.get_by_role("button", name="App launcher").click()

        async with page.expect_popup() as page1_info:
            await page.get_by_role("listitem", name="Netsuite will be opened in").click()
        page1 = await page1_info.value

        await page1.get_by_role("link", name="Track Time").click()
        await page1.get_by_role("link", name="Pick").click()
        await page1.get_by_role("link", name="31").nth(1).click()

        async with page1.expect_popup() as page2_info:
            await page1.get_by_role("link", name="Calculate").click()
        page2 = await page2_info.value

        await page2.get_by_role("textbox", name="Start Time").click()
        await page2.get_by_role("textbox", name="Start Time").fill("07:30")
        await page2.get_by_role("textbox", name="Start Time").press("Tab")
        await page2.get_by_role("textbox", name="End time").fill("17:30")
        await page2.get_by_role("button", name="Save").click()

        # Pause to inspect
        input("Press ENTER to close...")

        # Close pages and context
        await page2.close()
        await context.close()

# Run the async main
asyncio.run(run())
