from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

IP = "192.168.1.8"
PORT = 502


# ================= CONFIG =================

SMARTLOGGER_CONFIG = {
    "unit_id": 0,
    "grid": [
        {"name": "p_inv_total_kw", "address": 40525, "length": 2, "type": "sint32", "scale": 0.001},
        {"name": "q_inv_total_kvar", "address": 40544, "length": 2, "type": "sint32", "scale": 0.001},
        {"name": "v_a", "address": 40575, "length": 1, "type": "uint16", "scale": 0.1},
        {"name": "v_b", "address": 40576, "length": 1, "type": "uint16", "scale": 0.1},
        {"name": "v_c", "address": 40577, "length": 1, "type": "uint16", "scale": 0.1},
        {"name": "i_a", "address": 40572, "length": 1, "type": "uint16", "scale": 1},
        {"name": "i_b", "address": 40573, "length": 1, "type": "uint16", "scale": 1},
        {"name": "i_c", "address": 40574, "length": 1, "type": "uint16", "scale": 1},
        {"name": "pf", "address": 40532, "length": 1, "type": "sint16", "scale": 0.001},
    ],
    "energy": [
        {"name": "e_day_kwh", "address": 40562, "length": 2, "type": "uint32", "scale": 0.1},
        {"name": "e_total_kwh", "address": 40560, "length": 2, "type": "uint32", "scale": 0.1},
    ],
}

INVERTER_CONFIG = {
    "unit_ids": [1],
    "telemetry": [
        {"name": "status", "address": 32009, "length": 1, "type": "uint16", "scale": 1},
        {"name": "p_inv_out_kw", "address": 32080, "length": 2, "type": "sint32", "scale": 0.001},
        {
            "name": "freq",
            "address": 37118,
            "fallback_addresses": [32085],
            "length": 1,
            "type": "uint16",
            "scale": 0.01,
        },
        {"name": "q_inv_kvar", "address": 32106, "length": 2, "type": "sint32", "scale": 0.001},
        {"name": "e_day_kwh", "address": 32114, "length": 2, "type": "uint32", "scale": 0.01},
    ],
}


# ================= CORE =================

def read_register(client, unit_id, address, length):
    # fallback HOLDING
    rr = client.read_holding_registers(address - 1, length, slave=unit_id)
    if not rr.isError():
        return rr.registers

    return None


def decode_value(registers, dtype):
    """
    Decode với endian chuẩn Huawei/Sungrow
    """
    decoder = BinaryPayloadDecoder.fromRegisters(
        registers,
        byteorder=Endian.BIG,
        wordorder=Endian.LITTLE  # QUAN TRỌNG
    )

    if dtype == "uint16":
        return decoder.decode_16bit_uint()
    elif dtype == "sint16":
        return decoder.decode_16bit_int()
    elif dtype == "uint32":
        return decoder.decode_32bit_uint()
    elif dtype == "sint32":
        return decoder.decode_32bit_int()


# ================= SMARTLOGGER =================

def read_smartlogger(client):
    data = {}
    unit_id = SMARTLOGGER_CONFIG["unit_id"]

    for group in ["grid", "energy"]:
        for item in SMARTLOGGER_CONFIG[group]:
            regs = read_register(client, unit_id, item["address"], item["length"])

            if regs:
                value = decode_value(regs, item["type"])
                data[item["name"]] = round(value * item["scale"], 3)
            else:
                data[item["name"]] = None

    return data


# ================= INVERTER =================

def read_inverters(client):
    results = {}

    for unit_id in INVERTER_CONFIG["unit_ids"]:
        inv_data = {}

        for item in INVERTER_CONFIG["telemetry"]:
            regs = read_register(client, unit_id, item["address"], item["length"])

            # fallback address
            if not regs and "fallback_addresses" in item:
                for fb in item["fallback_addresses"]:
                    regs = read_register(client, unit_id, fb, item["length"])
                    if regs:
                        break

            if regs:
                value = decode_value(regs, item["type"])
                inv_data[item["name"]] = round(value * item["scale"], 3)
            else:
                inv_data[item["name"]] = None

        results[unit_id] = inv_data

    return results


# ================= DEBUG =================

def debug_raw(client):
    print("\n--- DEBUG RAW ---")

    # test smartlogger energy
    rr = client.read_input_registers(40562 - 1, 2, unit=0)
    print("SmartLogger e_day raw:", rr.registers if not rr.isError() else "ERROR")

    # test inverter power
    rr = client.read_input_registers(32080 - 1, 2, unit=1)
    print("Inverter P raw:", rr.registers if not rr.isError() else "ERROR")


# ================= MAIN =================

def main():
    client = ModbusTcpClient(IP, port=PORT)

    if not client.connect():
        print("❌ Connection failed")
        return

    print("✅ Connected")

    debug_raw(client)

    smart = read_smartlogger(client)
    inv = read_inverters(client)

    print("\n=== SMARTLOGGER ===")
    print(smart)

    print("\n=== INVERTER ===")
    print(inv)

    client.close()


if __name__ == "__main__":
    main()