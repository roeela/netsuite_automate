from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Launch browser with a persistent user profile
    user_data_dir = r"G:\Toee\playwright_sutff\browsing_profile"  # choose a folder
    landing_page_url = "https://ibase1.sharepoint.com/sites/hub/il/SitePages/New-Hire-Checklist.aspx"
    browser = p.chromium.launch_persistent_context(
        user_data_dir,
        headless=False,
        args=["--start-maximized"]
    )
    page = browser.pages[0] if browser.pages else browser.new_page()

    page.goto(landing_page_url)
    input("Press ENTER to close...")

