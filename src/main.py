import asyncio
from datetime import datetime
from automator import NetsuiteAutomator, DayType, StagingType


async def main():
    """Main function to run the automation"""
    
    # Use the automator as an async context manager
    async with NetsuiteAutomator() as automator:
        # Start and log in
        await automator.start()
        
        
        staging_type = StagingType.Test
        # await automator.process_date(datetime(2025, 10, 5), 9.0, DayType.Vacation, staging_type)
        await automator.process_date(datetime(2025, 10, 6), 4.5, DayType.PublicHoliday, staging_type)
        # await automator.process_date(datetime(2025, 10, 7), 4.5, DayType.PublicHoliday, staging_type)
        # await automator.process_date(datetime(2025, 10, 8), 9.0, DayType.Work, staging_type)
        # await automator.process_date(datetime(2025, 10, 9), 9.0, DayType.Work, staging_type)

        # await automator.goto_weekly_view()
        # Pause for inspection
        await automator.pause_for_inspection("Press ENTER to close...")



# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
    