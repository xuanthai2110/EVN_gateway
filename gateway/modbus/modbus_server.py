import struct
import asyncio
import logging
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusDeviceContext, ModbusServerContext
from pymodbus.datastore import ModbusSparseDataBlock

def encode_f32(value):
    """Encodes float32 to two 16-bit registers (Big Endian)."""
    packed = struct.pack('>f', value)
    return struct.unpack('>HH', packed)

def decode_f32(registers):
    """Decodes two 16-bit registers to float32 (Big Endian)."""
    packed = struct.pack('>HH', *registers)
    return struct.unpack('>f', packed)[0]

class EVNDataBlock(ModbusSparseDataBlock):
    def __init__(self, cache_manager, driver):
        # We don't need to initialize values since we override get/set
        super().__init__({0: 0}) 
        self.cache = cache_manager
        self.driver = driver

    def validate(self, func_code, address, count=1):
        """Validates if the requested address range is allowed."""
        # Allow all addresses for now, or restrict to EVN ranges
        # EVN uses 3xxxx (Read-only) and 4xxxx (Read-write)
        # modbus_address = evn_address - base
        return True

    def getValues(self, address, count=1):
        """Called for FC03, FC04 (Reading)"""
        # Pymodbus 3.x ModbusDeviceContext adds 1 to the address by default.
        # We subtract it back to restore our 0-based mapping.
        actual_address = address - 1
        
        # Since this is sync but we need async cache access, 
        # we can use a trick: cache_manager stores last data in a sync-friendly way 
        # or we use the last known data.
        # However, for 'vibe coding', we can use asyncio.run_coroutine_threadsafe or similar
        # but better yet, let's just make the cache access sync-accessible.
        
        # For simplicity in this demo, we'll try to use the async_getValues if called from async context,
        # but for sync calls, we'll return the last cached value.
        data = self.cache._cache # Access internal cache directly for sync read
        
        if actual_address == 0: # 30001
            return encode_f32(data.get("P_out", 0.0))
        elif actual_address == 2: # 30003
            return encode_f32(data.get("P_inv_out", 0.0))
        elif actual_address == 4: # 30005
            return encode_f32(data.get("E_dayly", 0.0))
        return [0] * count

    def setValues(self, address, values):
        """Called for FC05, FC06, FC16 (Writing)"""
        actual_address = address - 1
        
        if actual_address == 12: # Set_P_pct (float32, 2 registers)
            val = decode_f32(values)
            # Forward to driver (async task)
            asyncio.create_task(self.driver.write_power_pct(val))
            # Sync update of cache
            self.cache._cache["Set_P_pct"] = val
            
        return super().setValues(address, values)

    async def async_getValues(self, address, count=1):
        # Redirect to corrected sync version
        return self.getValues(address, count)

    async def async_setValues(self, address, values):
        # Redirect to corrected sync version
        return self.setValues(address, values)

class ModbusServer:
    def __init__(self, cache_manager, driver, host="192.168.1.8", port=5020):
        self.cache = cache_manager
        self.driver = driver
        self.host = host
        self.port = port
        self.server_task = None

    async def start(self):
        # Setup DataStore
        # Note: In pymodbus 3.x, ModbusSparseDataBlock can be async if we override properly
        # But usually we use a standard datastore and update it from a separate task.
        # However, for 'vibe coding' a dynamic datablock is more elegant.
        # For simplicity in this demo, we'll use a task that updates the datastore every 1s.
        
        self.block = EVNDataBlock(self.cache, self.driver)
        # di: Discrete Inputs, co: Coils, hr: Holding Registers, ir: Input Registers
        store = ModbusDeviceContext(
            di=self.block,
            co=self.block,
            hr=self.block,
            ir=self.block
        )
        context = ModbusServerContext(devices=store, single=True)
        
        logging.info(f"Starting Modbus Server on {self.host}:{self.port}")
        self.server_task = asyncio.create_task(
            StartAsyncTcpServer(
                context=context, 
                address=(self.host, self.port)
            )
        )

    async def stop(self):
        if self.server_task:
            self.server_task.cancel()
