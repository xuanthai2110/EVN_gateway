import asyncio
import logging
from datetime import datetime

class UploadService:
    def __init__(self, cache_manager, db_manager, http_client, project_id):
        self.cache = cache_manager
        self.db = db_manager
        self.client = http_client
        self.project_id = project_id
        self.upload_interval = 300 # 5 minutes as per spec
        self.running = False

    async def start(self):
        self.running = True
        # Initial login
        await self.client.login()
        asyncio.create_task(self._upload_loop())

    async def stop(self):
        self.running = False
        await self.client.close()

    async def _upload_loop(self):
        while self.running:
            try:
                data = await self.cache.get_all()
                if data and data.get("status") == "OK":
                    success = await self.client.post_telemetry(self.project_id, data)
                    if success:
                        logging.info("Cloud: Telemetry uploaded successfully")
                    else:
                        logging.warning("Cloud: Upload failed, data is buffered in local DB")
                
                # Sleep until next interval
                await asyncio.sleep(self.upload_interval)
            except Exception as e:
                logging.error(f"Upload error: {e}")
                await asyncio.sleep(60) # Wait a bit on error
