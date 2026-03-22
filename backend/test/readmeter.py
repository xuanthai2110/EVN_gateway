from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

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
    "unit_ids": [1],  # thêm [2,3,...] nếu có nhiều inverter
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
    rr = client.read_holding_registers(address - 1, length, unit=unit_id)
    if rr.isError():
        return None
    return rr.registers


def decode_value(registers, dtype):
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


# ================= READ SMARTLOGGER =================

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


# ================= READ INVERTER =================

def read_inverters(client):
    results = {}

    for unit_id in INVERTER_CONFIG["unit_ids"]:
        inv_data = {}

        for item in INVERTER_CONFIG["telemetry"]:
            regs = read_register(client, unit_id, item["address"], item["length"])

            # fallback
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


# ================= MAIN =================

if __name__ == "__main__":
    client = ModbusTcpClient("192.168.1.8", port=502)

    if client.connect():
        print("Connected!")

        smartlogger_data = read_smartlogger(client)
        inverter_data = read_inverters(client)

        print("\n=== SMARTLOGGER ===")
        print(smartlogger_data)

        print("\n=== INVERTER ===")
        print(inverter_data)

        client.close()
    else:
        print("Connection failed!")