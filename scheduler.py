#!/usr/bin/env python3
"""
Pinterest Affiliate Scheduler
Jalankan pipeline secara otomatis dengan interval tertentu.
"""

import schedule
import time
import logging
from pathlib import Path
from datetime import datetime
from main import Pipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_pipeline():
    """Jalankan satu siklus pipeline."""
    try:
        logger.info("=== Starting scheduled pipeline run ===")
        
        data_path = Path("data/shopee_products.json")
        pipeline = Pipeline(data_path)
        
        result = pipeline.run()
        
        if result.get("success"):
            logger.info(f"Pipeline SUCCESS | Board: {result.get('board_id')} | Product: {result.get('product')}")
        else:
            logger.error(f"Pipeline FAILED | Step: {result.get('step')} | Error: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Pipeline crashed: {str(e)}")
    
    logger.info("=== Pipeline run finished ===\n")


def main():
    # Jalankan setiap 2 jam (bisa diubah)
    schedule.every(2).hours.do(run_pipeline)
    
    # Jalankan sekali di awal
    logger.info("Scheduler started. First run will execute immediately.")
    run_pipeline()
    
    # Loop scheduler
    while True:
        schedule.run_pending()
        time.sleep(60)  # cek setiap 1 menit


if __name__ == "__main__":
    main()