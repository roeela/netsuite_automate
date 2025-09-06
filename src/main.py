import asyncio
from datetime import datetime
from automator import NetsuiteAutomator, DayType


async def main():
    """Main function to run the automation"""
    
    # Use the automator as an async context manager
    async with NetsuiteAutomator() as automator:
        # Start and log in
        await automator.start()
        
        await automator.process_date(datetime(2025, 9, 3), 9.5, DayType.Work)
        await automator.process_date(datetime(2025, 9, 3), 11.5, DayType.Sick)
        await automator.process_date(datetime(2025, 9, 4), 11.5, DayType.ReserveDuty)
        # Pause for inspection
        await automator.pause_for_inspection("Press ENTER to close...")


# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
    