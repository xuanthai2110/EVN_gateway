import asyncio
import struct
import logging
from pymodbus.client import AsyncModbusTcpClient
from .base_driver import BaseDriver

logger = logging.getLogger(__name__)

def decode_u16(registers, scale=1.0):
    return registers[0] * scale

def decode_s16(registers, scale=1.0):
    val = struct.unpack('>h', struct.pack('>H', registers[0]))[0]
    return val * scale

def decode_u32(registers, scale=1.0):
    packed = struct.pack('>HH', *registers)
    return struct.unpack('>I', packed)[0] * scale

def decode_s32(registers, scale=1.0):
    packed = struct.pack('>HH', *registers)
    return struct.unpack('>i', packed)[0] * scale

class HuaweiDriver(BaseDriver):
    def __init__(self, host, port=502):
        self.host = host
        self.port = port
        self.client = AsyncModbusTcpClient(host, port=port)

    async def connect(self):
        if await self.client.connect():
            logger.info(f"Connected to SmartLogger {self.host}:{self.port}")
            return True
        logger.error(f"Failed to connect to SmartLogger {self.host}")
        return False

    async def disconnect(self):
        self.client.close()

    async def read_logger_data(self, unit_id=0):
        """Read grid-level data from SmartLogger."""
        try:
            # 1. Active power (40525, 2 regs, sint32)
            # 2. Daily Energy (40562, 2 regs, uint32)
            # 3. Phasor data (40572, 6 regs)
            
            # Grid Power
            rr = await self.client.read_holding_registers(40525, count=2, device_id=unit_id)
            p_out = decode_s32(rr.registers, 0.001) if not rr.isError() else 0.0
            
            # Daily Energy
            rr = await self.client.read_holding_registers(40562, count=2, device_id=unit_id)
            e_dayly = decode_u32(rr.registers, 0.1) if not rr.isError() else 0.0
            
            # Phasor data (I_a, I_b, I_c, U_a, U_b, U_c)
            # Address 40572 onwards
            rr = await self.client.read_holding_registers(40572, count=6, device_id=unit_id)
            if not rr.isError():
                i_a, i_b, i_c = rr.registers[0], rr.registers[1], rr.registers[2]
                v_a, v_b, v_c = rr.registers[3]*0.1, rr.registers[4]*0.1, rr.registers[5]*0.1
            else:
                i_a = i_b = i_c = v_a = v_b = v_c = 0.0

            return {
                "P_out": p_out,
                "E_dayly": e_dayly,
                "I_a": i_a, "I_b": i_b, "I_c": i_c,
                "U_a": v_a, "U_b": v_b, "U_c": v_c,
                "Logger_connect": True
            }
        except Exception as e:
            logger.exception(f"Error reading SmartLogger data: {e}")
            return {"Logger_connect": False}

    async def read_inverter_data(self, unit_id):
        """Read per-inverter data."""
        try:
            # P_active (32080, 2 regs, sint32)
            # Daily Energy (32114, 2 regs, uint32)
            rr_p = await self.client.read_input_registers(32080, count=2, device_id=unit_id)
            rr_e = await self.client.read_input_registers(32114, count=2, device_id=unit_id)
            
            p = decode_s32(rr_p.registers, 0.001) if not rr_p.isError() else 0.0
            e = decode_u32(rr_e.registers, 0.01) if not rr_e.isError() else 0.0
            return [p, e]
        except Exception:
            return [0.0, 0.0]

    async def write_power_pct(self, value):
        """Write power limit command (Address 40013, 2 regs, sint32)"""
        if not self.client.connected:
            await self.connect()
            
        # Target pct * 0.1 for Huawei smartlogger
        raw_val = int(value * 10) # Adjust scale as per manual
        registers = struct.unpack('>HH', struct.pack('>i', raw_val))
        
        await self.client.write_registers(40013, registers, device_id=0)
        logger.info(f"Huawei Driver: Power Limit set to {value}%")
        return True

    async def read_data(self):
        # This will be replaced by multi-unit polling in PollingService, 
        # but kept base for compatibility
        return await self.read_logger_data()
