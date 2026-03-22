import asyncio
import logging
import sys
from storage.database_manager import DatabaseManager
from storage.cache_manager import CacheManager
from drivers.huawei_driver import HuaweiDriver
from services.polling_service import PollingService
from services.upload_service import UploadService
from network.http_client import HTTPClient
from modbus.modbus_server import ModbusServer

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

async def run_services(polling, upload, modbus):
    # Start all services concurrently
    tasks = [
        asyncio.create_task(polling.start()),
        asyncio.create_task(upload.start()),
        asyncio.create_task(modbus.start())
    ]
    
    logging.info("✅ All services initiated. Monitoring...")
    
    # Wait until cancelled
    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    except asyncio.CancelledError:
        logging.info("Shutting down services...")
        for task in tasks:
            task.cancel()
        await polling.stop()
        await upload.stop()
        await modbus.stop()

async def main():
    logging.info("🚀 EVN Gateway starting...")

    # 1. Initialize Storage
    db_manager = DatabaseManager()
    await db_manager.initialize()
    cache_manager = CacheManager()

    # 2. Setup Device Driver
    # Real SmartLogger at 192.168.1.8
    driver = HuaweiDriver(host="192.168.1.8")
    
    # 3. Initialize Services
    polling_service = PollingService(cache_manager, db_manager, driver)
    polling_service.poll_interval = 5.0 # Increase interval for 9 devices
    
    http_client = HTTPClient(
        base_url="https://api.solarvision.tech", 
        username="gateway_001", 
        password="secure_password"
    )
    upload_service = UploadService(cache_manager, db_manager, http_client, project_id="PROJ_001")
    
    modbus_server = ModbusServer(cache_manager, driver)

    # 4. Start concurrent tasks
    try:
        await run_services(polling_service, upload_service, modbus_server)
    except Exception as e:
        logging.exception(f"Fatal error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
