import asyncio
import re
from playwright.async_api import async_playwright
from datetime import datetime
from enum import Enum
import logging
import pandas as pd
from typing import Optional, Dict, List, Any, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DayType(Enum):
    Work = "Work"
    ChildSick = "ChildSick"
    ParentSick = "ParentSick"
    Sick = "Sick"
    SpouseSick = "SpouseSick"
    PublicHoliday = "PublicHoliday"
    ReserveDuty = "ReserveDuty"
    Vacation = "Vacation"


class NetsuiteAutomator:
    def __init__(self, user_data_dir: str, landing_page_url: str = "https://ibase1.sharepoint.com/sites/hub/il"):
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

    async def parse_timesheet_table(self) -> Optional[Dict[str, Tuple[str, Any]]]:
        """
        Parse the timesheet table on the Track Time page into a dictionary of time entries.
        
        Returns:
            Dict with date column names as keys (e.g., 'sun_24', 'tue_26') and 
            tuples of (time_text, link_locator) as values. Only includes entries where time was found.
            Example: {'sun_24': ('9:30', <playwright_locator>), 'mon_25': ('8:00', <playwright_locator>)}
        """
        try:
            if not self.page_netsuite:
                raise Exception("NetSuite page not initialized. Call start() first.")
            
            logger.info("Parsing timesheet table for time entries and links...")
            
            # Wait for the timesheet table to be present
            table_selector = "#timesheet_splits"
            await self.page_netsuite.wait_for_selector(table_selector, timeout=10000)
            
            # Get the table element
            table = self.page_netsuite.locator(table_selector)
            
            # Check if table exists
            if not await table.count():
                logger.warning("Timesheet table not found")
                return None
            
            # Get all rows
            rows = table.locator("tr")
            row_count = await rows.count()
            
            if row_count < 2:  # No data rows
                logger.info("No data rows found in timesheet table")
                return {}
            
            # Parse header row to get date columns
            header_row = rows.nth(0)
            header_cells = header_row.locator("td")
            header_count = await header_cells.count()
            
            # Map column indices to date column names
            date_column_mapping = {}  # index -> column_name
            
            for i in range(header_count):
                cell = header_cells.nth(i)
                cell_text = await cell.inner_text()
                cell_text = cell_text.strip()
                
                # Skip non-date columns (customer, task, service_item, total)
                if i < 3 or "Total" in cell_text:
                    continue
                
                # This is a date column (e.g., "Sun, 24")
                # Clean up the text to create a column name
                clean_name = re.sub(r'[^\w\s]', '', cell_text.lower().replace(' ', '_'))
                date_column_mapping[i] = clean_name
            
            logger.info(f"Found date columns: {list(date_column_mapping.values())}")
            
            # Dictionary to store the results
            time_entries = {}
            
            # Parse data rows (skip header and totals rows)
            for row_idx in range(1, row_count):
                row = rows.nth(row_idx)
                cells = row.locator("td")
                cell_count = await cells.count()
                
                # Get first cell text to check if this is a data row or totals row
                first_cell_text = await cells.nth(0).inner_text()
                first_cell_text = first_cell_text.strip()
                
                # Skip empty rows and totals row
                if not first_cell_text or "Totals" in first_cell_text:
                    continue
                
                # Process date columns for this row
                for col_idx, column_name in date_column_mapping.items():
                    if col_idx >= cell_count:
                        continue
                    
                    cell = cells.nth(col_idx)
                    cell_text = await cell.inner_text()
                    cell_text = cell_text.strip()
                    
                    # Check if there's a time entry in this cell
                    time_match = re.search(r'\d{1,2}:\d{2}', cell_text)
                    if time_match and time_match.group() != "0:00":
                        time_text = time_match.group()
                        
                        # Look for a link in this cell
                        link = cell.locator("a")
                        if await link.count() > 0:
                            # Store the time text and link locator
                            time_entries[column_name] = (time_text, link.first)
                            logger.info(f"Found time entry: {column_name} -> {time_text} with link")
                        else:
                            # Time found but no link - still store it with None as link
                            time_entries[column_name] = (time_text, None)
                            logger.info(f"Found time entry: {column_name} -> {time_text} (no link)")
            
            logger.info(f"Successfully parsed {len(time_entries)} time entries from timesheet table")
            return time_entries
            
        except Exception as e:
            logger.error(f"Error parsing timesheet table: {e}")
            raise


    def _parse_time_to_hours(self, time_str: str) -> float:
        """
        Convert time string (H:MM) to decimal hours.
        
        Args:
            time_str: Time in format "H:MM" or "HH:MM"
            
        Returns:
            float: Time in decimal hours (e.g., "9:30" -> 9.5)
        """
        try:
            if not time_str or time_str == "0:00":
                return 0.0
            
            time_match = re.match(r'(\d{1,2}):(\d{2})', time_str)
            if time_match:
                hours = int(time_match.group(1))
                minutes = int(time_match.group(2))
                return hours + (minutes / 60.0)
            
            return 0.0
        except Exception as e:
            logger.warning(f"Error parsing time string '{time_str}': {e}")
            return 0.0

    async def _select_customer_and_case(self, day_type: DayType):
        """Select appropriate customer and case based on day type (private helper method)"""
        try:
            if day_type == DayType.Work:
                # Select customer/project for work days
                await self.page_netsuite.locator("#parent_actionbuttons_customer_fs span").click()
                await self.page_netsuite.locator("#customer_popup_list").click()
                await self.page_netsuite.locator("#inner_popup_div").get_by_role("link", name="PRJ13058 Meta Platforms :").click()
                logger.info("Selected work customer/project")
                
                # Select case/task/event for work
                await self.page_netsuite.locator("#parent_actionbuttons_casetaskevent_fs span").click()
                await self.page_netsuite.locator("#casetaskevent_popup_list").click()
                await self.page_netsuite.get_by_role("link", name="Standard Time (Project Task)").click()
                logger.info("Selected work case/task/event")
            else:
                # Select Internal customer for non-work days
                await self.page_netsuite.locator("#parent_actionbuttons_customer_fs span").click()
                await self.page_netsuite.locator("#customer_popup_list").click()
                
                # Find customer containing "Internal" (case insensitive)
                internal_customer = await self.page_netsuite.locator("#inner_popup_div").get_by_role("link").filter(has_text="Internal").first.click()
                logger.info("Selected Internal customer")
                
                # Select appropriate case based on day type
                await self.page_netsuite.locator("#parent_actionbuttons_casetaskevent_fs span").click()
                await self.page_netsuite.locator("#casetaskevent_popup_list").click()
                
                # Map day types to expected text patterns
                case_mapping = {
                    DayType.ChildSick: "Child (Dependent) Sickness (Project Task)",
                    DayType.ParentSick: "Parent (dependent) Sickness (Project Task)", 
                    DayType.Sick: "Sickness (Project Task)",
                    DayType.SpouseSick: "Spouse (Project Task)",
                    DayType.PublicHoliday: "Public Holiday (Project Task)",
                    DayType.ReserveDuty: "Reserve Duty (Project Task)",
                    DayType.Vacation: "Vacation (Project Task)",
                }

                case_text = case_mapping.get(day_type, "")
                if case_text:
                    # Find case option containing the text (case insensitive)
                    case_option = self.page_netsuite.get_by_role("link", 
                                                                 name=re.compile(rf"^{re.escape(case_text)}", re.IGNORECASE)).first
                    await case_option.click()
                    logger.info(f"Selected case: {case_text}")
                else:
                    raise ValueError(f"Unknown day type: {day_type}")
                    
        except Exception as e:
            logger.error(f"Error selecting customer and case for {day_type}: {e}")
            raise

    async def fill_calculated_work_hours(self, total_hours: float):
        # Calculate start and end times based on duration
        start_hour = 7
        start_minute = 30

        # Convert duration to hours and minutes
        end_total_minutes = start_minute + (total_hours * 60)
        end_hour = start_hour + int(end_total_minutes // 60)
        end_minute = int(end_total_minutes % 60)

        start_time = f"{start_hour:02d}:{start_minute:02d}"
        end_time = f"{end_hour:02d}:{end_minute:02d}"

        # Open timesheet entry popup (either for new entry or to edit time for existing)

        popup_task = self.context.wait_for_event("page")
        await self.page_netsuite.get_by_role("link", name="Calculate").click()
        page_timespan_entry = await popup_task
        logger.info("Opened timesheet entry popup")

        # Fill in the time fields
        await page_timespan_entry.get_by_role("textbox", name="Start Time").fill(start_time)
        await page_timespan_entry.get_by_role("textbox", name="End Time").fill(end_time)

        logger.info(f"Filled start={start_time}, end={end_time}")
        await page_timespan_entry.get_by_role("textbox", name="Start Time").fill(start_time)
        await page_timespan_entry.get_by_role("textbox", name="Start Time").press("Tab")
        await page_timespan_entry.get_by_role("textbox", name="End time").fill(end_time)
        await page_timespan_entry.get_by_role("textbox", name="End time").press("Tab")
        logger.info(f"Filled time: {start_time} - {end_time} ({total_hours} hours)")
        
        # Save and close the popup
        await page_timespan_entry.get_by_role("button", name="Save").click()
        await page_timespan_entry.close()
        logger.info("Saved and closed timesheet entry popup")
    
    def _compute_date_key(self, date_obj: datetime) -> str:
        """Compute the date column key used in the timesheet table from a datetime object"""
        day_abbr = date_obj.strftime("%a").lower()
        day_num = date_obj.day
        return f"{day_abbr}_{day_num}"
    
    async def process_date(self, date_obj: datetime, duration_hours: float, day_type: DayType = DayType.Work, use_save: bool = True):
        """Process a single date entry"""
        page_timespan_entry = None
        try:
            date_str = date_obj.strftime("%d/%m/%Y")
            logger.info(f"Processing date: {date_str} for {duration_hours} hours, type: {day_type}")
            
            # Fill the date field - this will update the table to show the week containing this date
            await self.page_netsuite.get_by_role("textbox", name="Date *").fill(date_str)
            logger.info(f"Filled date: {date_str}")
            # wait for page to update
            await self.page_netsuite.wait_for_timeout(2000)

            timesheet_data = await self.parse_timesheet_table()

            date_key = self._compute_date_key(date_obj)
            if date_key in timesheet_data and timesheet_data[date_key][1] is not None:
                time_text, link_locator = timesheet_data[date_key]
                logger.info(f"Existing entry found for {date_key}: {time_text}")
                # click the link
                await link_locator.click()
                logger.info(f"Clicked existing entry link for {date_key}")
            else:
                logger.info(f"No existing entry for {date_key}")

            await self.fill_calculated_work_hours(duration_hours)
                
            await self._select_customer_and_case(day_type)
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
    
    # Use the automator as an async context manager
    async with NetsuiteAutomator(user_data_dir) as automator:
        # Start and log in
        await automator.start()
        
        # Navigate to Track Time
        await automator.goto_track_time()

        await automator.process_date(datetime(2025, 9, 3), 9.5, DayType.Work)
        await automator.process_date(datetime(2025, 9, 3), 11.5, DayType.Sick)
        await automator.process_date(datetime(2025, 9, 4), 11.5, DayType.ReserveDuty)



        
        # # Parse existing timesheet data
        # logger.info("Parsing existing timesheet data...")
        # df = await automator.parse_timesheet_table()
        
        # if df is not None and not df.empty:
        #     print("\n=== TIMESHEET DATA ===")
        #     print(df.to_string(index=False))
        # else:
        #     print("No timesheet data found or table is empty")
        
        # Pause for inspection
        await automator.pause_for_inspection("Press ENTER to close...")


# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())