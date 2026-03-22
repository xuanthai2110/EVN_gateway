import struct
import asyncio
import logging
from storage.database_manager import DatabaseManager
from storage.cache_manager import CacheManager
from drivers.huawei_driver import HuaweiDriver
from services.polling_service import PollingService
from modbus.modbus_server import ModbusServer
from pymodbus.client import AsyncModbusTcpClient

def decode_f32(registers):
    """Decodes two 16-bit registers to float32 (Big Endian)."""
    packed = struct.pack('>HH', *registers)
    return struct.unpack('>f', packed)[0]

logging.basicConfig(level=logging.INFO)

async def test_smoke():
    logging.info("Starting Smoke Test...")

    # 1. Setup Core
    db = DatabaseManager("/tmp/test_gateway.db")
    await db.initialize()
    cache = CacheManager()
    driver = HuaweiDriver("localhost")
    
    polling = PollingService(cache, db, driver)
    server = ModbusServer(cache, driver, port=5020) # Use 5020 for test
    
    await polling.start()
    await server.start()
    
    logging.info("Services started. Waiting for first poll...")
    for _ in range(10): # Wait up to 10s
        data = await cache.get_all()
        if data["status"] == "OK":
            break
        await asyncio.sleep(1)
    
    logging.info(f"Cache Data: {data}")
    if data["status"] != "OK":
        logging.error("Smoke Test Failed: Cache not updated")
        await polling.stop()
        await server.stop()
        return

    # 3. Verify Modbus Server
    async with AsyncModbusTcpClient("localhost", port=5020) as client:
        # Read P_out (Address 0, Length 2)
        rr = await client.read_input_registers(0, count=2, device_id=1)
        if rr.isError():
            logging.error(f"Modbus Read Failed: {rr}")
        else:
            p_out = decode_f32(rr.registers)
            logging.info(f"Modbus Read P_out: {p_out}")
    
    # 4. Stop
    await polling.stop()
    await server.stop()
    logging.info("Smoke Test Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(test_smoke())
