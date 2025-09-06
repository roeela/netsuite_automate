from enum import Enum
from playwright.async_api import BrowserContext, Page
import asyncio
from typing import Optional, List, Union
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PageState(Enum):
    """Enumeration of possible page states in the navigation flow"""
    LOGIN_PAGE = "login"
    QT_HOME_PAGE = "qt_home"
    NETSUITE_HOME_PAGE = "netsuite_home"
    TIME_TRACKING_PAGE = "time_tracking"
    WEEKLY_SHEET_PAGE = "weekly_sheet"
    UNKNOWN = "unknown"


login_page_url_pattern = "login.microsoftonline.com"
netsuite_home_url_pattern = "app.netsuite.com/app/center/card"
time_tracking_url_pattern = "app.netsuite.com/app/accounting/transactions/timebill"
weekly_sheet_url_pattern = "app.netsuite.com/app/accounting/transactions/time/weeklytimebill"
qt_home_url_pattern = "ibase1.sharepoint.com/sites/hub/il"

qt_home_target_url = 'https://ibase1.sharepoint.com/sites/hub/il'


class NetsuiteNavigator:
    """
    Navigator class for automating navigation between different pages in the NetSuite workflow
    """
    
    def __init__(self, context: BrowserContext):
        """
        Initialize the navigator with a playwright browser context
        
        Args:
            context: An already opened playwright browser context
        """
        self.context = context
        self.page_qtest_portal: Optional[Page] = None
        self.page_netsuite: Optional[Page] = None
        self._current_page: Optional[Page] = None
    
    async def get_current_page(self) -> PageState:
        """
        Determine the current page state based on the active page URL
        
        Returns:
            PageState: The current page state as an enumerated type
        """
        # Get the active page from context
        pages = self.context.pages
        if not pages:
            return PageState.UNKNOWN
        
        # Use the most recently active page
        active_page = pages[-1]
        self._current_page = active_page
        current_url = active_page.url
        
        # Identify the page based on URL patterns
        if login_page_url_pattern in current_url:
            return PageState.LOGIN_PAGE
        elif qt_home_url_pattern in current_url:
            self.page_qtest_portal = active_page
            return PageState.QT_HOME_PAGE
        elif netsuite_home_url_pattern in current_url:
            self.page_netsuite = active_page
            return PageState.NETSUITE_HOME_PAGE
        elif time_tracking_url_pattern in current_url:
            self.page_netsuite = active_page
            return PageState.TIME_TRACKING_PAGE
        elif weekly_sheet_url_pattern in current_url:
            self.page_netsuite = active_page
            return PageState.WEEKLY_SHEET_PAGE
        
        return PageState.UNKNOWN
    
    async def go_to_page(self, target_state: PageState) -> Page:
        """
        Navigate to the specified page state from the current state
        
        Args:
            target_state: The desired page state to navigate to
            
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        current_state = await self.get_current_page()
        
        if current_state == target_state:
            logging.info(f"Already on target page: {target_state.value}")
            return self._current_page
        
        try:
            return await self._navigate_from_to(current_state, target_state)
        except Exception as e:
            logging.error(f"Navigation failed from {current_state.value} to {target_state.value}: {str(e)}")
            return None
    
    async def _navigate_to_qt_home(self) -> None:
        """
        Handle navigation from unknown state by first going to Qualitest home page
        
        Args:
            target_state: The desired target state
            
        Returns:
            bool: True if navigation was successful
        """
        logger.info("Starting from unknown state. Navigating to Qualitest home page...")
        
        # Get the active page or create a new one if none exists
        pages = self.context.pages
        if not pages:
            # Create a new page if none exists
            page = await self.context.new_page()
        else:
            page = pages[0]  # Use the first available page
        
        self._current_page = page
        
        # Navigate to Qualitest home page
        await page.goto(qt_home_target_url)
        await self.wait_for_page_load([qt_home_url_pattern, login_page_url_pattern], timeout_seconds=10)
        
        # Check what state we ended up in
        current_state = await self.get_current_page()
        
        if current_state == PageState.LOGIN_PAGE:
            logger.info("Landed on login page. User needs to complete authentication.")
            # If we need to go to QT home and we're on login, handle login

            await self.wait_for_page_load(qt_home_url_pattern, timeout_seconds=300)  # wait up to 5 minutes for user to login
            current_state = await self.get_current_page()
            if current_state != PageState.QT_HOME_PAGE:
                logger.error("Failed to reach Qualitest home page after login.")
                return False
                
        else:
            assert current_state == PageState.QT_HOME_PAGE # should not be anything else
            logger.info("Successfully landed on Qualitest home page.")


    async def _navigate_from_to(self, from_state: PageState, to_state: PageState) -> Page:
        """
        Internal method to handle navigation logic between states
        
        Args:
            from_state: Current page state
            to_state: Target page state
            
        Returns:
            bool: True if navigation was successful
        """
        logging.info(f"Navigating from {from_state.value} to {to_state.value}...")
        if from_state == PageState.LOGIN_PAGE:
            await self._handle_login_navigation(to_state)
        elif from_state == PageState.QT_HOME_PAGE:
            await self._navigate_from_qt_home(to_state)
        elif from_state == PageState.NETSUITE_HOME_PAGE:
            await self._navigate_from_netsuite_home(to_state)
        elif from_state in [PageState.TIME_TRACKING_PAGE, PageState.WEEKLY_SHEET_PAGE]:
            await self._navigate_from_netsuite_subpage(to_state)
        elif from_state == PageState.UNKNOWN:
            await self._navigate_to_qt_home()
            await self._navigate_from_to(PageState.QT_HOME_PAGE, to_state)
        else:
            logging.error(f"Unknown current state: {from_state.value}")
            return None
        
        return self._current_page
    
    async def _handle_login_navigation(self, target_state: PageState) -> bool:
        """
        Handle navigation from login page (requires manual user authentication)
        
        Args:
            target_state: The desired target state
            
        Returns:
            bool: True if login was completed and navigation proceeded
        """
        logging.info("Currently on login page. Waiting for user to complete authentication...")
        
        # Wait for the user to complete login (URL should change from login.microsoftonline.com)
        try:
            await self._current_page.wait_for_url(
                lambda url: "login.microsoftonline.com" not in url,
                timeout=300000  # 5 minutes timeout
            )
            logging.info("Login completed. Continuing navigation...")
            
            # After login, determine new state and continue navigation
            new_state = await self.get_current_page()
            if new_state == target_state:
                return True
            else:
                return await self._navigate_from_to(new_state, target_state)
                
        except Exception as e:
            logging.error(f"Login timeout or error: {str(e)}")
            return False
    
    async def _navigate_from_qt_home(self, target_state: PageState) -> bool:
        """
        Navigate from QT home page to target state
        
        Args:
            target_state: The desired target state
            
        Returns:
            bool: True if navigation was successful
        """
        if target_state == PageState.QT_HOME_PAGE:
            return True
        
        # For any NetSuite-related target, first go to NetSuite home
        if target_state in [PageState.NETSUITE_HOME_PAGE, PageState.TIME_TRACKING_PAGE, PageState.WEEKLY_SHEET_PAGE]:
            success = await self._go_to_netsuite_from_qt_home()
            if not success:
                return False
            
            # If we just wanted NetSuite home, we're done
            if target_state == PageState.NETSUITE_HOME_PAGE:
                return True
            
            # Otherwise, continue navigation from NetSuite home
            return await self._navigate_from_netsuite_home(target_state)
        
        return False
    
    async def _go_to_netsuite_from_qt_home(self) -> bool:
        """
        Navigate from QT home page to NetSuite home page
        
        Returns:
            bool: True if navigation was successful
        """
        try:
            # Click the "App launcher" button
            await self.page_qtest_portal.get_by_role("button", name="App launcher").click()
            
            # Click on the search box and search for NetSuite
            await self.page_qtest_portal.get_by_role("searchbox", name="Find Microsoft 365 apps").click()
            await self.page_qtest_portal.get_by_role("searchbox", name="Search all your Microsoft 365").fill("netsuite")
            
            # NetSuite opens in a new popup
            popup_task = self.context.wait_for_event("page")
            await self.page_qtest_portal.get_by_role("listitem", name="Netsuite will be opened in new tab", exact=True).click()
            self.page_netsuite = await popup_task
            
            # Wait for NetSuite page to load
            await self.page_netsuite.wait_for_load_state("networkidle")
            
            # Verify we're on NetSuite home page
            current_state = await self.get_current_page()
            return current_state == PageState.NETSUITE_HOME_PAGE
            
        except Exception as e:
            logging.error(f"Failed to navigate to NetSuite from QT home: {str(e)}")
            return False
    
    async def _navigate_from_netsuite_home(self, target_state: PageState) -> bool:
        """
        Navigate from NetSuite home page to target state
        
        Args:
            target_state: The desired target state
            
        Returns:
            bool: True if navigation was successful
        """
        if target_state == PageState.NETSUITE_HOME_PAGE:
            return True
        
        try:
            if target_state == PageState.TIME_TRACKING_PAGE:
                await self.page_netsuite.get_by_role("link", name="Track Time").click()
                await self.wait_for_page_load(time_tracking_url_pattern, timeout_seconds=10)
                return await self.get_current_page() == PageState.TIME_TRACKING_PAGE
                
            elif target_state == PageState.WEEKLY_SHEET_PAGE:
                await self.page_netsuite.get_by_role("link", name="Weekly Timesheet").click()
                await self.wait_for_page_load(weekly_sheet_url_pattern, timeout_seconds=10)
                return await self.get_current_page() == PageState.WEEKLY_SHEET_PAGE
            
        except Exception as e:
            logging.error(f"Failed to navigate from NetSuite home to {target_state.value}: {str(e)}")
            return False
        
        return False
    
    async def _navigate_from_netsuite_subpage(self, target_state: PageState) -> bool:
        """
        Navigate from NetSuite subpages (Time Tracking or Weekly Sheet) to target state
        
        Args:
            target_state: The desired target state
            
        Returns:
            bool: True if navigation was successful
        """
        current_state = await self.get_current_page()
        
        if current_state == target_state:
            return True
        
        # If we need to go to QT home, we might need to go back through browser history
        # or navigate to a different context
        if target_state == PageState.QT_HOME_PAGE:
            if self.page_qtest_portal:
                await self.page_qtest_portal.bring_to_front()
                return True
            else:
                logging.error("QT portal page reference lost. Cannot navigate back to QT home.")
                return False
        
        # For NetSuite home page, navigate back using Home link
        elif target_state == PageState.NETSUITE_HOME_PAGE:
            try:
                await self.page_netsuite.get_by_role("link", name="Home").click()
                
                # Wait for URL to settle on NetSuite home pattern
                await self.wait_for_page_load(netsuite_home_url_pattern, timeout_seconds=10)
                return True
                
            except Exception as e:
                logging.error(f"Failed to navigate back to NetSuite home: {str(e)}")
                return False
        
        # For other NetSuite subpages, go through NetSuite home
        elif target_state in [PageState.TIME_TRACKING_PAGE, PageState.WEEKLY_SHEET_PAGE]:
            # First go to NetSuite home, then to target
            logging.info(f"Navigating back to NetSuite home before going to {target_state.value}...")
            if await self._navigate_from_netsuite_subpage(PageState.NETSUITE_HOME_PAGE):
                return await self._navigate_from_netsuite_home(target_state)
        
        return False
    
    async def wait_for_page_load(self, url_strings_to_wait_for: Union[str, List[str]], timeout_seconds: int = 10) -> None:
        time_counter = 0

        if isinstance(url_strings_to_wait_for, str):
            url_strings_to_wait_for = [url_strings_to_wait_for]
        
        while time_counter < timeout_seconds:
            try:
                current_url = self._current_page.url
                logger.info(f"Current URL: {current_url}")

                for url_string_to_wait_for in url_strings_to_wait_for:
                    if url_string_to_wait_for in current_url:
                        logger.info("page loaded successfully!")
                        return
                    
                await asyncio.sleep(1)
                time_counter += 1
                
            except Exception as e:
                logger.warning(f"Error checking URL: {e}")
                await asyncio.sleep(1)
                time_counter += 1

        if url_string_to_wait_for not in self._current_page.url:
            raise TimeoutError(f"Timeout waiting for URL to contain '{url_string_to_wait_for}'")
        
    @property
    def current_page(self) -> Optional[Page]:
        return self._current_page


# Example usage
async def example_usage():
    """
    Example of how to use the NetsuiteNavigator with persistent user context
    """
    from playwright.async_api import async_playwright
    import platformdirs
    import os
    
    # Set up persistent user data directory
    user_data_dir = platformdirs.user_data_dir()
    context_dir = os.path.join(user_data_dir, "netsuite_nav_test")
    
    # Create directory if it doesn't exist
    os.makedirs(context_dir, exist_ok=True)
    
    logging.info(f"Using persistent context directory: {context_dir}")
    
    async with async_playwright() as p:
        # Launch browser with persistent context
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=context_dir,
            headless=False,
            # Optional: Set viewport size
            viewport={'width': 1920, 'height': 1080},
            # Optional: Accept downloads
            accept_downloads=True,
            # Optional: Bypass CSP
            bypass_csp=True,
        )
        
        # Get the default context (persistent context acts as both browser and context)
        context = browser
        
        # Initialize the navigator
        navigator = NetsuiteNavigator(context)
        
        # Check current page
        current_state = await navigator.get_current_page()
        logger.info(f"Current page state: {current_state.value}")
        
        # # Example navigation sequence
        # if current_state == PageState.LOGIN_PAGE:
        #     logger.info("Please complete the login process in the browser...")
        #     success = await navigator.go_to_page(PageState.NETSUITE_HOME_PAGE)
        #     if success:
        #         logger.info("Successfully navigated to NetSuite Home after login")
        
        # Navigate to time tracking page
        success = await navigator.go_to_page(PageState.TIME_TRACKING_PAGE)
        if success:
            logger.info("Successfully navigated to Time Tracking page")
            
            # Navigate to weekly sheet page
            success = await navigator.go_to_page(PageState.WEEKLY_SHEET_PAGE)
            if success:
                logger.info("Successfully navigated to Weekly Sheet page")
                
                # # Navigate back to NetSuite home
                # success = await navigator.go_to_page(PageState.NETSUITE_HOME_PAGE)
                # if success:
                #     logger.info("Successfully navigated back to NetSuite Home")
        else:
            logger.error("Navigation to Time Tracking failed")
        
        # Keep browser open for manual inspection (optional)
        if success:
            input("Press Enter to close the browser...")
        else:
            logger.info("Closing browser due to navigation failure.")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(example_usage())