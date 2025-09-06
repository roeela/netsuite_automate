import asyncio
from datetime import datetime
from automator import NetsuiteAutomator, DayType, StagingType


async def main():
    """Main function to run the automation"""
    
    # Use the automator as an async context manager
    async with NetsuiteAutomator() as automator:
        # Start and log in
        await automator.start()
        
        
        await automator.process_date(datetime(2025, 9, 8), 9.5, DayType.Work)
        # this is how to save
        # await automator.process_date(datetime(2025, 9, 8), 9.5, DayType.Work, StagingType.Save)
        # this is how to submit... be careful as this is irreversible
        # await automator.process_date(datetime(2025, 9, 8), 9.5, DayType.Work, StagingType.Submit)
        await automator.process_date(datetime(2025, 9, 10), 11.5, DayType.Sick)
        await automator.process_date(datetime(2025, 9, 11), 11.5, DayType.ReserveDuty)

        await automator.goto_weekly_view()
        # Pause for inspection
        await automator.pause_for_inspection("Press ENTER to close...")


# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
    