import time
import logging
from typing import Dict, Any, List

from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

logger = logging.getLogger(__name__)


# ================= BASE DRIVER =================

class HuaweiModbusDriver:
    def __init__(self, host: str, port: int = 502, timeout: int = 3):
        self.host = host
        self.port = port
        self.client = ModbusTcpClient(host, port=port, timeout=timeout)

    def connect(self) -> bool:
        if self.client.connect():
            logger.info(f"Connected to {self.host}")
            return True
        logger.error(f"Failed to connect {self.host}")
        return False

    def close(self):
        self.client.close()

    def read_registers(self, unit_id: int, address: int, length: int):
        try:
            rr = self.client.read_holding_registers(address, length, slave=unit_id)
            if rr.isError():
                logger.warning(f"Read fail u={unit_id} addr={address}")
                return None
            return rr.registers
        except Exception as e:
            logger.error(f"Exception read: {e}")
            return None

    @staticmethod
    def decode(registers: List[int], dtype: str):
        decoder = BinaryPayloadDecoder.fromRegisters(
            registers,
            byteorder=Endian.BIG,
            wordorder=Endian.BIG
        )

        if dtype == "uint16":
            return decoder.decode_16bit_uint()
        elif dtype == "sint16":
            return decoder.decode_16bit_int()
        elif dtype == "uint32":
            return decoder.decode_32bit_uint()
        elif dtype == "sint32":
            return decoder.decode_32bit_int()
        else:
            return None


# ================= SMARTLOGGER =================

class SmartLogger:
    def __init__(self, driver: HuaweiModbusDriver, unit_id: int = 0):
        self.driver = driver
        self.unit_id = unit_id

        self.map = [
            # grid
            ("p_inv_total_kw", 40525, 2, "sint32", 0.001),
            ("q_inv_total_kvar", 40544, 2, "sint32", 0.001),
            ("v_a", 40575, 1, "uint16", 0.1),
            ("v_b", 40576, 1, "uint16", 0.1),
            ("v_c", 40577, 1, "uint16", 0.1),
            ("i_a", 40572, 1, "uint16", 1),
            ("i_b", 40573, 1, "uint16", 1),
            ("i_c", 40574, 1, "uint16", 1),
            ("pf", 40532, 1, "sint16", 0.001),

            # energy (FIX SCALE)
            ("e_day_kwh", 40562, 2, "uint32", 0.001),
            ("e_total_kwh", 40560, 2, "uint32", 0.001),
        ]

    def read(self) -> Dict[str, Any]:
        data = {}

        for name, addr, length, dtype, scale in self.map:
            regs = self.driver.read_registers(self.unit_id, addr, length)

            if regs:
                try:
                    value = self.driver.decode(regs, dtype)
                    data[name] = round(value * scale, 3)
                except Exception as e:
                    logger.error(f"Decode error {name}: {e}")
                    data[name] = None
            else:
                data[name] = None

        return data


# ================= INVERTER =================

class Inverter:
    def __init__(self, driver: HuaweiModbusDriver, unit_ids: List[int]):
        self.driver = driver
        self.unit_ids = unit_ids

        self.map = [
            ("status", 32009, 1, "uint16", 1),
            ("p_inv_out_kw", 32080, 2, "sint32", 0.001),
            ("freq", 32085, 1, "uint16", 0.01),
            ("q_inv_kvar", 32082, 2, "sint32", 0.001),
            ("e_day_kwh", 32114, 2, "uint32", 0.001),
        ]

    def read(self) -> Dict[int, Dict[str, Any]]:
        results = {}

        for uid in self.unit_ids:
            inv_data = {}

            for name, addr, length, dtype, scale in self.map:
                regs = self.driver.read_registers(uid, addr, length)

                if regs:
                    try:
                        value = self.driver.decode(regs, dtype)
                        inv_data[name] = round(value * scale, 3)
                    except Exception as e:
                        logger.error(f"Decode error inv{uid}-{name}: {e}")
                        inv_data[name] = None
                else:
                    inv_data[name] = None

            results[uid] = inv_data

        return results


# ================= MAIN TEST =================

