from __future__ import annotations


import json
import sys
from pathlib import Path

from pymodbus.client import ModbusTcpClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from drivers.huawei_smartlogger import HuaweiSmartLoggerDriver


SMARTLOGGER_IP = "192.168.1.8"
PORT = 502
SMARTLOGGER_ID = 0
DEVICE_ADDR = 1


def get_all_register_data(smartlogger_ip: str, port: int, device_addr: int) -> dict:
    client = ModbusTcpClient(host=smartlogger_ip, port=port)
    if not client.connect():
        raise SystemExit(f"Cannot connect to SmartLogger at {smartlogger_ip}:{port}")

    try:
        driver = HuaweiSmartLoggerDriver(transport=client, slave_id=device_addr)
        smartlogger_data = driver.read_smartlogger()
        inverter_data = driver.read_inverter()
        return {
            "smartlogger_ip": smartlogger_ip,
            "smartlogger_unit_id": SMARTLOGGER_ID,
            "inverter_unit_ids": driver.inverter_unit_ids,
            "smartlogger": smartlogger_data,
            "inverter": inverter_data,
        }
    finally:
        client.close()


if __name__ == "__main__":
    result = get_all_register_data(SMARTLOGGER_IP, PORT, DEVICE_ADDR)
    print(json.dumps(result, indent=2, ensure_ascii=False))
