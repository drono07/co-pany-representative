"""
Cron job scheduler for automated website analysis
"""

import asyncio
import logging
from datetime import datetime
from analysis_engine import SchedulerEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CronScheduler:
    """Cron scheduler for automated analysis runs"""
    
    def __init__(self):
        self.scheduler_engine = SchedulerEngine()
        self.running = False
    
    async def start(self):
        """Start the cron scheduler"""
        logger.info("Starting cron scheduler...")
        self.running = True
        
        try:
            # Initialize the scheduler engine
            await self.scheduler_engine.initialize()
            
            # Start the scheduler loop
            await self.scheduler_engine.run_scheduler_loop()
            
        except Exception as e:
            logger.error(f"Error starting cron scheduler: {e}")
            raise
    
    async def stop(self):
        """Stop the cron scheduler"""
        logger.info("Stopping cron scheduler...")
        self.running = False

async def main():
    """Main function to run the cron scheduler"""
    scheduler = CronScheduler()
    
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, stopping scheduler...")
        await scheduler.stop()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await scheduler.stop()

if __name__ == "__main__":
    asyncio.run(main())
