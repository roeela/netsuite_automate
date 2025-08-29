import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NetsuiteAutomator:
    def __init__(self, user_data_dir: str, landing_page_url: str):
        self.user_data_dir = user_data_dir
        self.landing_page_url = landing_page_url
        self.playwright = None
        self.context = None
        self.page_qtest_portal = None
        self.page_netsuite = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.playwright = await async_playwright().start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def start(self):
        """Initialize browser and log in to the site, navigate to NetSuite"""
        try:
            logger.info("Starting browser and logging in...")
            
            # Launch persistent browser context (keeps your login session)
            self.context = await self.playwright.chromium.launch_persistent_context(
                self.user_data_dir,
                headless=False,
                args=["--start-maximized"]
            )

            # Use existing page if available, else create new
            self.page_qtest_portal = self.context.pages[0] if self.context.pages else await self.context.new_page()

            # Go to landing page
            await self.page_qtest_portal.goto(self.landing_page_url)
            logger.info("Navigated to landing page")

            # Click the "App launcher" button
            await self.page_qtest_portal.get_by_role("button", name="App launcher").click()
            logger.info("Clicked App launcher")

            # Click on the search box and search for NetSuite
            await self.page_qtest_portal.get_by_role("searchbox", name="Find Microsoft 365 apps").click()
            await self.page_qtest_portal.get_by_role("searchbox", name="Search all your Microsoft 365").fill("netsuite")
            logger.info("Searched for NetSuite")

            # NetSuite opens in a new popup
            popup_task = self.context.wait_for_event("page")
            await self.page_qtest_portal.get_by_role("listitem", name="Netsuite will be opened in new tab", exact=True).click()
            self.page_netsuite = await popup_task
            
            # Wait for NetSuite to fully load and complete login redirects
            logger.info("Waiting for NetSuite to load completely...")
            
            # Wait for the page to stabilize using a polling approach
            max_attempts = 60  # 60 seconds max
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    current_url = self.page_netsuite.url
                    logger.info(f"Current URL: {current_url}")
                    
                    if "app.netsuite.com/app/center" in current_url:
                        logger.info("NetSuite loaded successfully!")
                        break
                        
                    await asyncio.sleep(1)
                    attempt += 1
                    
                except Exception as e:
                    logger.warning(f"Error checking URL: {e}")
                    await asyncio.sleep(1)
                    attempt += 1
            
            if attempt >= max_attempts:
                logger.warning("NetSuite may not have loaded completely, but proceeding...")
            
            # Give it a moment to settle
            await asyncio.sleep(2)
            logger.info("NetSuite page opened")
            
        except Exception as e:
            logger.error(f"Error during startup: {e}")
            raise
    
    async def goto_track_time(self):
        """Navigate to the Track Time page in NetSuite"""
        try:
            if not self.page_netsuite:
                raise Exception("NetSuite page not initialized. Call start() first.")
            
            logger.info("Navigating to Track Time page...")
            await self.page_netsuite.get_by_role("link", name="Track Time").click()
            logger.info("Successfully navigated to Track Time page")
            
        except Exception as e:
            logger.error(f"Error navigating to Track Time: {e}")
            raise
    
    async def do_stuff(self):
        """Perform timesheet entry operations"""
        try:
            logger.info("Starting timesheet operations...")
            
            # Test some dates
            example_dates = [datetime(2025, 7, 23), datetime(2025, 8, 15), datetime(2025, 9, 27)]
            
            for sample_date in example_dates:
                await self._process_date(sample_date)
                
            logger.info("All timesheet operations completed")
            
        except Exception as e:
            logger.error(f"Error during timesheet operations: {e}")
            raise
    
    async def _process_date(self, date_obj: datetime, start_time: str = "07:30", end_time: str = "17:00"):
        """Process a single date entry (private method)"""
        page_timespan_entry = None
        try:
            date_str = date_obj.strftime("%d/%m/%Y")
            logger.info(f"Processing date: {date_str}")
            
            # Fill the date field
            await self.page_netsuite.get_by_role("textbox", name="Date *").fill(date_str)
            logger.info(f"Filled date: {date_str}")
            
            # Open timesheet entry popup
            popup_task = self.context.wait_for_event("page")
            await self.page_netsuite.get_by_role("link", name="Calculate").click()
            page_timespan_entry = await popup_task
            logger.info("Opened timesheet entry popup")
            
            # Fill in the time fields
            await page_timespan_entry.get_by_role("textbox", name="Start Time").click()
            await page_timespan_entry.get_by_role("textbox", name="Start Time").fill(start_time)
            await page_timespan_entry.get_by_role("textbox", name="Start Time").press("Tab")
            await page_timespan_entry.get_by_role("textbox", name="End time").fill(end_time)
            await page_timespan_entry.get_by_role("textbox", name="End time").press("Tab")
            logger.info(f"Filled time: {start_time} - {end_time}")
            
            # Save and close the popup
            await page_timespan_entry.get_by_role("button", name="Save").click()
            await page_timespan_entry.close()
            logger.info("Saved and closed timesheet entry popup")
            
            # Select customer/project
            await self.page_netsuite.locator("#parent_actionbuttons_customer_fs span").click()
            await self.page_netsuite.locator("#customer_popup_list").click()
            await self.page_netsuite.locator("#inner_popup_div").get_by_role("link", name="PRJ13058 Meta Platforms :").click()
            logger.info("Selected customer/project")
            
            # Select case/task/event
            await self.page_netsuite.locator("#parent_actionbuttons_casetaskevent_fs span").click()
            await self.page_netsuite.locator("#casetaskevent_popup_list").click()
            await self.page_netsuite.get_by_role("link", name="Standard Time (Project Task)").click()
            logger.info("Selected case/task/event")
            
            # Submit the entry
            await self.page_netsuite.locator("#btn_multibutton_submitter").click()
            await self.page_netsuite.get_by_role("button", name="OK").click()
            logger.info("Submitted timesheet entry")
            
            logger.info(f"Completed processing for {date_str}")
            
        except Exception as e:
            logger.error(f"Error processing date {date_obj}: {e}")
            # Try to close any open popups
            try:
                if page_timespan_entry:
                    await page_timespan_entry.close()
            except:
                pass
            raise
    
    async def _fill_timesheet_entry(self, page_timespan_entry, start_time: str, end_time: str):
        """Fill timesheet entry with time values (private method)"""
        try:
            logger.info(f"Filling timesheet entry: {start_time} - {end_time}")
            
            # Fill start time
            await page_timespan_entry.get_by_role("textbox", name="Start Time").fill(start_time)
            await page_timespan_entry.get_by_role("textbox", name="Start Time").press("Tab")
            
            # Fill end time
            await page_timespan_entry.get_by_role("textbox", name="End time").fill(end_time)
            
            # Save the entry
            await page_timespan_entry.get_by_role("button", name="Save").click()
            
            # Wait for save to complete
            await asyncio.sleep(2)
            logger.info("Timesheet entry saved successfully")
            
        except Exception as e:
            logger.error(f"Error filling timesheet entry: {e}")
            raise
    
    async def pause_for_inspection(self, message: str = "Press ENTER to continue..."):
        """Pause execution for manual inspection"""
        input(message)
    
    async def close(self):
        """Close all browser resources"""
        try:
            if self.context:
                await self.context.close()
                logger.info("Browser context closed")
            if self.playwright:
                await self.playwright.stop()
                logger.info("Playwright stopped")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main():
    """Main function to run the automation"""
    user_data_dir = r"G:\Toee\netsuite_automate\browsing_profile"
    landing_page_url = "https://ibase1.sharepoint.com/sites/hub/il/SitePages/New-Hire-Checklist.aspx"
    
    # Use the automator as an async context manager
    async with NetsuiteAutomator(user_data_dir, landing_page_url) as automator:
        # Start and log in
        await automator.start()
        
        # Navigate to Track Time
        await automator.goto_track_time()
        
        # Perform timesheet operations
        await automator.do_stuff()
        
        # Pause for inspection
        await automator.pause_for_inspection("Press ENTER to close...")


# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())