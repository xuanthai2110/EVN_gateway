import asyncio
import logging
from datetime import datetime

class PollingService:
    def __init__(self, cache_manager, db_manager, driver):
        self.cache = cache_manager
        self.db = db_manager
        self.driver = driver
        self.poll_interval = 2.0
        self.retry_count = 3
        self.retry_delay = [0.5, 1, 2]
        self.running = False

    async def start(self):
        self.running = True
        await self.driver.connect()
        asyncio.create_task(self._poll_loop())

    async def stop(self):
        self.running = False
        await self.driver.disconnect()

    async def _poll_loop(self):
        while self.running:
            try:
                devices = await self.db.get_devices()
                logger_data = {}
                invs_data = []
                total_p_inv = 0.0
                
                # 1. Read SmartLogger (Unit ID '0')
                for dev in devices:
                    if dev["type"] == "LOGGER":
                        uid = int(dev["device_id"])
                        logger_data = await self._read_with_retry(self.driver.read_logger_data, uid)
                        break
                
                # 2. Read Inverters
                for dev in devices:
                    if dev["type"] == "INVERTER":
                        uid = int(dev["device_id"])
                        inv_vals = await self._read_with_retry(self.driver.read_inverter_data, uid)
                        if inv_vals:
                            invs_data.append(inv_vals)
                            total_p_inv += inv_vals[0]
                
                if logger_data:
                    data = logger_data
                    data["Invs_Data"] = invs_data
                    data["P_inv_out"] = total_p_inv
                    data["created_at"] = datetime.now().isoformat()
                    data["project_id"] = "PROJ_001" 
                    
                    await self.cache.update(data)
                    await self.db.save_telemetry(data)
                    logging.info(f"Polling: Total P_inv={total_p_inv:.2f} kW, P_grid={data.get('P_out',0):.2f} kW")
                    
            except Exception as e:
                logging.error(f"Polling error: {e}")
                await self.cache.mark_error()
            
            await asyncio.sleep(self.poll_interval)

    async def _read_with_retry(self, func, *args):
        for i in range(self.retry_count):
            try:
                return await asyncio.wait_for(func(*args), timeout=3.0)
            except Exception as e:
                logging.warning(f"Read attempt {i+1} failed for {func.__name__}: {e}")
                if i < self.retry_count - 1:
                    await asyncio.sleep(self.retry_delay[i])
        return None
